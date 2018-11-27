import asyncio
from collections import (
    namedtuple,
)
import os
import subprocess
import time

import pytest

from p2pclient.datastructures import (
    Multiaddr,
    PeerID,
)
from p2pclient.p2pclient import (
    Client,
    ControlFailure,
)


NUM_P2PD = 3
P2PDInfo = namedtuple('P2PDInfo', ['proc', 'control_path', 'listen_path'])

p2pd_procs = {}


@pytest.fixture(scope="module")
def peer_id_random():
    return PeerID.from_string("QmcgpsyWgH8Y8ajJz1Cu72KnS5uo2Aa2LpzU7kinSupNK1")


@pytest.fixture(scope="function", autouse=True)
def spinup_p2pds(request):
    """Spin up `NUM_P2PD` p2pds at the first test, to reduce the waiting time to spin up
    p2pds every time
    """
    for i in range(NUM_P2PD):
        control_path = f"/tmp/test_p2pd_control_{i}"
        listen_path = f"/tmp/test_p2pd_listen_path_{i}"
        try:
            os.unlink(listen_path)
        except FileNotFoundError:
            pass
        proc = start_p2pd(control_path)
        p2pd_info = P2PDInfo(proc, control_path, listen_path)
        p2pd_procs[i] = p2pd_info

    time.sleep(2)

    yield

    # teardown
    for _, p2pd_info in p2pd_procs.items():
        p2pd_info.proc.terminate()
        p2pd_info.proc.wait()


def start_p2pd(control_path):
    try:
        os.unlink(control_path)
    except FileNotFoundError:
        pass
    f_log = open('/tmp/p2pd_{}.log'.format(control_path[5:]), 'wb')
    return subprocess.Popen(
        [
            "p2pd",
            f"-sock={control_path}",
            "-dht",
        ],
        stdout=f_log,
        stderr=f_log,
    )


async def make_p2pclient(number):
    if number >= NUM_P2PD:
        raise ValueError(f"number={number} >= NUM_P2PD={NUM_P2PD}")
    p2pd_info = p2pd_procs[number]
    c = Client(p2pd_info.control_path, p2pd_info.listen_path)
    await c.listen()
    return c


@pytest.mark.asyncio
async def test_client_identify():
    c = await make_p2pclient(0)
    await c.identify()


@pytest.mark.asyncio
async def test_client_connect_success():
    c0 = await make_p2pclient(0)
    c1 = await make_p2pclient(1)
    peer_id_0, maddrs_0 = await c0.identify()
    peer_id_1, maddrs_1 = await c1.identify()
    await c0.connect(peer_id_1, maddrs_1)
    # test case: repeated connections
    await c1.connect(peer_id_0, maddrs_0)


@pytest.mark.asyncio
async def test_client_connect_failure(peer_id_random):
    c0 = await make_p2pclient(0)
    c1 = await make_p2pclient(1)
    peer_id_1, maddrs_1 = await c1.identify()
    await c0.identify()
    # test case: `peer_id` mismatches
    with pytest.raises(ControlFailure):
        await c0.connect(peer_id_random, maddrs_1)
    # test case: empty maddrs
    with pytest.raises(ControlFailure):
        await c0.connect(peer_id_1, [])
    # test case: wrong maddrs
    with pytest.raises(ControlFailure):
        await c0.connect(peer_id_1, [Multiaddr(string_addr="/ip4/127.0.0.1/udp/0")])


@pytest.mark.asyncio
async def test_client_stream_open_success():
    c0 = await make_p2pclient(0)
    c1 = await make_p2pclient(1)

    peer_id_1, maddrs_1 = await c1.identify()
    await c0.connect(peer_id_1, maddrs_1)

    proto = "123"

    async def handle_proto(stream_info, reader, writer):
        assert reader.at_eof()

    await c1.stream_handler(proto, handle_proto)

    # test case: normal
    stream_info, _, writer = await c0.stream_open(
        peer_id_1,
        [proto],
    )
    assert stream_info.peer_id == peer_id_1
    assert stream_info.addr in maddrs_1
    assert stream_info.proto == "123"
    writer.close()
    await asyncio.sleep(0.1)  # yield

    # test case: open with multiple protocols
    stream_info, _, writer = await c0.stream_open(
        peer_id_1,
        [proto, "another_protocol"],
    )
    assert stream_info.peer_id == peer_id_1
    assert stream_info.addr in maddrs_1
    assert stream_info.proto == "123"
    writer.close()
    await asyncio.sleep(0.1)  # yield


