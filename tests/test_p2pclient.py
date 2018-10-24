from p2pd.config import (
    control_path,
    listen_path,
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


def test_client_integration():
    c = Client(control_path, listen_path)
    peer_id, maddrs = c.identify()
    maddrs = [Multiaddr(string_addr="/ip4/127.0.0.1/tcp/10000")]
    peer_id = PeerID.from_string("QmS5QmciTXXnCUCyxud5eWFenUMAmvAWSDa1c7dvdXRMZ7")
    c.connect(peer_id, maddrs)
    c.stream_open(
        peer_id,
        [
            "/shardPeerRequest/1.0.0",
            "/generalRequest/1.0.0",
        ],
    )

if __name__ == "__main__":
    test_client_integration()
