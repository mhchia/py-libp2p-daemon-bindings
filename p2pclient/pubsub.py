from typing import Tuple

import anyio
from p2pclient.libp2p_stubs.peer.id import ID

from .control import DaemonConnector
from .pb import p2pd_pb2 as p2pd_pb
from .utils import raise_if_failed, read_pbmsg_safe, write_pbmsg


class PubSubClient:
    daemon_connector: DaemonConnector

    def __init__(self, daemon_connector: DaemonConnector) -> None:
        self.daemon_connector = daemon_connector

    async def get_topics(self) -> Tuple[str, ...]:
        """PUBSUB GET_TOPICS
        """
        pubsub_req = p2pd_pb.PSRequest(type=p2pd_pb.PSRequest.GET_TOPICS)
        req = p2pd_pb.Request(type=p2pd_pb.Request.PUBSUB, pubsub=pubsub_req)
        stream = await self.daemon_connector.open_connection()
        await write_pbmsg(stream, req)
        resp = p2pd_pb.Response()
        await read_pbmsg_safe(stream, resp)
        await stream.close()
        raise_if_failed(resp)

        topics = tuple(resp.pubsub.topics)
        return topics

    async def list_peers(self, topic: str) -> Tuple[ID, ...]:
        """PUBSUB LIST_PEERS
        """
        pubsub_req = p2pd_pb.PSRequest(type=p2pd_pb.PSRequest.LIST_PEERS, topic=topic)
        req = p2pd_pb.Request(type=p2pd_pb.Request.PUBSUB, pubsub=pubsub_req)
        stream = await self.daemon_connector.open_connection()
        await write_pbmsg(stream, req)
        resp = p2pd_pb.Response()
        await read_pbmsg_safe(stream, resp)
        await stream.close()
        raise_if_failed(resp)

        return tuple(ID(peer_id_bytes) for peer_id_bytes in resp.pubsub.peerIDs)

    async def publish(self, topic: str, data: bytes) -> None:
        """PUBSUB PUBLISH
        """
        pubsub_req = p2pd_pb.PSRequest(
            type=p2pd_pb.PSRequest.PUBLISH, topic=topic, data=data
        )
        req = p2pd_pb.Request(type=p2pd_pb.Request.PUBSUB, pubsub=pubsub_req)
        stream = await self.daemon_connector.open_connection()
        await write_pbmsg(stream, req)
        resp = p2pd_pb.Response()
        await read_pbmsg_safe(stream, resp)
        await stream.close()
        raise_if_failed(resp)

    async def subscribe(self, topic: str) -> anyio.abc.SocketStream:
        """PUBSUB SUBSCRIBE
        """
        pubsub_req = p2pd_pb.PSRequest(type=p2pd_pb.PSRequest.SUBSCRIBE, topic=topic)
        req = p2pd_pb.Request(type=p2pd_pb.Request.PUBSUB, pubsub=pubsub_req)
        stream = await self.daemon_connector.open_connection()
        await write_pbmsg(stream, req)
        resp = p2pd_pb.Response()
        await read_pbmsg_safe(stream, resp)
        raise_if_failed(resp)

        return stream
