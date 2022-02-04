from typing import AsyncGenerator, Tuple

import anyio
from p2pclient.libp2p_stubs.crypto.pb import crypto_pb2 as crypto_pb
from p2pclient.libp2p_stubs.peer.id import ID

from .control import DaemonConnector
from .datastructures import PeerInfo
from .exceptions import ControlFailure
from .pb import p2pd_pb2 as p2pd_pb
from .utils import raise_if_failed, read_pbmsg_safe, write_pbmsg


class DHTClient:
    daemon_connector: DaemonConnector

    def __init__(self, daemon_connector: DaemonConnector) -> None:
        self.daemon_connector = daemon_connector

    @staticmethod
    async def _read_dht_stream(
        stream: anyio.abc.SocketStream,
    ) -> AsyncGenerator[p2pd_pb.DHTResponse, None]:
        while True:
            dht_resp = p2pd_pb.DHTResponse()
            await read_pbmsg_safe(stream, dht_resp)
            if dht_resp.type == dht_resp.END:
                break
            yield dht_resp

    async def _do_dht(
        self, dht_req: p2pd_pb.DHTRequest
    ) -> Tuple[p2pd_pb.DHTResponse, ...]:
        stream = await self.daemon_connector.open_connection()
        req = p2pd_pb.Request(type=p2pd_pb.Request.DHT, dht=dht_req)
        await write_pbmsg(stream, req)
        resp = p2pd_pb.Response()
        await read_pbmsg_safe(stream, resp)
        raise_if_failed(resp)

        try:
            dht_resp = resp.dht
        except AttributeError as e:
            raise ControlFailure(f"resp should contains dht: resp={resp}, e={e}")

        if dht_resp.type == dht_resp.VALUE:
            return (dht_resp,)

        if dht_resp.type != dht_resp.BEGIN:
            raise ControlFailure(f"Type should be BEGIN instead of {dht_resp.type}")
        # BEGIN/END stream
        resps = tuple([i async for i in self._read_dht_stream(stream)])
        await stream.close()
        return resps

    async def find_peer(self, peer_id: ID) -> PeerInfo:
        """FIND_PEER
        """
        dht_req = p2pd_pb.DHTRequest(
            type=p2pd_pb.DHTRequest.FIND_PEER, peer=peer_id.to_bytes()
        )
        resps = await self._do_dht(dht_req)
        if len(resps) != 1:
            raise ControlFailure(
                f"should only get one response from `find_peer`, resps={resps}"
            )
        dht_resp = resps[0]
        try:
            pinfo = dht_resp.peer
        except AttributeError as e:
            raise ControlFailure(
                f"dht_resp should contains peer info: dht_resp={dht_resp}, e={e}"
            )
        return PeerInfo.from_pb(pinfo)  # type: ignore

    async def find_peers_connected_to_peer(self, peer_id: ID) -> Tuple[PeerInfo, ...]:
        """FIND_PEERS_CONNECTED_TO_PEER
        """
        dht_req = p2pd_pb.DHTRequest(
            type=p2pd_pb.DHTRequest.FIND_PEERS_CONNECTED_TO_PEER,
            peer=peer_id.to_bytes(),
        )
        resps = await self._do_dht(dht_req)
        try:
            pinfos = tuple(PeerInfo.from_pb(dht_resp.peer) for dht_resp in resps)
        except AttributeError as e:
            raise ControlFailure(
                f"dht_resp should contains peer info: resps={resps}, e={e}"
            )
        return pinfos   # type: ignore

    async def find_providers(
        self, content_id_bytes: bytes, count: int
    ) -> Tuple[PeerInfo, ...]:
        """FIND_PROVIDERS
        """
        # TODO: should have another class ContendID
        dht_req = p2pd_pb.DHTRequest(
            type=p2pd_pb.DHTRequest.FIND_PROVIDERS, cid=content_id_bytes, count=count
        )
        resps = await self._do_dht(dht_req)
        try:
            pinfos = tuple(PeerInfo.from_pb(dht_resp.peer) for dht_resp in resps)
        except AttributeError as e:
            raise ControlFailure(
                f"dht_resp should contains peer info: resps={resps}, e={e}"
            )
        return pinfos   # type: ignore

    async def get_closest_peers(self, key: bytes) -> Tuple[ID, ...]:
        """GET_CLOSEST_PEERS
        """
        dht_req = p2pd_pb.DHTRequest(type=p2pd_pb.DHTRequest.GET_CLOSEST_PEERS, key=key)
        resps = await self._do_dht(dht_req)
        try:
            peer_ids = tuple(ID(dht_resp.value) for dht_resp in resps)
        except AttributeError as e:
            raise ControlFailure(
                f"dht_resp should contains `value`: resps={resps}, e={e}"
            )
        return peer_ids

    async def get_public_key(self, peer_id: ID) -> crypto_pb.PublicKey:
        """GET_PUBLIC_KEY
        """
        dht_req = p2pd_pb.DHTRequest(
            type=p2pd_pb.DHTRequest.GET_PUBLIC_KEY, peer=peer_id.to_bytes()
        )
        resps = await self._do_dht(dht_req)
        if len(resps) != 1:
            raise ControlFailure(f"should only get one response, resps={resps}")
        try:
            public_key_pb_bytes = resps[0].value
        except AttributeError as e:
            raise ControlFailure(
                f"dht_resp should contains `value`: resps={resps}, e={e}"
            )
        public_key_pb = crypto_pb.PublicKey()
        public_key_pb.ParseFromString(public_key_pb_bytes)
        return public_key_pb

    async def get_value(self, key: bytes) -> bytes:
        """GET_VALUE
        """
        dht_req = p2pd_pb.DHTRequest(type=p2pd_pb.DHTRequest.GET_VALUE, key=key)
        resps = await self._do_dht(dht_req)
        if len(resps) != 1:
            raise ControlFailure(f"should only get one response, resps={resps}")
        try:
            value = resps[0].value
        except AttributeError as e:
            raise ControlFailure(
                f"dht_resp should contains `value`: resps={resps}, e={e}"
            )
        return value

    async def search_value(self, key: bytes) -> Tuple[bytes, ...]:
        """SEARCH_VALUE
        """
        dht_req = p2pd_pb.DHTRequest(type=p2pd_pb.DHTRequest.SEARCH_VALUE, key=key)
        resps = await self._do_dht(dht_req)
        try:
            values = tuple(resp.value for resp in resps)
        except AttributeError as e:
            raise ControlFailure(
                f"dht_resp should contains `value`: resps={resps}, e={e}"
            )
        return values

    async def put_value(self, key: bytes, value: bytes) -> None:
        """PUT_VALUE
        """
        dht_req = p2pd_pb.DHTRequest(
            type=p2pd_pb.DHTRequest.PUT_VALUE, key=key, value=value
        )
        req = p2pd_pb.Request(type=p2pd_pb.Request.DHT, dht=dht_req)
        stream = await self.daemon_connector.open_connection()
        await write_pbmsg(stream, req)
        resp = p2pd_pb.Response()
        await read_pbmsg_safe(stream, resp)
        await stream.close()
        raise_if_failed(resp)

    async def provide(self, cid: bytes) -> None:
        """PROVIDE
        """
        dht_req = p2pd_pb.DHTRequest(type=p2pd_pb.DHTRequest.PROVIDE, cid=cid)
        req = p2pd_pb.Request(type=p2pd_pb.Request.DHT, dht=dht_req)
        stream = await self.daemon_connector.open_connection()
        await write_pbmsg(stream, req)
        resp = p2pd_pb.Response()
        await read_pbmsg_safe(stream, resp)
        await stream.close()
        raise_if_failed(resp)
