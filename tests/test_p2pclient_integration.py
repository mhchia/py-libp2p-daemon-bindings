import functools
import os
import subprocess
import time
from typing import NamedTuple
import uuid

import anyio
from async_exit_stack import AsyncExitStack
from async_generator import asynccontextmanager
from p2pclient.libp2p_stubs.peer.id import ID
from multiaddr import Multiaddr, protocols
import multihash
import pytest

from p2pclient.exceptions import ControlFailure
from p2pclient.p2pclient import Client
import p2pclient.pb.p2pd_pb2 as p2pd_pb
from p2pclient.utils import get_unused_tcp_port, read_pbmsg_safe

TIMEOUT_DURATION = 30  # seconds


@pytest.fixture
def num_p2pds():
    return 4


@pytest.fixture(scope="module")
def peer_id_random():
    return ID.from_base58("QmcgpsyWgH8Y8ajJz1Cu72KnS5uo2Aa2LpzU7kinSupNK1")


@pytest.fixture
def enable_control():
    return True


@pytest.fixture
def enable_connmgr():
    return False


@pytest.fixture
def enable_dht():
    return False


@pytest.fixture
def enable_pubsub():
    return False


@pytest.fixture
def func_make_p2pd_pair():
    return make_p2pd_pair_ip4


async def try_until_success(coro_func, timeout=TIMEOUT_DURATION):
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


class Daemon:
    control_maddr = None
    proc_daemon = None
    log_filename = ""
    f_log = None
    closed = None

    def __init__(
        self, control_maddr, enable_control, enable_connmgr, enable_dht, enable_pubsub
    ):
        self.control_maddr = control_maddr
        self.enable_control = enable_control
        self.enable_connmgr = enable_connmgr
        self.enable_dht = enable_dht
        self.enable_pubsub = enable_pubsub
        self.is_closed = False
        self._start_logging()
        self._run()

    def _start_logging(self):
        name_control_maddr = str(self.control_maddr).replace("/", "_").replace(".", "_")
        self.log_filename = f"/tmp/log_p2pd{name_control_maddr}.txt"
        self.f_log = open(self.log_filename, "wb")

    def _run(self):
        cmd_list = ["p2pd", f"--listen={str(self.control_maddr)}"]
        if self.enable_connmgr:
            cmd_list += ["--connManager=true", "--connLo=1", "--connHi=2", "--connGrace=0"]
        if self.enable_dht:
            cmd_list += ["--dht=true"]
        if self.enable_pubsub:
            cmd_list += ["--pubsub=true", "--pubsubRouter=gossipsub"]
        self.proc_daemon = subprocess.Popen(
            cmd_list, stdout=self.f_log, stderr=self.f_log, bufsize=0
        )

    async def wait_until_ready(self):
        # lines_head_pattern = (b"Control socket:", b"Peer ID:", b"Peer Addrs:", b"daemon has started")
        lines_head_pattern = (b"daemon has started",)
        lines_head_occurred = {line: False for line in lines_head_pattern}

        with open(self.log_filename, "rb") as f_log_read:

            async def read_from_daemon_and_check():
                line = f_log_read.readline()
                for head_pattern in lines_head_occurred:
                    if line.startswith(head_pattern):
                        lines_head_occurred[head_pattern] = True
                return all([value for _, value in lines_head_occurred.items()])

            await try_until_success(read_from_daemon_and_check)

        # sleep for a while in case that the daemon haven't been ready after emitting these lines
        await anyio.sleep(0.1)

    def close(self):
        if self.is_closed:
            return
        self.proc_daemon.terminate()
        self.proc_daemon.wait()
        self.f_log.close()
        self.is_closed = True


class DaemonTuple(NamedTuple):
    daemon: Daemon
    client: Client


class ConnectionFailure(Exception):
    pass


