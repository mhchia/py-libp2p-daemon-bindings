from typing import AsyncIterator, Iterable, Sequence, Tuple

import anyio
from async_generator import asynccontextmanager
from p2pclient.libp2p_stubs.crypto.pb import crypto_pb2 as crypto_pb
from p2pclient.libp2p_stubs.peer.id import ID
from multiaddr import Multiaddr

from .connmgr import ConnectionManagerClient
from .control import ControlClient, DaemonConnector, StreamHandler
from .datastructures import PeerInfo, StreamInfo
from .dht import DHTClient
from .pubsub import PubSubClient


class Client:
    control: ControlClient
    connmgr: ConnectionManagerClient
    dht: DHTClient
    pubsub: PubSubClient

    def __init__(
        self, control_maddr: Multiaddr = None, listen_maddr: Multiaddr = None
    ) -> None:
        daemon_connector = DaemonConnector(control_maddr=control_maddr)
        self.control = ControlClient(
            daemon_connector=daemon_connector, listen_maddr=listen_maddr
        )
        self.connmgr = ConnectionManagerClient(daemon_connector=daemon_connector)
        self.dht = DHTClient(daemon_connector=daemon_connector)
        self.pubsub = PubSubClient(daemon_connector=daemon_connector)

    @asynccontextmanager
    async def listen(self) -> AsyncIterator["Client"]:
        async with self.control.listen():
            yield self

    async def close(self) -> None:
        await self.control.close()

    async def identify(self) -> Tuple[ID, Tuple[Multiaddr, ...]]:
        return await self.control.identify()

    async def connect(self, peer_id: ID, maddrs: Iterable[Multiaddr]) -> None:
        await self.control.connect(peer_id=peer_id, maddrs=maddrs)

    async def list_peers(self) -> Tuple[PeerInfo, ...]:
        return await self.control.list_peers()

    async def disconnect(self, peer_id: ID) -> None:
        await self.control.disconnect(peer_id=peer_id)

    async def stream_open(
        self, peer_id: ID, protocols: Sequence[str]
    ) -> Tuple[StreamInfo, anyio.abc.SocketStream]:
        return await self.control.stream_open(peer_id=peer_id, protocols=protocols)

    async def stream_handler(self, proto: str, handler_cb: StreamHandler) -> None:
        await self.control.stream_handler(proto=proto, handler_cb=handler_cb)

    async def connmgr_tag_peer(self, peer_id: ID, tag: str, weight: int) -> None:
        await self.connmgr.tag_peer(peer_id=peer_id, tag=tag, weight=weight)

    async def connmgr_untag_peer(self, peer_id: ID, tag: str) -> None:
        await self.connmgr.untag_peer(peer_id=peer_id, tag=tag)

    async def connmgr_trim(self) -> None:
        await self.connmgr.trim()

    async def dht_find_peer(self, peer_id: ID) -> PeerInfo:
        return await self.dht.find_peer(peer_id=peer_id)

    async def dht_find_peers_connected_to_peer(
        self, peer_id: ID
    ) -> Tuple[PeerInfo, ...]:
        return await self.dht.find_peers_connected_to_peer(peer_id=peer_id)

    async def dht_find_providers(
        self, content_id_bytes: bytes, count: int
    ) -> Tuple[PeerInfo, ...]:
        return await self.dht.find_providers(
            content_id_bytes=content_id_bytes, count=count
        )

    async def dht_get_closest_peers(self, key: bytes) -> Tuple[ID, ...]:
        return await self.dht.get_closest_peers(key=key)

    async def dht_get_public_key(self, peer_id: ID) -> crypto_pb.PublicKey:
        return await self.dht.get_public_key(peer_id=peer_id)

    async def dht_get_value(self, key: bytes) -> bytes:
        return await self.dht.get_value(key=key)

    async def dht_search_value(self, key: bytes) -> Tuple[bytes, ...]:
        return await self.dht.search_value(key=key)

    async def dht_put_value(self, key: bytes, value: bytes) -> None:
        await self.dht.put_value(key=key, value=value)

    async def dht_provide(self, cid: bytes) -> None:
        await self.dht.provide(cid=cid)

    async def pubsub_get_topics(self) -> Tuple[str, ...]:
        return await self.pubsub.get_topics()

    async def pubsub_list_peers(self, topic: str) -> Tuple[ID, ...]:
        return await self.pubsub.list_peers(topic=topic)

    async def pubsub_publish(self, topic: str, data: bytes) -> None:
        return await self.pubsub.publish(topic=topic, data=data)

    async def pubsub_subscribe(self, topic: str) -> anyio.abc.SocketStream:
        return await self.pubsub.subscribe(topic=topic)
