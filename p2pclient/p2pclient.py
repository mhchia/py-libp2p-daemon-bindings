import asyncio
import inspect
import logging

from p2pclient.datastructures import (
    Multiaddr,
    PeerID,
    PeerInfo,
    StreamInfo,
)
from p2pclient.serialization import (
    read_pbmsg_safe,
    serialize,
)

import p2pclient.pb.p2pd_pb2 as pb


class ControlFailure(Exception):
    pass


class DispatchFailure(Exception):
    pass


def raise_if_failed(response):
    if response.type == pb.Response.ERROR:
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
        pb_stream_info = pb.StreamInfo()
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
        req = pb.Request(type=pb.Request.IDENTIFY)
        await self._write_pb(writer, req)

        resp = pb.Response()
        await read_pbmsg_safe(reader, resp)
        raise_if_failed(resp)
        peer_id_bytes = resp.identify.id
        maddrs_bytes = resp.identify.addrs

        maddrs = []
        for maddr_bytes in maddrs_bytes:
            # maddr_str = str(maddr)[2:-1]
            # maddr_bytes_m = bytes.fromhex(maddr_str)
            maddr = Multiaddr(bytes_addr=maddr_bytes)
            assert maddr.to_bytes() == maddr_bytes
            maddrs.append(maddr)
        peer_id = PeerID(peer_id_bytes)

        return peer_id, maddrs

    async def connect(self, peer_id, maddrs):
        reader, writer = await asyncio.open_unix_connection(self.control_path)

        maddrs_bytes = [i.to_bytes() for i in maddrs]
        connect_req = pb.ConnectRequest(
            peer=peer_id.to_bytes(),
            addrs=maddrs_bytes,
        )
        req = pb.Request(
            type=pb.Request.CONNECT,
            connect=connect_req,
        )
        await self._write_pb(writer, req)

        resp = pb.Response()
        await read_pbmsg_safe(reader, resp)
        raise_if_failed(resp)

    async def stream_open(self, peer_id, protocols):
        reader, writer = await asyncio.open_unix_connection(self.control_path)

        stream_open_req = pb.StreamOpenRequest(
            peer=peer_id.to_bytes(),
            proto=protocols,
        )
        req = pb.Request(
            type=pb.Request.STREAM_OPEN,
            streamOpen=stream_open_req,
        )
        await self._write_pb(writer, req)

        resp = pb.Response()
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

        stream_handler_req = pb.StreamHandlerRequest(
            path=self.listen_path,
            proto=[proto],
        )
        req = pb.Request(
            type=pb.Request.STREAM_HANDLER,
            streamHandler=stream_handler_req,
        )
        await self._write_pb(writer, req)

        resp = pb.Response()
        await read_pbmsg_safe(reader, resp)
        raise_if_failed(resp)

        # if success, add the handler to the dict
        self.handlers[proto] = handler_cb

    async def _do_dht(self, dht_req):
        reader, writer = await asyncio.open_unix_connection(self.control_path)
        req = pb.Request(
            type=pb.Request.DHT,
            dht=dht_req,
        )
        await self._write_pb(writer, req)
        resp = pb.Response()
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
            dht_resp = pb.DHTResponse()
            await read_pbmsg_safe(reader, dht_resp)
            if dht_resp.type == dht_resp.END:
                break
            resps.append(dht_resp)
        return resps

    async def find_peer(self, peer_id):
        """FIND_PEER
        """
        dht_req = pb.DHTRequest(
            type=pb.DHTRequest.FIND_PEER,
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
        dht_req = pb.DHTRequest(
            type=pb.DHTRequest.FIND_PEERS_CONNECTED_TO_PEER,
            peer=peer_id.to_bytes(),
        )
        resps = await self._do_dht(dht_req)

        # TODO: maybe change these checks to a validator pattern
        try:
            pinfos = [dht_resp.peer for dht_resp in resps]
        except AttributeError as e:
            raise ControlFailure(
                f"dht_resp should contains peer info: resps={resps}, e={e}"
            )
        return pinfos

    async def find_providers(self, content_id_bytes, count):
        """GET_CLOSEST_PEERS
        """
        # TODO: should have another class ContendID
        dht_req = pb.DHTRequest(
            type=pb.DHTRequest.FIND_PROVIDERS,
            cid=content_id_bytes,
            count=count,
        )
        resps = await self._do_dht(dht_req)
        # TODO: maybe change these checks to a validator pattern
        try:
            pinfos = [dht_resp.peer for dht_resp in resps]
        except AttributeError as e:
            raise ControlFailure(
                f"dht_resp should contains peer info: resps={resps}, e={e}"
            )
        return pinfos

    async def get_closest_peers(self, key):
        """GET_CLOSEST_PEERS
        """
        dht_req = pb.DHTRequest(
            type=pb.DHTRequest.GET_CLOSEST_PEERS,
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
        dht_req = pb.DHTRequest(
            type=pb.DHTRequest.GET_PUBLIC_KEY,
            peer=peer_id.to_bytes(),
        )
        resps = await self._do_dht(dht_req)
        if len(resps) != 1:
            raise ControlFailure(f"should only get one response, resps={resps}")
        try:
                # TODO: parse the public key with another class?
            public_key = resps[0].value
        except AttributeError as e:
            raise ControlFailure(
                f"dht_resp should contains `value`: resps={resps}, e={e}"
            )
        return public_key

    async def get_value(self, key):
        """GET_VALUE
        """
        dht_req = pb.DHTRequest(
            type=pb.DHTRequest.GET_VALUE,
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
        """GET_VALUE
        """
        dht_req = pb.DHTRequest(
            type=pb.DHTRequest.SEARCH_VALUE,
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
        dht_req = pb.DHTRequest(
            type=pb.DHTRequest.PUT_VALUE,
            key=key,
            value=value,
        )
        resps = await self._do_dht(dht_req)
        print(resps)
        # try:
        #     # TODO: parse the public key with another class?
        #     values = [resp.value for resp in resps]
        # except AttributeError as e:
        #     raise ControlFailure(
        #         f"dht_resp should contains `value`: resps={resps}, e={e}"
        #     )
        # return values
