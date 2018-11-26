import asyncio
from collections import (
    namedtuple,
)
import os
import subprocess

import pytest

from p2pclient.p2pclient import (
    Client,
)


def start_p2pd(control_path):
    try:
        os.unlink(control_path)
    except FileNotFoundError:
        pass
    return subprocess.Popen(
        "p2pd -sock={} -dht 2>&1 1>/tmp/p2pd_{}.log".format(
            control_path,
            control_path[5:],
        ),
        shell=True,
    )


P2PDInfo = namedtuple('P2PDInfo', ['proc', 'control_path', 'listen_path'])


@pytest.yield_fixture(scope="function")
def make_p2pd():
    p2pd_procs = {}

    def _make_p2pd(number):
        if number in p2pd_procs:
            p2pd_info = p2pd_procs[number]
            return p2pd_info.control_path, p2pd_info.listen_path
        control_path = f"/tmp/test_p2pd_control_{number}"
        listen_path = f"/tmp/test_p2pd_listen_path_{number}"
        try:
            os.unlink(listen_path)
        except FileNotFoundError:
            pass
        proc = start_p2pd(control_path)
        p2pd_procs[number] = P2PDInfo(proc, control_path, listen_path)
        return control_path, listen_path

    yield _make_p2pd

    # teardown
    for _, p2pd_info in p2pd_procs.items():
        p2pd_info.proc.terminate()


@pytest.mark.asyncio
async def test_client_integration(make_p2pd):
    control_path_0, listen_path_0 = make_p2pd(0)
    control_path_1, listen_path_1 = make_p2pd(1)

    await asyncio.sleep(2)

    c0 = Client(control_path_0, listen_path_0)
    await c0.listen()

    peer_id_0, maddrs_0 = await c0.identify()

    c1 = Client(control_path_1, listen_path_1)
    await c1.listen()
    peer_id_1, maddrs_1 = await c1.identify()

    await c0.connect(peer_id_1, maddrs_1)

    bytes_to_send = b"yoyoyoyoyog"

    async def handle_proto(stream_info, reader, writer):
        bytes_received = await reader.read(len(bytes_to_send))
        assert bytes_received == bytes_to_send

    await c1.stream_handler("123", handle_proto)

    stream_info, reader, writer = await c0.stream_open(
        peer_id_1,
        [
            "123",
        ],
    )
    writer.write(bytes_to_send)
    await writer.drain()  # TODO: confirm this behaviour
    writer.close()
    await asyncio.sleep(0.2)  # yield

    # test dht.find_peer
    pinfo = await c0.find_peer(peer_id_1)
    print(pinfo)


def test_abc(make_p2pd):
    control_path_1, listen_path_1 = make_p2pd(0)
    pass
