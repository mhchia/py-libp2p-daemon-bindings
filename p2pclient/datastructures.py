import binascii

import base58

from multiaddr import (
    Multiaddr,
)

from .pb import p2pd_pb2 as pb


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
            addr=binascii.unhexlify(self.addr.to_bytes()),
            proto=self.proto,
        )
        return pb_msg

    @classmethod
    def from_pb(cls, pb_msg):
        stream_info = cls(
            peer_id=PeerID(pb_msg.peer),
            addr=Multiaddr(binascii.hexlify(pb_msg.addr)),
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
        addrs = [Multiaddr(binascii.hexlify(addr)) for addr in peer_info_pb.addrs]
        return cls(peer_id, addrs)
