import base58

import multiaddr

import p2pclient.pb.p2pd_pb2 as pb


class ProtocolNoCheck:
    """This class is a temporary workaround used for `add_protocol`. It bypasses
    the checks on the attributes `code`, `size`, `name`, `vcode`
    """
    def __init__(self, code, size, name, vcode):
        self.code = code
        self.size = size
        self.name = name
        self.vcode = vcode


P_P2P_CIRCUIT = 290

multiaddr.protocols.add_protocol(
    ProtocolNoCheck(
        P_P2P_CIRCUIT,
        0,
        "p2p-circuit",
        multiaddr.codec.code_to_varint(P_P2P_CIRCUIT),
    )
)


class Multiaddr(multiaddr.Multiaddr):
    """Currently use `multiaddr.Multiaddr` as the backend.
    """

    def __init__(self, *, bytes_addr=None, string_addr=None):
        # e.g. maddr_bytes = b'\x04\x7f\x00\x00\x01\x06\xc2\xc9'
        if bytes_addr is not None:
            maddr_hex = bytes_addr.hex()  # '047f00000106c2c9'
            bytes_addr = maddr_hex.encode()  # b'047f00000106c2c9'
        super().__init__(bytes_addr=bytes_addr, string_addr=string_addr)

    def to_bytes(self):
        strange_bytes = super().to_bytes()  # b'047f00000106c2c9'
        maddr_hex = str(strange_bytes)[2:-1]  # '047f00000106c2c9'
        return bytes.fromhex(maddr_hex)

    def to_string(self):
        return multiaddr.codec.bytes_to_string(self._bytes)


class PeerID:
    _bytes = None

    def __init__(self, peer_id_bytes):
        # TODO: should add checks for the validity of peer_id
        self._bytes = peer_id_bytes

    def __eq__(self, other):
        return self._bytes == other._bytes

    def __ne__(self, other):
        return not (self == other)

    def __repr__(self):
        return "<PeerID {}>".format(self.to_string()[2:10])

    def to_bytes(self):
        return self._bytes

    def to_string(self):
        return base58.b58encode(self._bytes).decode()

    @classmethod
    def from_string(cls, peer_id_string):
        peer_id_bytes = base58.b58decode(peer_id_string)
        pid = PeerID(peer_id_bytes)
        return pid


class StreamInfo:
    peer_id = None
    addr = None
    proto = None

    def __init__(self, peer_id, addr, proto):
        self.peer_id = peer_id
        self.addr = addr
        self.proto = proto

    def __repr__(self):
        return "<StreamInfo peer_id={} addr={} proto={}>".format(
            self.peer_id,
            self.addr,
            self.proto,
        )

    def to_pb(self):
        pb_msg = pb.StreamInfo(
            peer=self.peer_id.to_bytes(),
            addr=self.addr.to_bytes(),
            proto=self.proto,
        )
        return pb_msg

    @classmethod
    def from_pb(cls, pb_msg):
        stream_info = cls(
            peer_id=PeerID(pb_msg.peer),
            addr=Multiaddr(bytes_addr=pb_msg.addr),
            proto=pb_msg.proto,
        )
        return stream_info


class PeerInfo:
    peer_id = None
    addrs = None

    def __init__(self, peer_id, addrs):
        self.peer_id = peer_id
        self.addrs = addrs

    def __repr__(self):
        return "<PeerInfo peer_id={} addrs={}>".format(
            self.peer_id,
            self.addrs,
        )

    @classmethod
    def from_pb(cls, peer_info_pb):
        peer_id = PeerID(peer_info_pb.id)
        addrs = [Multiaddr(bytes_addr=addr) for addr in peer_info_pb.addrs]
        return cls(peer_id, addrs)
