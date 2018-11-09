import asyncio
import os

import pytest

from p2pd.config import (
    control_path,
    listen_path,
)
from p2pd.constants import (
    BUFFER_SIZE,
)
from p2pd.p2pclient import (
    Client,
    Multiaddr,
    PeerID,
)



def test_multiaddr():
    string_addr = "/ip4/127.0.0.1/tcp/10000"
    bytes_addr = b"\x04\x7f\x00\x00\x01\x06'\x10"
    # test initialized with `string_addr`
    m = Multiaddr(string_addr=string_addr)
    assert m.to_bytes() == bytes_addr
    assert m.to_string() == string_addr
    # test initialized with `bytes_addr`
    m2 = Multiaddr(bytes_addr=bytes_addr)
    assert m.to_bytes() == bytes_addr
    assert m.to_string() == string_addr
    # test both are the same
    assert m == m2
    # test not eqaul
    assert m != Multiaddr(string_addr="/ip4/127.0.0.1/tcp/10001")
    assert m != Multiaddr(string_addr="/ip4/0.0.0.0/tcp/10000")
    assert m != Multiaddr(string_addr="/ip4/127.0.0.1/udp/10000")


def test_peer_id():
    peer_id_string = "QmS5QmciTXXnCUCyxud5eWFenUMAmvAWSDa1c7dvdXRMZ7"
    peer_id_bytes = b'\x12 7\x87F.[\xb5\xb1o\xe5*\xc7\xb9\xbb\x11:"Z|j2\x8ad\x1b\xa6\xe5<Ip\xfe\xb4\xf5v'  # noqa: E501
    # test initialized with bytes
    peer_id = PeerID(peer_id_bytes)
    assert peer_id.to_bytes() == peer_id_bytes
    assert peer_id.to_string() == peer_id_string
    # test initialized with string
    peer_id_2 = PeerID.from_string(peer_id_string)
    assert peer_id_2.to_bytes() == peer_id_bytes
    assert peer_id_2.to_string() == peer_id_string
    # test equal
    assert peer_id == peer_id_2
    # test not equal
    peer_id_3 = PeerID.from_string("QmbmfNDEth7Ucvjuxiw3SP3E4PoJzbk7g4Ge6ZDigbCsNp")
    assert peer_id != peer_id_3


def start_p2pd(control_path):
    try:
        os.unlink(control_path)
    except FileNotFoundError:
        pass
    os.system("p2pd -sock={} &".format(control_path))



@pytest.mark.asyncio
async def test_client_integration():
    control_path_0 = "/tmp/test_p2pd_control_0"
    listen_path_0 = "/tmp/test_p2pd_listen_path_0"
    control_path_1 = "/tmp/test_p2pd_control_1"
    listen_path_1 = "/tmp/test_p2pd_listen_path_1"
    try:
        os.unlink(listen_path_0)
    except FileNotFoundError:
        pass
    try:
        os.unlink(listen_path_1)
    except FileNotFoundError:
        pass
    os.system("killall p2pd")
    start_p2pd(control_path_0)
    start_p2pd(control_path_1)
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
        print("stream_info = {}".format(stream_info))
        bytes_received = await reader.read(BUFFER_SIZE)
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


if __name__ == "__main__":
    # loop = asyncio.get_event_loop()
    pass
