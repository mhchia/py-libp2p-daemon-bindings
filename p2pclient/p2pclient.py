import asyncio
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
        # TODO: handlers
        self.handlers = {}

    async def _dispatcher(self, reader, writer):
        pb_stream_info = pb.StreamInfo()
        await read_pbmsg_safe(reader, pb_stream_info)
        stream_info = StreamInfo.from_pb(pb_stream_info)
        self.logger.info("New incoming stream: %s", stream_info)
        handler = self.handlers[stream_info.proto]
        await handler(stream_info, reader, writer)

    async def listen(self):
        self.listener = await asyncio.start_unix_server(self._dispatcher, self.listen_path)

    async def identify(self):
        reader, writer = await asyncio.open_unix_connection(self.control_path)
        req = pb.Request(type=pb.Request.IDENTIFY)
        data_bytes = serialize(req)
        writer.write(data_bytes)

        resp = pb.Response()
        await read_pbmsg_safe(reader, resp)
        raise_if_failed(resp)
        peer_id_bytes = resp.identify.id
        maddrs_bytes = resp.identify.addrs

        maddrs = []
        for maddr_bytes in maddrs_bytes:
            # addr is
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
        data_bytes = serialize(req)
        writer.write(data_bytes)

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
        data_bytes = serialize(req)
        writer.write(data_bytes)

        resp = pb.Response()
        await read_pbmsg_safe(reader, resp)
        raise_if_failed(resp)

        pb_stream_info = resp.streamInfo
        stream_info = StreamInfo.from_pb(pb_stream_info)

        return stream_info, reader, writer

    async def stream_handler(self, proto, handler_cb):
        reader, writer = await asyncio.open_unix_connection(self.control_path)

        stream_handler_req = pb.StreamHandlerRequest(
            path=self.listen_path,
            proto=[proto],
        )
        req = pb.Request(
            type=pb.Request.STREAM_HANDLER,
            streamHandler=stream_handler_req,
        )
        data_bytes = serialize(req)
        writer.write(data_bytes)

        resp = pb.Response()
        await read_pbmsg_safe(reader, resp)
        raise_if_failed(resp)

        # if success, add the handler to the dict
        self.handlers[proto] = handler_cb

    async def read_dht_response_stream(self, reader):
        pass

    async def find_peer(self, peer_id):
        reader, writer = await asyncio.open_unix_connection(self.control_path)
        dht_req = pb.DHTRequest(
            type=pb.DHTRequest.FIND_PEER,
            peer=peer_id.to_bytes(),
        )
        req = pb.Request(
            type=pb.Request.DHT,
            dht=dht_req,
        )
        data_bytes = serialize(req)
        writer.write(data_bytes)

        resp = pb.Response()
        await read_pbmsg_safe(reader, resp)
        raise_if_failed(resp)

        dht_resp = resp.dht
        if dht_resp.type != dht_resp.VALUE:
            raise ValueError("Type should be VALUE instead of f{dht_resp.type}")
        pinfo = PeerInfo.from_pb(dht_resp.peer)
        return pinfo
