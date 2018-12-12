import asyncio
import binascii
import inspect
import logging

from multiaddr import (
    Multiaddr,
)

from .datastructures import (
    PeerID,
    PeerInfo,
    StreamInfo,
)
from .serialization import (
    read_pbmsg_safe,
    serialize,
)

from .pb import p2pd_pb2 as p2pd_pb
from .pb import crypto_pb2 as crypto_pb


class ControlFailure(Exception):
    pass


class DispatchFailure(Exception):
    pass


def raise_if_failed(response):
    if response.type == p2pd_pb.Response.ERROR:
        raise ControlFailure(
            "connect failed. msg={}".format(
                response.error.msg,
            )
        )


class Client:
    control_path = None
    listen_path = None
    listener = None

    mutex_handlers = None
    handlers = None

    logger = logging.getLogger('p2pclient.Client')

    def __init__(self, control_path, listen_path):
        self.control_path = control_path
        self.listen_path = listen_path
        self.handlers = {}

    async def _dispatcher(self, reader, writer):
        pb_stream_info = p2pd_pb.StreamInfo()
        await read_pbmsg_safe(reader, pb_stream_info)
        stream_info = StreamInfo.from_pb(pb_stream_info)
        self.logger.info("New incoming stream: %s", stream_info)
        try:
            handler = self.handlers[stream_info.proto]
        except KeyError as e:
            raise DispatchFailure(e)
        await handler(stream_info, reader, writer)

    async def _write_pb(self, writer, data_pb):
        data_bytes = serialize(data_pb)
        writer.write(data_bytes)
        await writer.drain()

    async def listen(self):
        self.listener = await asyncio.start_unix_server(self._dispatcher, self.listen_path)

    async def identify(self):
        reader, writer = await asyncio.open_unix_connection(self.control_path)
        req = p2pd_pb.Request(type=p2pd_pb.Request.IDENTIFY)
        await self._write_pb(writer, req)

        resp = p2pd_pb.Response()
        await read_pbmsg_safe(reader, resp)
        raise_if_failed(resp)
        peer_id_bytes = resp.identify.id
        maddrs_bytes = resp.identify.addrs

        maddrs = []
        for maddr_bytes in maddrs_bytes:
            maddr = Multiaddr(binascii.hexlify(maddr_bytes))
            maddrs.append(maddr)
        peer_id = PeerID(peer_id_bytes)

        return peer_id, maddrs

    async def connect(self, peer_id, maddrs):
        reader, writer = await asyncio.open_unix_connection(self.control_path)

        maddrs_bytes = [binascii.unhexlify(i.to_bytes()) for i in maddrs]
        connect_req = p2pd_pb.ConnectRequest(
            peer=peer_id.to_bytes(),
            addrs=maddrs_bytes,
        )
        req = p2pd_pb.Request(
            type=p2pd_pb.Request.CONNECT,
            connect=connect_req,
        )
        await self._write_pb(writer, req)

        resp = p2pd_pb.Response()
        await read_pbmsg_safe(reader, resp)
        raise_if_failed(resp)

    async def list_peers(self):
        req = p2pd_pb.Request(
            type=p2pd_pb.Request.LIST_PEERS,
        )
        reader, writer = await asyncio.open_unix_connection(self.control_path)
        await self._write_pb(writer, req)
        resp = p2pd_pb.Response()
        await read_pbmsg_safe(reader, resp)
        raise_if_failed(resp)

        pinfos = [PeerInfo.from_pb(pinfo) for pinfo in resp.peers]
        return pinfos

    async def disconnect(self, peer_id):
        disconnect_req = p2pd_pb.DisconnectRequest(
            peer=peer_id.to_bytes(),
        )
        req = p2pd_pb.Request(
            type=p2pd_pb.Request.DISCONNECT,
            disconnect=disconnect_req,
        )
        reader, writer = await asyncio.open_unix_connection(self.control_path)
        await self._write_pb(writer, req)
        resp = p2pd_pb.Response()
        await read_pbmsg_safe(reader, resp)
        raise_if_failed(resp)

    async def stream_open(self, peer_id, protocols):
        reader, writer = await asyncio.open_unix_connection(self.control_path)

        stream_open_req = p2pd_pb.StreamOpenRequest(
            peer=peer_id.to_bytes(),
            proto=protocols,
        )
        req = p2pd_pb.Request(
            type=p2pd_pb.Request.STREAM_OPEN,
            streamOpen=stream_open_req,
        )
        await self._write_pb(writer, req)

        resp = p2pd_pb.Response()
        await read_pbmsg_safe(reader, resp)
        raise_if_failed(resp)

        pb_stream_info = resp.streamInfo
        stream_info = StreamInfo.from_pb(pb_stream_info)

        return stream_info, reader, writer

    async def stream_handler(self, proto, handler_cb):
        reader, writer = await asyncio.open_unix_connection(self.control_path)

        # FIXME: should introduce type annotation to solve this elegantly
        handler_sig = inspect.signature(handler_cb).parameters
        if len(handler_sig) != 3:
            raise ControlFailure(
                "signature of the callback handler {} is wrong: {}".format(
                    handler_cb,
                    handler_sig,
                )
            )

        stream_handler_req = p2pd_pb.StreamHandlerRequest(
            path=self.listen_path,
            proto=[proto],
        )
        req = p2pd_pb.Request(
            type=p2pd_pb.Request.STREAM_HANDLER,
            streamHandler=stream_handler_req,
        )
        await self._write_pb(writer, req)

        resp = p2pd_pb.Response()
        await read_pbmsg_safe(reader, resp)
        raise_if_failed(resp)

        # if success, add the handler to the dict
        self.handlers[proto] = handler_cb

    # DHT operations

    async def _do_dht(self, dht_req):
        reader, writer = await asyncio.open_unix_connection(self.control_path)
        req = p2pd_pb.Request(
            type=p2pd_pb.Request.DHT,
            dht=dht_req,
        )
        await self._write_pb(writer, req)
        resp = p2pd_pb.Response()
        await read_pbmsg_safe(reader, resp)
        raise_if_failed(resp)

        try:
            dht_resp = resp.dht
        except AttributeError as e:
            raise ControlFailure(f"resp should contains dht: resp={resp}, e={e}")

        if dht_resp.type == dht_resp.VALUE:
            return [dht_resp]

        if dht_resp.type != dht_resp.BEGIN:
            raise ControlFailure(f"Type should be BEGIN instead of {dht_resp.type}")
        # BEGIN/END stream
        resps = []
        while True:
            dht_resp = p2pd_pb.DHTResponse()
            await read_pbmsg_safe(reader, dht_resp)
            if dht_resp.type == dht_resp.END:
                break
            resps.append(dht_resp)
        return resps

    async def find_peer(self, peer_id):
        """FIND_PEER
        """
        dht_req = p2pd_pb.DHTRequest(
            type=p2pd_pb.DHTRequest.FIND_PEER,
            peer=peer_id.to_bytes(),
        )
        resps = await self._do_dht(dht_req)
        if len(resps) != 1:
            raise ControlFailure(f"should only get one response from `find_peer`, resps={resps}")
        dht_resp = resps[0]
        try:
            pinfo = dht_resp.peer
        except AttributeError as e:
            raise ControlFailure(f"dht_resp should contains peer info: dht_resp={dht_resp}, e={e}")
        return PeerInfo.from_pb(pinfo)

    async def find_peers_connected_to_peer(self, peer_id):
        """FIND_PEERS_CONNECTED_TO_PEER
        """
        dht_req = p2pd_pb.DHTRequest(
            type=p2pd_pb.DHTRequest.FIND_PEERS_CONNECTED_TO_PEER,
            peer=peer_id.to_bytes(),
        )
        resps = await self._do_dht(dht_req)

        # TODO: maybe change these checks to a validator pattern
        try:
            pinfos = [PeerInfo.from_pb(dht_resp.peer) for dht_resp in resps]
        except AttributeError as e:
            raise ControlFailure(
                f"dht_resp should contains peer info: resps={resps}, e={e}"
            )
        return pinfos

    async def find_providers(self, content_id_bytes, count):
        """FIND_PROVIDERS
        """
        # TODO: should have another class ContendID
        dht_req = p2pd_pb.DHTRequest(
            type=p2pd_pb.DHTRequest.FIND_PROVIDERS,
            cid=content_id_bytes,
            count=count,
        )
        resps = await self._do_dht(dht_req)
        # TODO: maybe change these checks to a validator pattern
        try:
            pinfos = [PeerInfo.from_pb(dht_resp.peer) for dht_resp in resps]
        except AttributeError as e:
            raise ControlFailure(
                f"dht_resp should contains peer info: resps={resps}, e={e}"
            )
        return pinfos

    async def get_closest_peers(self, key):
        """GET_CLOSEST_PEERS
        """
        dht_req = p2pd_pb.DHTRequest(
            type=p2pd_pb.DHTRequest.GET_CLOSEST_PEERS,
            key=key,
        )
        resps = await self._do_dht(dht_req)
        try:
            peer_ids = [PeerID(dht_resp.value) for dht_resp in resps]
        except AttributeError as e:
            raise ControlFailure(
                f"dht_resp should contains `value`: resps={resps}, e={e}"
            )
        return peer_ids

    async def get_public_key(self, peer_id):
        """GET_PUBLIC_KEY
        """
        dht_req = p2pd_pb.DHTRequest(
            type=p2pd_pb.DHTRequest.GET_PUBLIC_KEY,
            peer=peer_id.to_bytes(),
        )
        resps = await self._do_dht(dht_req)
        if len(resps) != 1:
            raise ControlFailure(f"should only get one response, resps={resps}")
        try:
                # TODO: parse the public key with another class?
            public_key_pb_bytes = resps[0].value
        except AttributeError as e:
            raise ControlFailure(
                f"dht_resp should contains `value`: resps={resps}, e={e}"
            )
        public_key_pb = crypto_pb.PublicKey()
        public_key_pb.ParseFromString(public_key_pb_bytes)
        return public_key_pb

    async def get_value(self, key):
        """GET_VALUE
        """
        dht_req = p2pd_pb.DHTRequest(
            type=p2pd_pb.DHTRequest.GET_VALUE,
            key=key,
        )
        resps = await self._do_dht(dht_req)
        if len(resps) != 1:
            raise ControlFailure(f"should only get one response, resps={resps}")
        try:
                # TODO: parse the public key with another class?
            value = resps[0].value
        except AttributeError as e:
            raise ControlFailure(
                f"dht_resp should contains `value`: resps={resps}, e={e}"
            )
        return value

    async def search_value(self, key):
        """SEARCH_VALUE
        """
        dht_req = p2pd_pb.DHTRequest(
            type=p2pd_pb.DHTRequest.SEARCH_VALUE,
            key=key,
        )
        resps = await self._do_dht(dht_req)
        try:
            # TODO: parse the public key with another class?
            values = [resp.value for resp in resps]
        except AttributeError as e:
            raise ControlFailure(
                f"dht_resp should contains `value`: resps={resps}, e={e}"
            )
        return values

    async def put_value(self, key, value):
        """PUT_VALUE
        """
        dht_req = p2pd_pb.DHTRequest(
            type=p2pd_pb.DHTRequest.PUT_VALUE,
            key=key,
            value=value,
        )
        req = p2pd_pb.Request(
            type=p2pd_pb.Request.DHT,
            dht=dht_req,
        )
        reader, writer = await asyncio.open_unix_connection(self.control_path)
        await self._write_pb(writer, req)
        resp = p2pd_pb.Response()
        await read_pbmsg_safe(reader, resp)
        raise_if_failed(resp)

    async def provide(self, cid):
        """PROVIDE
        """
        dht_req = p2pd_pb.DHTRequest(
            type=p2pd_pb.DHTRequest.PROVIDE,
            cid=cid,
        )
        req = p2pd_pb.Request(
            type=p2pd_pb.Request.DHT,
            dht=dht_req,
        )
        reader, writer = await asyncio.open_unix_connection(self.control_path)
        await self._write_pb(writer, req)
        resp = p2pd_pb.Response()
        await read_pbmsg_safe(reader, resp)
        raise_if_failed(resp)

    # connection manager

    async def tag_peer(self, peer_id, tag, weight):
        """TAG_PEER
        """
        connmgr_req = p2pd_pb.ConnManagerRequest(
            type=p2pd_pb.ConnManagerRequest.TAG_PEER,
            peer=peer_id.to_bytes(),
            tag=tag,
            weight=weight,
        )
        req = p2pd_pb.Request(
            type=p2pd_pb.Request.CONNMANAGER,
            connManager=connmgr_req,
        )
        reader, writer = await asyncio.open_unix_connection(self.control_path)
        await self._write_pb(writer, req)
        resp = p2pd_pb.Response()
        await read_pbmsg_safe(reader, resp)
        raise_if_failed(resp)

    async def untag_peer(self, peer_id, tag):
        """UNTAG_PEER
        """
        connmgr_req = p2pd_pb.ConnManagerRequest(
            type=p2pd_pb.ConnManagerRequest.UNTAG_PEER,
            peer=peer_id.to_bytes(),
            tag=tag,
        )
        req = p2pd_pb.Request(
            type=p2pd_pb.Request.CONNMANAGER,
            connManager=connmgr_req,
        )
        reader, writer = await asyncio.open_unix_connection(self.control_path)
        await self._write_pb(writer, req)
        resp = p2pd_pb.Response()
        await read_pbmsg_safe(reader, resp)
        raise_if_failed(resp)

    async def trim(self):
        """TRIM
        """
        connmgr_req = p2pd_pb.ConnManagerRequest(
            type=p2pd_pb.ConnManagerRequest.TRIM,
        )
        req = p2pd_pb.Request(
            type=p2pd_pb.Request.CONNMANAGER,
            connManager=connmgr_req,
        )
        reader, writer = await asyncio.open_unix_connection(self.control_path)
        await self._write_pb(writer, req)
        resp = p2pd_pb.Response()
        await read_pbmsg_safe(reader, resp)
        raise_if_failed(resp)

    # PubSub

    async def get_topics(self):
        """PUBSUB GET_TOPICS
        """
        pubsub_req = p2pd_pb.PSRequest(
            type=p2pd_pb.PSRequest.GET_TOPICS,
        )
        req = p2pd_pb.Request(
            type=p2pd_pb.Request.PUBSUB,
            pubsub=pubsub_req,
        )
        reader, writer = await asyncio.open_unix_connection(self.control_path)
        await self._write_pb(writer, req)
        resp = p2pd_pb.Response()
        await read_pbmsg_safe(reader, resp)
        raise_if_failed(resp)

        return resp.pubsub.topics

    # FIXME: name conflicts: `list_topic_peers` is originally `list_peers` in pubsub
    async def list_topic_peers(self, topic):
        """PUBSUB LIST_PEERS
        """
        pubsub_req = p2pd_pb.PSRequest(
            type=p2pd_pb.PSRequest.LIST_PEERS,
            topic=topic,
        )
        req = p2pd_pb.Request(
            type=p2pd_pb.Request.PUBSUB,
            pubsub=pubsub_req,
        )
        reader, writer = await asyncio.open_unix_connection(self.control_path)
        await self._write_pb(writer, req)
        resp = p2pd_pb.Response()
        await read_pbmsg_safe(reader, resp)
        raise_if_failed(resp)

        peers = [PeerID(peer_id_bytes) for peer_id_bytes in resp.pubsub.peerIDs]
        return peers

    async def publish(self, topic, data):
        """PUBSUB PUBLISH
        """
        pubsub_req = p2pd_pb.PSRequest(
            type=p2pd_pb.PSRequest.PUBLISH,
            topic=topic,
            data=data,
        )
        req = p2pd_pb.Request(
            type=p2pd_pb.Request.PUBSUB,
            pubsub=pubsub_req,
        )
        reader, writer = await asyncio.open_unix_connection(self.control_path)
        await self._write_pb(writer, req)
        resp = p2pd_pb.Response()
        await read_pbmsg_safe(reader, resp)
        raise_if_failed(resp)

    async def subscribe(self, topic):
        """PUBSUB SUBSCRIBE
        """
        pubsub_req = p2pd_pb.PSRequest(
            type=p2pd_pb.PSRequest.SUBSCRIBE,
            topic=topic,
        )
        req = p2pd_pb.Request(
            type=p2pd_pb.Request.PUBSUB,
            pubsub=pubsub_req,
        )
        reader, writer = await asyncio.open_unix_connection(self.control_path)
        await self._write_pb(writer, req)
        resp = p2pd_pb.Response()
        await read_pbmsg_safe(reader, resp)
        raise_if_failed(resp)

        return reader, writer
