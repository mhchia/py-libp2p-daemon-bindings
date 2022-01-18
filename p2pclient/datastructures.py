from p2pclient.libp2p_stubs.peer.id import ID
from p2pclient.libp2p_stubs.peer.peerinfo import PeerInfo as PeerInfoLibP2P
from multiaddr import Multiaddr

from .pb import p2pd_pb2


class StreamInfo:
    peer_id: ID
    addr: Multiaddr
    proto: str

    def __init__(self, peer_id: ID, addr: Multiaddr, proto: str) -> None:
        self.peer_id = peer_id
        self.addr = addr
        self.proto = proto

    def __repr__(self) -> str:
        return (
            f"<StreamInfo peer_id={self.peer_id} addr={self.addr} proto={self.proto}>"
        )

    def to_pb(self) -> p2pd_pb2.StreamInfo:
        pb_msg = p2pd_pb2.StreamInfo(
            peer=self.peer_id.to_bytes(), addr=self.addr.to_bytes(), proto=self.proto
        )
        return pb_msg

    @classmethod
    def from_pb(cls, pb_msg: p2pd_pb2.StreamInfo) -> "StreamInfo":
        stream_info = cls(
            peer_id=ID(pb_msg.peer), addr=Multiaddr(pb_msg.addr), proto=pb_msg.proto
        )
        return stream_info


class PeerInfo(PeerInfoLibP2P):
    @classmethod
    def from_pb(cls, peer_info_pb: p2pd_pb2.PeerInfo) -> PeerInfoLibP2P:
        peer_id = ID(peer_info_pb.id)
        addrs = [Multiaddr(addr) for addr in peer_info_pb.addrs]
        return PeerInfoLibP2P(peer_id, addrs)
