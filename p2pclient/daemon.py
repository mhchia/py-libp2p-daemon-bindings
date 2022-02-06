"""
The classes in this file allow to launch the JS or Go daemon as a subprocess. This provides a simple system
for application maintainers to write tests using one or more instances of the P2P daemon.
"""

# Used for the annotation of Popen, which is not generic before Python 3.9
from __future__ import annotations

import abc
import os
import subprocess
import time
import uuid
from typing import AsyncIterator, Awaitable, Callable, List, NamedTuple, Tuple

import anyio
from async_generator import asynccontextmanager
from multiaddr import Multiaddr, protocols

from p2pclient.p2pclient import Client
from p2pclient.utils import get_unused_tcp_port
from typing import BinaryIO, Optional

TIMEOUT_DURATION = 30  # seconds


async def try_until_success(
    coro_func: Callable[[], Awaitable[bool]], timeout: int = TIMEOUT_DURATION
) -> None:
    """
    Keep running ``coro_func`` until the time is out.
    All arguments of ``coro_func`` should be filled, i.e. it should be called without arguments.
    """
    t_start = time.monotonic()
    while True:
        result = await coro_func()
        if result:
            break
        if (time.monotonic() - t_start) >= timeout:
            # timeout
            assert False, f"{coro_func} still failed after `{timeout}` seconds"
        await anyio.sleep(0.01)


class Daemon(abc.ABC):
    LINES_HEAD_PATTERN: Tuple[bytes, ...]
    control_maddr: Multiaddr
    proc_daemon: subprocess.Popen[bytes]
    log_filename: str = ""
    f_log: Optional[BinaryIO] = None
    is_closed: bool

    def __init__(
        self,
        daemon_executable: str,
        control_maddr: Multiaddr,
        enable_control: bool,
        enable_connmgr: bool,
        enable_dht: bool,
        enable_pubsub: bool,
    ):
        self.daemon_executable = daemon_executable
        self.control_maddr = control_maddr
        self.enable_control = enable_control
        self.enable_connmgr = enable_connmgr
        self.enable_dht = enable_dht
        self.enable_pubsub = enable_pubsub
        self.is_closed = False
        self._start_logging()
        self._run(daemon_executable)

    def _start_logging(self) -> None:
        name_control_maddr = str(self.control_maddr).replace("/", "_").replace(".", "_")
        self.log_filename = f"/tmp/log_p2pd{name_control_maddr}.txt"
        self.f_log = open(self.log_filename, "wb")

    @abc.abstractmethod
    def _make_command_line_options(self) -> List[str]:
        ...

    @abc.abstractmethod
    def _terminate(self) -> None:
        ...

    def _run(self, daemon_executable: str) -> None:
        cmd_list = [daemon_executable] + self._make_command_line_options()
        self.proc_daemon = subprocess.Popen(
            cmd_list, stdout=self.f_log, stderr=self.f_log, bufsize=0
        )

    async def wait_until_ready(self) -> None:
        lines_head_occurred = {line: False for line in self.LINES_HEAD_PATTERN}

        with open(self.log_filename, "rb") as f_log_read:

            async def read_from_daemon_and_check() -> bool:
                line = f_log_read.readline()
                for head_pattern in lines_head_occurred:
                    if line.startswith(head_pattern):
                        lines_head_occurred[head_pattern] = True
                return all([value for _, value in lines_head_occurred.items()])

            await try_until_success(read_from_daemon_and_check)

        # sleep for a while in case that the daemon haven't been ready after emitting these lines
        await anyio.sleep(0.1)

    def close(self) -> None:
        if self.is_closed:
            return
        self._terminate()
        self.proc_daemon.wait()
        self.f_log.close()
        self.is_closed = True


class GoDaemon(Daemon):

    LINES_HEAD_PATTERN = (b"Control socket:", b"Peer ID:", b"Peer Addrs:")

    def _make_command_line_options(self) -> List[str]:
        cmd_list = [f"-listen={str(self.control_maddr)}"]
        if self.enable_connmgr:
            cmd_list += ["-connManager=true", "-connLo=1", "-connHi=2", "-connGrace=0"]
        if self.enable_dht:
            cmd_list += ["-dht=true"]
        if self.enable_pubsub:
            cmd_list += ["-pubsub=true", "-pubsubRouter=gossipsub"]

        return cmd_list

    def _terminate(self) -> None:
        self.proc_daemon.terminate()


