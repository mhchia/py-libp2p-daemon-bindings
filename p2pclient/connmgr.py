from p2pclient.libp2p_stubs.peer.id import ID

from .control import DaemonConnector
from .pb import p2pd_pb2 as p2pd_pb
from .utils import raise_if_failed, read_pbmsg_safe, write_pbmsg


class ConnectionManagerClient:
    daemon_connector: DaemonConnector

    def __init__(self, daemon_connector: DaemonConnector) -> None:
        self.daemon_connector = daemon_connector

    async def tag_peer(self, peer_id: ID, tag: str, weight: int) -> None:
        """TAG_PEER
        """
        connmgr_req = p2pd_pb.ConnManagerRequest(
            type=p2pd_pb.ConnManagerRequest.TAG_PEER,
            peer=peer_id.to_bytes(),
            tag=tag,
            weight=weight,
        )
        req = p2pd_pb.Request(type=p2pd_pb.Request.CONNMANAGER, connManager=connmgr_req)
        stream = await self.daemon_connector.open_connection()
        await write_pbmsg(stream, req)
        resp = p2pd_pb.Response()
        await read_pbmsg_safe(stream, resp)
        await stream.close()
        raise_if_failed(resp)

    async def untag_peer(self, peer_id: ID, tag: str) -> None:
        """UNTAG_PEER
        """
        connmgr_req = p2pd_pb.ConnManagerRequest(
            type=p2pd_pb.ConnManagerRequest.UNTAG_PEER, peer=peer_id.to_bytes(), tag=tag
        )
        req = p2pd_pb.Request(type=p2pd_pb.Request.CONNMANAGER, connManager=connmgr_req)
        stream = await self.daemon_connector.open_connection()
        await write_pbmsg(stream, req)
        resp = p2pd_pb.Response()
        await read_pbmsg_safe(stream, resp)
        await stream.close()
        raise_if_failed(resp)

    async def trim(self) -> None:
        """TRIM
        """
        connmgr_req = p2pd_pb.ConnManagerRequest(type=p2pd_pb.ConnManagerRequest.TRIM)
        req = p2pd_pb.Request(type=p2pd_pb.Request.CONNMANAGER, connManager=connmgr_req)
        stream = await self.daemon_connector.open_connection()
        await write_pbmsg(stream, req)
        resp = p2pd_pb.Response()
        await read_pbmsg_safe(stream, resp)
        await stream.close()
        raise_if_failed(resp)