@asynccontextmanager
async def make_p2pd_pair_unix(
    enable_control, enable_connmgr, enable_dht, enable_pubsub
):
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
    async with _make_p2pd_pair(
        control_maddr=control_maddr,
        listen_maddr=listen_maddr,
        enable_control=enable_control,
        enable_connmgr=enable_connmgr,
        enable_dht=enable_dht,
        enable_pubsub=enable_pubsub,
    ) as pair:
        yield pair


@asynccontextmanager
async def make_p2pd_pair_ip4(enable_control, enable_connmgr, enable_dht, enable_pubsub):
    control_maddr = Multiaddr(f"/ip4/127.0.0.1/tcp/{get_unused_tcp_port()}")
    listen_maddr = Multiaddr(f"/ip4/127.0.0.1/tcp/{get_unused_tcp_port()}")
    async with _make_p2pd_pair(
        control_maddr=control_maddr,
        listen_maddr=listen_maddr,
        enable_control=enable_control,
        enable_connmgr=enable_connmgr,
        enable_dht=enable_dht,
        enable_pubsub=enable_pubsub,
    ) as pair:
        yield pair


@asynccontextmanager
async def _make_p2pd_pair(
    control_maddr,
    listen_maddr,
    enable_control,
    enable_connmgr,
    enable_dht,
    enable_pubsub,
):
    p2pd = Daemon(
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


@pytest.fixture
async def p2pcs(
    num_p2pds,
    enable_control,
    enable_connmgr,
    enable_dht,
    enable_pubsub,
    func_make_p2pd_pair,
):
    # TODO: Change back to gather style
    async with AsyncExitStack() as stack:
        p2pd_tuples = [
            await stack.enter_async_context(
                func_make_p2pd_pair(
                    enable_control=enable_control,
                    enable_connmgr=enable_connmgr,
                    enable_dht=enable_dht,
                    enable_pubsub=enable_pubsub,
                )
            )
            for _ in range(num_p2pds)
        ]
        yield tuple(p2pd_tuple.client for p2pd_tuple in p2pd_tuples)


@pytest.mark.parametrize(
    "enable_control, func_make_p2pd_pair", ((True, make_p2pd_pair_unix),)
)
@pytest.mark.anyio
async def test_client_identify_unix_socket(p2pcs):
    await p2pcs[0].identify()


@pytest.mark.parametrize("enable_control", (True,))
@pytest.mark.anyio
async def test_client_identify(p2pcs, anyio_backend):
    await p2pcs[0].identify()


@pytest.mark.parametrize("enable_control", (True,))
@pytest.mark.anyio
async def test_client_connect_success(p2pcs):
    peer_id_0, maddrs_0 = await p2pcs[0].identify()
    peer_id_1, maddrs_1 = await p2pcs[1].identify()
    await p2pcs[0].connect(peer_id_1, maddrs_1)
    # test case: repeated connections
    await p2pcs[1].connect(peer_id_0, maddrs_0)


@pytest.mark.parametrize("enable_control", (True,))
@pytest.mark.anyio
async def test_client_connect_failure(peer_id_random, p2pcs):
    peer_id_1, maddrs_1 = await p2pcs[1].identify()
    await p2pcs[0].identify()
    # test case: `peer_id` mismatches
    with pytest.raises(ControlFailure):
        await p2pcs[0].connect(peer_id_random, maddrs_1)
    # test case: empty maddrs
    with pytest.raises(ControlFailure):
        await p2pcs[0].connect(peer_id_1, [])
    # test case: wrong maddrs
    with pytest.raises(ControlFailure):
        await p2pcs[0].connect(peer_id_1, [Multiaddr("/ip4/127.0.0.1/udp/0")])


async def _check_connection(p2pd_tuple_0, p2pd_tuple_1):
    peer_id_0, _ = await p2pd_tuple_0.identify()
    peer_id_1, _ = await p2pd_tuple_1.identify()
    peers_0 = [pinfo.peer_id for pinfo in await p2pd_tuple_0.list_peers()]
    peers_1 = [pinfo.peer_id for pinfo in await p2pd_tuple_1.list_peers()]
    return (peer_id_0 in peers_1) and (peer_id_1 in peers_0)


async def connect_safe(p2pd_tuple_0, p2pd_tuple_1):
    peer_id_1, maddrs_1 = await p2pd_tuple_1.identify()
    await p2pd_tuple_0.connect(peer_id_1, maddrs_1)
    await try_until_success(
        functools.partial(
            _check_connection, p2pd_tuple_0=p2pd_tuple_0, p2pd_tuple_1=p2pd_tuple_1
        )
    )


@pytest.mark.parametrize("enable_control", (True,))
@pytest.mark.anyio
async def test_connect_safe(p2pcs):
    await connect_safe(p2pcs[0], p2pcs[1])


@pytest.mark.parametrize("enable_control", (True,))
@pytest.mark.anyio
async def test_client_list_peers(p2pcs):
    # test case: no peers
    assert len(await p2pcs[0].list_peers()) == 0
    # test case: 1 peer
    await connect_safe(p2pcs[0], p2pcs[1])
    assert len(await p2pcs[0].list_peers()) == 1
    assert len(await p2pcs[1].list_peers()) == 1
    # test case: one more peer
    await connect_safe(p2pcs[0], p2pcs[2])
    assert len(await p2pcs[0].list_peers()) == 2
    assert len(await p2pcs[1].list_peers()) == 1
    assert len(await p2pcs[2].list_peers()) == 1


@pytest.mark.parametrize("enable_control", (True,))
@pytest.mark.anyio
async def test_client_disconnect(peer_id_random, p2pcs):
    # test case: disconnect a peer without connections
    await p2pcs[1].disconnect(peer_id_random)
    # test case: disconnect
    peer_id_0, _ = await p2pcs[0].identify()
    await connect_safe(p2pcs[0], p2pcs[1])
    assert len(await p2pcs[0].list_peers()) == 1
    assert len(await p2pcs[1].list_peers()) == 1
    await p2pcs[1].disconnect(peer_id_0)
    assert len(await p2pcs[0].list_peers()) == 0
    assert len(await p2pcs[1].list_peers()) == 0
    # test case: disconnect twice
    await p2pcs[1].disconnect(peer_id_0)
    assert len(await p2pcs[0].list_peers()) == 0
    assert len(await p2pcs[1].list_peers()) == 0


@pytest.mark.parametrize("enable_control", (True,))
@pytest.mark.anyio
async def test_client_stream_open_success(p2pcs):
    peer_id_1, maddrs_1 = await p2pcs[1].identify()
    await connect_safe(p2pcs[0], p2pcs[1])

    proto = "123"

    async def handle_proto(stream_info, stream):
        with pytest.raises(anyio.exceptions.IncompleteRead):
            await stream.receive_exactly(1)

    await p2pcs[1].stream_handler(proto, handle_proto)

    # test case: normal
    stream_info, stream = await p2pcs[0].stream_open(peer_id_1, (proto,))
    assert stream_info.peer_id == peer_id_1
    assert stream_info.addr in maddrs_1
    assert stream_info.proto == "123"
    await stream.close()

    # test case: open with multiple protocols
    stream_info, stream = await p2pcs[0].stream_open(
        peer_id_1, (proto, "another_protocol")
    )
    assert stream_info.peer_id == peer_id_1
    assert stream_info.addr in maddrs_1
    assert stream_info.proto == "123"
    await stream.close()


@pytest.mark.parametrize("enable_control", (True,))
@pytest.mark.anyio
async def test_client_stream_open_failure(p2pcs):
    peer_id_1, _ = await p2pcs[1].identify()
    await connect_safe(p2pcs[0], p2pcs[1])

    proto = "123"

    # test case: `stream_open` to a peer who didn't register the protocol
    with pytest.raises(ControlFailure):
        await p2pcs[0].stream_open(peer_id_1, (proto,))

    # test case: `stream_open` to a peer for a non-registered protocol
    async def handle_proto(stream_info, stream):
        pass

    await p2pcs[1].stream_handler(proto, handle_proto)
    with pytest.raises(ControlFailure):
        await p2pcs[0].stream_open(peer_id_1, ("another_protocol",))


@pytest.mark.parametrize("enable_control", (True,))
@pytest.mark.anyio
async def test_client_stream_handler_success(p2pcs):
    peer_id_1, _ = await p2pcs[1].identify()
    await connect_safe(p2pcs[0], p2pcs[1])

    proto = "protocol123"
    bytes_to_send = b"yoyoyoyoyog"
    # event for this test function to wait until the handler function receiving the incoming data
    event_handler_finished = anyio.create_event()

    async def handle_proto(stream_info, stream):
        nonlocal event_handler_finished
        bytes_received = await stream.receive_exactly(len(bytes_to_send))
        assert bytes_received == bytes_to_send
        await event_handler_finished.set()

    await p2pcs[1].stream_handler(proto, handle_proto)
    assert proto in p2pcs[1].control.handlers
    assert handle_proto == p2pcs[1].control.handlers[proto]

    # test case: test the stream handler `handle_proto`

    _, stream = await p2pcs[0].stream_open(peer_id_1, (proto,))

    # wait until the handler function starts blocking waiting for the data
    # because we haven't sent the data, we know the handler function must still blocking waiting.
    # get the task of the protocol handler
    await stream.send_all(bytes_to_send)

    # wait for the handler to finish
    await stream.close()

    await event_handler_finished.wait()

    # test case: two streams to different handlers respectively
    another_proto = "another_protocol123"
    another_bytes_to_send = b"456"
    event_another_proto = anyio.create_event()

    async def handle_another_proto(stream_info, stream):
        await event_another_proto.set()
        bytes_received = await stream.receive_exactly(len(another_bytes_to_send))
        assert bytes_received == another_bytes_to_send

    await p2pcs[1].stream_handler(another_proto, handle_another_proto)
    assert another_proto in p2pcs[1].control.handlers
    assert handle_another_proto == p2pcs[1].control.handlers[another_proto]

    _, another_stream = await p2pcs[0].stream_open(peer_id_1, (another_proto,))
    await event_another_proto.wait()

    # we know at this moment the handler must still blocking wait

    await another_stream.send_all(another_bytes_to_send)

    await another_stream.close()

    # test case: registering twice can override the previous registration
    event_third = anyio.create_event()

    async def handler_third(stream_info, stream):
        await event_third.set()

    await p2pcs[1].stream_handler(another_proto, handler_third)
    assert another_proto in p2pcs[1].control.handlers
    # ensure the handler is override
    assert handler_third == p2pcs[1].control.handlers[another_proto]

    await p2pcs[0].stream_open(peer_id_1, (another_proto,))
    # ensure the overriding handler is called when the protocol is opened a stream
    await event_third.wait()


@pytest.mark.parametrize("enable_control", (True,))
@pytest.mark.anyio
async def test_client_stream_handler_failure(p2pcs):
    peer_id_1, _ = await p2pcs[1].identify()
    await connect_safe(p2pcs[0], p2pcs[1])

    proto = "123"

    # test case: registered a wrong protocol name
    async def handle_proto_correct_params(stream_info, stream):
        pass

    await p2pcs[1].stream_handler("another_protocol", handle_proto_correct_params)
    with pytest.raises(ControlFailure):
        await p2pcs[0].stream_open(peer_id_1, (proto,))


@pytest.mark.parametrize("enable_control, enable_dht", ((True, True),))
@pytest.mark.anyio
async def test_client_dht_find_peer_success(p2pcs):
    peer_id_2, _ = await p2pcs[2].identify()
    await connect_safe(p2pcs[0], p2pcs[1])
    await connect_safe(p2pcs[1], p2pcs[2])
    pinfo = await p2pcs[0].dht_find_peer(peer_id_2)
    assert pinfo.peer_id == peer_id_2
    assert len(pinfo.addrs) != 0


@pytest.mark.parametrize("enable_control, enable_dht", ((True, True),))
@pytest.mark.anyio
async def test_client_dht_find_peer_failure(peer_id_random, p2pcs):
    peer_id_2, _ = await p2pcs[2].identify()
    await connect_safe(p2pcs[0], p2pcs[1])
    # test case: `peer_id` not found
    with pytest.raises(ControlFailure):
        await p2pcs[0].dht_find_peer(peer_id_random)
    # test case: no route to the peer with peer_id_2
    with pytest.raises(ControlFailure):
        await p2pcs[0].dht_find_peer(peer_id_2)


@pytest.mark.parametrize("enable_control, enable_dht", ((True, True),))
@pytest.mark.anyio
async def test_client_dht_find_peers_connected_to_peer_success(p2pcs):
    peer_id_2, _ = await p2pcs[2].identify()
    await connect_safe(p2pcs[0], p2pcs[1])
    # test case: 0 <-> 1 <-> 2
    await connect_safe(p2pcs[1], p2pcs[2])
    pinfos_connecting_to_2 = await p2pcs[0].dht_find_peers_connected_to_peer(peer_id_2)
    # TODO: need to confirm this behaviour. Why the result is the PeerInfo of `peer_id_2`?
    assert len(pinfos_connecting_to_2) == 1


@pytest.mark.parametrize("enable_control, enable_dht", ((True, True),))
@pytest.mark.anyio
async def test_client_dht_find_peers_connected_to_peer_failure(peer_id_random, p2pcs):
    peer_id_2, _ = await p2pcs[2].identify()
    await connect_safe(p2pcs[0], p2pcs[1])
    # test case: request for random peer_id
    pinfos = await p2pcs[0].dht_find_peers_connected_to_peer(peer_id_random)
    assert not pinfos
    # test case: no route to the peer with peer_id_2
    pinfos = await p2pcs[0].dht_find_peers_connected_to_peer(peer_id_2)
    assert not pinfos


@pytest.mark.parametrize("enable_control, enable_dht", ((True, True),))
@pytest.mark.anyio
async def test_client_dht_find_providers(p2pcs):
    await connect_safe(p2pcs[0], p2pcs[1])
    # borrowed from https://github.com/ipfs/go-cid#parsing-string-input-from-users
    content_id_bytes = b"\x01r\x12 \xc0F\xc8\xechB\x17\xf0\x1b$\xb9\xecw\x11\xde\x11Cl\x8eF\xd8\x9a\xf1\xaeLa?\xb0\xaf\xe6K\x8b"  # noqa: E501
    pinfos = await p2pcs[1].dht_find_providers(content_id_bytes, 100)
    assert not pinfos


@pytest.mark.parametrize("enable_control, enable_dht", ((True, True),))
@pytest.mark.anyio
async def test_client_dht_get_closest_peers(p2pcs):
    await connect_safe(p2pcs[0], p2pcs[1])
    await connect_safe(p2pcs[1], p2pcs[2])
    peer_ids_1 = await p2pcs[1].dht_get_closest_peers(b"123")
    assert len(peer_ids_1) == 2


@pytest.mark.parametrize("enable_control, enable_dht", ((True, True),))
@pytest.mark.anyio
async def test_client_dht_get_public_key_success(peer_id_random, p2pcs):
    peer_id_0, _ = await p2pcs[0].identify()
    peer_id_1, _ = await p2pcs[1].identify()
    await connect_safe(p2pcs[0], p2pcs[1])
    await connect_safe(p2pcs[1], p2pcs[2])
    await anyio.sleep(0.2)
    pk0 = await p2pcs[0].dht_get_public_key(peer_id_0)
    pk1 = await p2pcs[0].dht_get_public_key(peer_id_1)
    assert pk0 != pk1


@pytest.mark.parametrize("enable_control, enable_dht", ((True, True),))
@pytest.mark.anyio
async def test_client_dht_get_public_key_failure(peer_id_random, p2pcs):
    peer_id_2, _ = await p2pcs[2].identify()
    await connect_safe(p2pcs[0], p2pcs[1])
    await connect_safe(p2pcs[1], p2pcs[2])
    # test case: failed to get the pubkey of the peer_id_random
    with pytest.raises(ControlFailure):
        await p2pcs[0].dht_get_public_key(peer_id_random)
    # test case: should get the pubkey of the peer_id_2
    await p2pcs[0].dht_get_public_key(peer_id_2)


@pytest.mark.parametrize("enable_control, enable_dht", ((True, True),))
@pytest.mark.anyio
async def test_client_dht_get_value(p2pcs):
    key_not_existing = b"/123/456"
    # test case: no peer in table
    with pytest.raises(ControlFailure):
        await p2pcs[0].dht_get_value(key_not_existing)
    await connect_safe(p2pcs[0], p2pcs[1])
    # test case: routing not found
    with pytest.raises(ControlFailure):
        await p2pcs[0].dht_get_value(key_not_existing)


@pytest.mark.parametrize("enable_control, enable_dht", ((True, True),))
@pytest.mark.anyio
async def test_client_dht_search_value(p2pcs):
    key_not_existing = b"/123/456"
    # test case: no peer in table
    with pytest.raises(ControlFailure):
        await p2pcs[0].dht_search_value(key_not_existing)
    await connect_safe(p2pcs[0], p2pcs[1])
    # test case: non-existing key
    pinfos = await p2pcs[0].dht_search_value(key_not_existing)
    assert len(pinfos) == 0


# FIXME
@pytest.mark.skip("Temporary skip the test since dht is not used often")
@pytest.mark.parametrize("enable_control, enable_dht", ((True, True),))
@pytest.mark.anyio
async def test_client_dht_put_value(p2pcs):
    peer_id_0, _ = await p2pcs[0].identify()
    await connect_safe(p2pcs[0], p2pcs[1])

    # test case: valid key
    pk0 = await p2pcs[0].dht_get_public_key(peer_id_0)
    # make the `key` from pk0
    algo = multihash.Func.sha2_256
    value = pk0.data
    mh_digest = multihash.digest(value, algo)
    mh_digest_bytes = mh_digest.encode()
    key = b"/pk/" + mh_digest_bytes
    await p2pcs[0].dht_put_value(key, value)
    # test case: get_value
    await p2pcs[1].dht_get_value(key) == value

    # test case: invalid key
    key_invalid = b"/123/456"
    with pytest.raises(ControlFailure):
        await p2pcs[0].dht_put_value(key_invalid, key_invalid)


@pytest.mark.parametrize("enable_control, enable_dht", ((True, True),))
@pytest.mark.anyio
async def test_client_dht_provide(p2pcs):
    peer_id_0, _ = await p2pcs[0].identify()
    await connect_safe(p2pcs[0], p2pcs[1])
    # test case: no providers
    content_id_bytes = b"\x01r\x12 \xc0F\xc8\xechB\x17\xf0\x1b$\xb9\xecw\x11\xde\x11Cl\x8eF\xd8\x9a\xf1\xaeLa?\xb0\xaf\xe6K\x8b"  # noqa: E501
    pinfos_empty = await p2pcs[1].dht_find_providers(content_id_bytes, 100)
    assert not pinfos_empty
    # test case: p2pcs[0] provides
    await p2pcs[0].dht_provide(content_id_bytes)
    pinfos = await p2pcs[1].dht_find_providers(content_id_bytes, 100)
    assert len(pinfos) == 1
    assert pinfos[0].peer_id == peer_id_0


@pytest.mark.parametrize("enable_control, enable_connmgr", ((True, True),))
@pytest.mark.anyio
async def test_client_connmgr_tag_peer(peer_id_random, p2pcs):
    peer_id_0, _ = await p2pcs[0].identify()
    # test case: tag myself
    await p2pcs[0].connmgr_tag_peer(peer_id_0, "123", 123)
    # test case: tag others
    await p2pcs[1].connmgr_tag_peer(peer_id_0, "123", 123)
    # test case: tag the same peers multiple times
    await p2pcs[1].connmgr_tag_peer(peer_id_0, "456", 456)
    # test case: tag multiple peers
    await p2pcs[1].connmgr_tag_peer(peer_id_random, "123", 1)
    # test case: tag the same peer with the same tag but different weight
    await p2pcs[1].connmgr_tag_peer(peer_id_random, "123", 123)


@pytest.mark.parametrize("enable_control, enable_connmgr", ((True, True),))
@pytest.mark.anyio
async def test_client_connmgr_untag_peer(peer_id_random, p2pcs):
    # test case: untag an inexisting tag
    await p2pcs[0].connmgr_untag_peer(peer_id_random, "123")
    # test case: untag a tag
    await p2pcs[0].connmgr_tag_peer(peer_id_random, "123", 123)
    await p2pcs[0].connmgr_untag_peer(peer_id_random, "123")
    # test case: untag a tag twice
    await p2pcs[0].connmgr_untag_peer(peer_id_random, "123")


@pytest.mark.skip("Skipped because automatic trim is not stable to test")
@pytest.mark.parametrize("enable_control, enable_connmgr", ((True, True),))
@pytest.mark.anyio
async def test_client_connmgr_trim_automatically_by_connmgr(p2pcs):
    # test case: due to `connHi=2` and `connLo=1`, when `p2pcs[1]` connecting to the third peer,
    #            `p2pcs[3]`, the connmgr of `p2pcs[1]` will try to prune the connections, down to
    #            `connLo=1`.
    peer_id_0, maddrs_0 = await p2pcs[0].identify()
    peer_id_2, maddrs_2 = await p2pcs[2].identify()
    peer_id_3, maddrs_3 = await p2pcs[3].identify()
    await p2pcs[1].connect(peer_id_0, maddrs_0)
    await p2pcs[1].connect(peer_id_2, maddrs_2)
    await p2pcs[1].connect(peer_id_3, maddrs_3)
    # sleep to wait for the goroutine `Connmgr.TrimOpenConns` invoked by `mNotifee.Connected`
    await anyio.sleep(1)
    assert len(await p2pcs[1].list_peers()) == 1


@pytest.mark.parametrize("enable_control, enable_connmgr", ((True, True),))
@pytest.mark.anyio
async def test_client_connmgr_trim(p2pcs):
    peer_id_0, _ = await p2pcs[0].identify()
    peer_id_2, _ = await p2pcs[2].identify()
    await connect_safe(p2pcs[1], p2pcs[0])
    await connect_safe(p2pcs[1], p2pcs[2])
    assert len(await p2pcs[1].list_peers()) == 2
    await p2pcs[1].connmgr_tag_peer(peer_id_0, "123", 1)
    await p2pcs[1].connmgr_tag_peer(peer_id_2, "123", 2)
    # trim the connections, the number of connections should go down to the low watermark
    await p2pcs[1].connmgr_trim()
    peers_1 = await p2pcs[1].list_peers()
    assert len(peers_1) == 1
    assert peers_1[0].peer_id == peer_id_2


@pytest.mark.parametrize("enable_control, enable_pubsub", ((True, True),))
@pytest.mark.anyio
async def test_client_pubsub_get_topics(p2pcs):
    topics = await p2pcs[0].pubsub_get_topics()
    assert len(topics) == 0


@pytest.mark.parametrize("enable_control, enable_pubsub", ((True, True),))
@pytest.mark.anyio
async def test_client_pubsub_list_topic_peers(p2pcs):
    peers = await p2pcs[0].pubsub_list_peers("123")
    assert len(peers) == 0


@pytest.mark.parametrize("enable_control, enable_pubsub", ((True, True),))
@pytest.mark.anyio
async def test_client_pubsub_publish(p2pcs):
    await p2pcs[0].pubsub_publish("123", b"data")


@pytest.mark.parametrize("enable_control, enable_pubsub", ((True, True),))
@pytest.mark.anyio
async def test_client_pubsub_subscribe(p2pcs):
    peer_id_0, _ = await p2pcs[0].identify()
    peer_id_1, _ = await p2pcs[1].identify()
    await connect_safe(p2pcs[0], p2pcs[1])
    await connect_safe(p2pcs[1], p2pcs[2])
    topic = "topic123"
    data = b"data"
    stream_0 = await p2pcs[0].pubsub_subscribe(topic)
    stream_1 = await p2pcs[1].pubsub_subscribe(topic)
    # test case: `get_topics` after subscriptions
    assert topic in await p2pcs[0].pubsub_get_topics()
    assert topic in await p2pcs[1].pubsub_get_topics()
    # wait for mesh built
    await anyio.sleep(2)
    # test case: `list_topic_peers` after subscriptions
    assert peer_id_0 in await p2pcs[1].pubsub_list_peers(topic)
    assert peer_id_1 in await p2pcs[0].pubsub_list_peers(topic)
    # test case: publish, and both clients receive data
    await p2pcs[0].pubsub_publish(topic, data)
    pubsub_msg_0 = p2pd_pb.PSMessage()
    await read_pbmsg_safe(stream_0, pubsub_msg_0)
    assert pubsub_msg_0.data == data
    pubsub_msg_1 = p2pd_pb.PSMessage()
    await read_pbmsg_safe(stream_1, pubsub_msg_1)
    assert pubsub_msg_1.data == data
    # test case: publish more data
    another_data_0 = b"another_data_0"
    another_data_1 = b"another_data_1"
    await p2pcs[0].pubsub_publish(topic, another_data_0)
    await p2pcs[0].pubsub_publish(topic, another_data_1)
    pubsub_msg_1_0 = p2pd_pb.PSMessage()
    await read_pbmsg_safe(stream_1, pubsub_msg_1_0)
    pubsub_msg_1_1 = p2pd_pb.PSMessage()
    await read_pbmsg_safe(stream_1, pubsub_msg_1_1)
    assert set([pubsub_msg_1_0.data, pubsub_msg_1_1.data]) == set(
        [another_data_0, another_data_1]
    )
    # test case: subscribe to multiple topics
    another_topic = "topic456"
    await p2pcs[0].pubsub_subscribe(another_topic)
    stream_1_another = await p2pcs[1].pubsub_subscribe(another_topic)
    await p2pcs[0].pubsub_publish(another_topic, another_data_0)
    pubsub_msg_1_another = p2pd_pb.PSMessage()
    await read_pbmsg_safe(stream_1_another, pubsub_msg_1_another)
    assert pubsub_msg_1_another.data == another_data_0
    # test case: test `from`
    assert ID(pubsub_msg_1_1.from_id) == peer_id_0
    # test case: test `from_id`, when it is sent through 1 hop(p2pcs[1])
    stream_2 = await p2pcs[2].pubsub_subscribe(topic)
    another_data_2 = b"another_data_2"
    await p2pcs[0].pubsub_publish(topic, another_data_2)
    pubsub_msg_2_0 = p2pd_pb.PSMessage()
    await read_pbmsg_safe(stream_2, pubsub_msg_2_0)
    assert ID(pubsub_msg_2_0.from_id) == peer_id_0
    # test case: unsubscribe by closing the stream
    await stream_0.close()
    await anyio.sleep(0)
    assert topic not in await p2pcs[0].pubsub_get_topics()

    async def is_peer_removed_from_topic():
        return peer_id_0 not in await p2pcs[1].pubsub_list_peers(topic)

    await try_until_success(is_peer_removed_from_topic)