class JsDaemon(Daemon):

    LINES_HEAD_PATTERN = (b"daemon has started",)

    def _make_command_line_options(self) -> List[str]:
        cmd_list = [f"--listen={str(self.control_maddr)}"]
        if self.enable_connmgr:
            cmd_list += [
                "--connManager=true",
                "--connLo=1",
                "--connHi=2",
                "--connGrace=0",
            ]
        if self.enable_dht:
            cmd_list += ["--dht=true"]
        if self.enable_pubsub:
            cmd_list += ["--pubsub=true", "--pubsubRouter=gossipsub"]

        return cmd_list

    # TODO: investigate why the JS daemon needs to be killed instead of terminating gracefully. Some tests
    #       (ex: test_client_stream_open_failure) freeze after completion if we use terminate.
    def _terminate(self) -> None:
        self.proc_daemon.kill()


class DaemonTuple(NamedTuple):
    daemon: Daemon
    client: Client


@asynccontextmanager
async def make_p2pd_pair_unix(
    daemon_executable: str,
    enable_control: bool,
    enable_connmgr: bool,
    enable_dht: bool,
    enable_pubsub: bool,
) -> AsyncIterator[DaemonTuple]:
    name = str(uuid.uuid4())[:8]
    control_maddr = Multiaddr(f"/unix/tmp/test_p2pd_control_{name}.sock")
    listen_maddr = Multiaddr(f"/unix/tmp/test_p2pd_listen_{name}.sock")
    # Remove the existing unix socket files if they are existing
    try:
        os.unlink(control_maddr.value_for_protocol(protocols.P_UNIX))
    except FileNotFoundError:
        pass
    try:
        os.unlink(listen_maddr.value_for_protocol(protocols.P_UNIX))
    except FileNotFoundError:
        pass
    async with make_p2pd_pair(
        daemon_executable=daemon_executable,
        control_maddr=control_maddr,
        listen_maddr=listen_maddr,
        enable_control=enable_control,
        enable_connmgr=enable_connmgr,
        enable_dht=enable_dht,
        enable_pubsub=enable_pubsub,
    ) as pair:
        yield pair


@asynccontextmanager
async def make_p2pd_pair_ip4(
    daemon_executable: str,
    enable_control: bool,
    enable_connmgr: bool,
    enable_dht: bool,
    enable_pubsub: bool,
) -> AsyncIterator[DaemonTuple]:
    control_maddr = Multiaddr(f"/ip4/127.0.0.1/tcp/{get_unused_tcp_port()}")
    listen_maddr = Multiaddr(f"/ip4/127.0.0.1/tcp/{get_unused_tcp_port()}")
    async with make_p2pd_pair(
        daemon_executable=daemon_executable,
        control_maddr=control_maddr,
        listen_maddr=listen_maddr,
        enable_control=enable_control,
        enable_connmgr=enable_connmgr,
        enable_dht=enable_dht,
        enable_pubsub=enable_pubsub,
    ) as pair:
        yield pair


@asynccontextmanager
async def make_p2pd_pair(
    daemon_executable: str,
    control_maddr: Multiaddr,
    listen_maddr: Multiaddr,
    enable_control: bool,
    enable_connmgr: bool,
    enable_dht: bool,
    enable_pubsub: bool,
) -> AsyncIterator[DaemonTuple]:
    daemon_cls = GoDaemon if daemon_executable == "p2pd" else JsDaemon
    p2pd = daemon_cls(
        daemon_executable=daemon_executable,
        control_maddr=control_maddr,
        enable_control=enable_control,
        enable_connmgr=enable_connmgr,
        enable_dht=enable_dht,
        enable_pubsub=enable_pubsub,
    )
    # wait for daemon ready
    await p2pd.wait_until_ready()
    client = Client(control_maddr=control_maddr, listen_maddr=listen_maddr)
    try:
        async with client.listen():
            yield DaemonTuple(daemon=p2pd, client=client)
    finally:
        if not p2pd.is_closed:
            p2pd.close()