@pytest.mark.asyncio
async def test_client_stream_open_failure():
    c0 = await make_p2pclient(0)
    c1 = await make_p2pclient(1)

    peer_id_1, maddrs_1 = await c1.identify()
    await c0.connect(peer_id_1, maddrs_1)

    proto = "123"

    # test case: `stream_open` to a peer who didn't register the protocol
    with pytest.raises(ControlFailure):
        await c0.stream_open(peer_id_1, [proto])

    # test case: `stream_open` to a peer for a non-registered protocol
    async def handle_proto(stream_info, reader, writer):
        pass

    await c1.stream_handler(proto, handle_proto)
    with pytest.raises(ControlFailure):
        await c0.stream_open(
            peer_id_1,
            ["another_protocol"],
        )


@pytest.mark.asyncio
async def test_client_stream_handler_success():
    c0 = await make_p2pclient(0)
    c1 = await make_p2pclient(1)

    peer_id_1, maddrs_1 = await c1.identify()
    await c0.connect(peer_id_1, maddrs_1)

    proto = "123"
    bytes_to_send = b"yoyoyoyoyog"

    async def handle_proto(stream_info, reader, writer):
        bytes_received = await reader.read(len(bytes_to_send))
        assert bytes_received == bytes_to_send
        assert reader.at_eof()

    await c1.stream_handler(proto, handle_proto)

    _, _, writer = await c0.stream_open(
        peer_id_1,
        [proto],
    )
    # test case: test the stream handler `handle_proto`
    writer.write(bytes_to_send)
    await writer.drain()
    writer.close()
    await asyncio.sleep(0.1)  # yield


@pytest.mark.asyncio
async def test_client_stream_handler_failure():
    c0 = await make_p2pclient(0)
    c1 = await make_p2pclient(1)

    peer_id_1, maddrs_1 = await c1.identify()
    await c0.connect(peer_id_1, maddrs_1)

    proto = "123"

    # test case: registered a wrong protocol name
    async def handle_proto_correct_params(stream_info, reader, writer):
        pass

    await c1.stream_handler("another_protocol", handle_proto_correct_params)
    with pytest.raises(ControlFailure):
        await c0.stream_open(peer_id_1, [proto])

    # test case: registered a handler with the wrong signature(parameters)
    async def handle_proto_wrong_params(stream_info, reader):
        pass

    with pytest.raises(ControlFailure):
        await c1.stream_handler(proto, handle_proto_wrong_params)


@pytest.mark.asyncio
async def test_client_find_peer_success():
    c0 = await make_p2pclient(0)
    c1 = await make_p2pclient(1)
    c2 = await make_p2pclient(2)
    peer_id_0, maddrs_0 = await c0.identify()
    peer_id_1, maddrs_1 = await c1.identify()
    peer_id_2, _ = await c2.identify()
    await c1.connect(peer_id_0, maddrs_0)
    await c2.connect(peer_id_1, maddrs_1)
    pinfo = await c0.find_peer(peer_id_2)
    assert pinfo.peer_id == peer_id_2
    assert len(pinfo.addrs) != 0


@pytest.mark.asyncio
async def test_client_find_peer_failure(peer_id_random):
    c0 = await make_p2pclient(0)
    c1 = await make_p2pclient(1)
    c2 = await make_p2pclient(2)
    peer_id_0, maddrs_0 = await c0.identify()
    peer_id_2, _ = await c2.identify()
    await c1.connect(peer_id_0, maddrs_0)
    # test case: `peer_id` not found
    with pytest.raises(ControlFailure):
        await c0.find_peer(peer_id_random)
    # test case: no route to the peer with peer_id_2
    with pytest.raises(ControlFailure):
        await c0.find_peer(peer_id_2)


@pytest.mark.asyncio
async def test_client_find_peers_connected_to_peer_success(peer_id_random):
    c0 = await make_p2pclient(0)
    c1 = await make_p2pclient(1)
    c2 = await make_p2pclient(2)
    peer_id_0, maddrs_0 = await c0.identify()
    peer_id_1, maddrs_1 = await c1.identify()
    peer_id_2, _ = await c2.identify()
    await c1.connect(peer_id_0, maddrs_0)
    await c2.connect(peer_id_1, maddrs_1)
    pinfos_connecting_to_2 = await c0.find_peers_connected_to_peer(peer_id_2)
    assert len(pinfos_connecting_to_2) == 1
    print("\n!@# ", peer_id_0, peer_id_1, peer_id_2)
    assert pinfos_connecting_to_2[0].peer_id == peer_id_1
    # # test case: no route to the peer with peer_id_2
    # with pytest.raises(ControlFailure):
    #     await c0.find_peer(peer_id_2)
