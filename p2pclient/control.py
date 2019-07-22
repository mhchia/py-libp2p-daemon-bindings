import asyncio
import logging
from typing import Awaitable, Callable, Dict, Iterable, Sequence, Tuple

from multiaddr import Multiaddr, protocols

from . import config

from .datastructures import PeerID, PeerInfo, StreamInfo
from .exceptions import ControlFailure, DispatchFailure
from .utils import raise_if_failed, read_pbmsg_safe, write_pbmsg

from .pb import p2pd_pb2 as p2pd_pb


StreamHandler = Callable[
    [StreamInfo, asyncio.StreamReader, asyncio.StreamWriter], Awaitable[None]
]


_supported_conn_protocols = (
    protocols.P_IP4,
    # protocols.P_IP6,
    protocols.P_UNIX,
)


def parse_conn_protocol(maddr: Multiaddr) -> int:
    proto_codes = set(proto.code for proto in maddr.protocols())
    proto_cand = proto_codes.intersection(_supported_conn_protocols)
    if len(proto_cand) != 1:
        supported_protos = (
            protocols.protocol_with_code(proto) for proto in _supported_conn_protocols
        )
        raise ValueError(
            f"connection protocol should be only one protocol out of {supported_protos}"
            ", maddr={maddr}"
        )
    return tuple(proto_cand)[0]


class DaemonConnector:
    control_maddr: Multiaddr
    logger = logging.getLogger("p2pclient.DaemonConnector")

    def __init__(self, control_maddr: Multiaddr = None) -> None:
        if control_maddr is None:
            control_maddr = Multiaddr(config.control_maddr_str)
        self.control_maddr = control_maddr

    async def open_connection(
        self
    ) -> Tuple[asyncio.StreamReader, asyncio.StreamWriter]:
        proto_code = parse_conn_protocol(self.control_maddr)
        if proto_code == protocols.P_UNIX:
            control_path = self.control_maddr.value_for_protocol(protocols.P_UNIX)
            self.logger.debug(
                "DaemonConnector %s opens connection to %s", self, self.control_maddr
            )
            return await asyncio.open_unix_connection(control_path)
        elif proto_code == protocols.P_IP4:
            host = self.control_maddr.value_for_protocol(protocols.P_IP4)
            port = int(self.control_maddr.value_for_protocol(protocols.P_TCP))
            return await asyncio.open_connection(host=host, port=port)
        else:
            raise ValueError(
                f"protocol not supported: protocol={protocols.protocol_with_code(proto_code)}"
            )


class ControlClient:
    listen_maddr: Multiaddr
    daemon_connector: DaemonConnector
    handlers: Dict[str, StreamHandler]
    listener: asyncio.AbstractServer = None
    logger = logging.getLogger("p2pclient.ControlClient")

    def __init__(
        self, daemon_connector: DaemonConnector, listen_maddr: Multiaddr = None
    ) -> None:
        if listen_maddr is None:
            listen_maddr = Multiaddr(config.listen_maddr_str)
        self.listen_maddr = listen_maddr
        self.daemon_connector = daemon_connector
        self.handlers = {}

    async def _dispatcher(
        self, reader: asyncio.StreamReader, writer: asyncio.StreamWriter
    ) -> None:
        pb_stream_info = p2pd_pb.StreamInfo()
        await read_pbmsg_safe(reader, pb_stream_info)
        stream_info = StreamInfo.from_pb(pb_stream_info)
        self.logger.info("New incoming stream: %s", stream_info)
        try:
            handler = self.handlers[stream_info.proto]
        except KeyError as e:
            # should never enter here... daemon should reject the stream for us.
            writer.close()
            raise DispatchFailure(e)
        await handler(stream_info, reader, writer)

    async def listen(self) -> None:
        if self.listener is not None:
            raise ControlFailure("Listener is already listening")
        proto_code = parse_conn_protocol(self.listen_maddr)
        if proto_code == protocols.P_UNIX:
            listen_path = self.listen_maddr.value_for_protocol(protocols.P_UNIX)
            self.listener = await asyncio.start_unix_server(
                self._dispatcher, listen_path
            )
        elif proto_code == protocols.P_IP4:
            host = self.listen_maddr.value_for_protocol(protocols.P_IP4)
            port = int(self.listen_maddr.value_for_protocol(protocols.P_TCP))
            self.listener = await asyncio.start_server(
                self._dispatcher, host=host, port=port
            )
        else:
            raise ValueError(
                f"protocol not supported: protocol={protocols.protocol_with_code(proto_code)}"
            )
        self.logger.info(
            "DaemonConnector %s starts listening to %s", self, self.listen_maddr
        )

    async def close(self) -> None:
        self.listener.close()
        await self.listener.wait_closed()
        self.listener = None
        self.logger.info("DaemonConnector %s closed", self)

    async def identify(self) -> Tuple[PeerID, Tuple[Multiaddr, ...]]:
        reader, writer = await self.daemon_connector.open_connection()
        req = p2pd_pb.Request(type=p2pd_pb.Request.IDENTIFY)
        await write_pbmsg(writer, req)

        resp = p2pd_pb.Response()
        await read_pbmsg_safe(reader, resp)
        writer.close()
        raise_if_failed(resp)
        peer_id_bytes = resp.identify.id
        maddrs_bytes = resp.identify.addrs

        maddrs = tuple(Multiaddr(maddr_bytes) for maddr_bytes in maddrs_bytes)
        peer_id = PeerID(peer_id_bytes)

        return peer_id, maddrs

    async def connect(self, peer_id: PeerID, maddrs: Iterable[Multiaddr]) -> None:
        reader, writer = await self.daemon_connector.open_connection()

        maddrs_bytes = [i.to_bytes() for i in maddrs]
        connect_req = p2pd_pb.ConnectRequest(
            peer=peer_id.to_bytes(), addrs=maddrs_bytes
        )
        req = p2pd_pb.Request(type=p2pd_pb.Request.CONNECT, connect=connect_req)
        await write_pbmsg(writer, req)

        resp = p2pd_pb.Response()
        await read_pbmsg_safe(reader, resp)
        writer.close()
        raise_if_failed(resp)

    async def list_peers(self) -> Tuple[PeerInfo, ...]:
        req = p2pd_pb.Request(type=p2pd_pb.Request.LIST_PEERS)
        reader, writer = await self.daemon_connector.open_connection()
        await write_pbmsg(writer, req)
        resp = p2pd_pb.Response()
        await read_pbmsg_safe(reader, resp)
        writer.close()
        raise_if_failed(resp)

        peers = tuple(PeerInfo.from_pb(pinfo) for pinfo in resp.peers)
        return peers

    async def disconnect(self, peer_id: PeerID) -> None:
        disconnect_req = p2pd_pb.DisconnectRequest(peer=peer_id.to_bytes())
        req = p2pd_pb.Request(
            type=p2pd_pb.Request.DISCONNECT, disconnect=disconnect_req
        )
        reader, writer = await self.daemon_connector.open_connection()
        await write_pbmsg(writer, req)
        resp = p2pd_pb.Response()
        await read_pbmsg_safe(reader, resp)
        writer.close()
        raise_if_failed(resp)

    async def stream_open(
        self, peer_id: PeerID, protocols: Sequence[str]
    ) -> Tuple[StreamInfo, asyncio.StreamReader, asyncio.StreamWriter]:
        reader, writer = await self.daemon_connector.open_connection()

        stream_open_req = p2pd_pb.StreamOpenRequest(
            peer=peer_id.to_bytes(), proto=list(protocols)
        )
        req = p2pd_pb.Request(
            type=p2pd_pb.Request.STREAM_OPEN, streamOpen=stream_open_req
        )
        await write_pbmsg(writer, req)

        resp = p2pd_pb.Response()
        await read_pbmsg_safe(reader, resp)
        raise_if_failed(resp)

        pb_stream_info = resp.streamInfo
        stream_info = StreamInfo.from_pb(pb_stream_info)

        return stream_info, reader, writer

    async def stream_handler(self, proto: str, handler_cb: StreamHandler) -> None:
        reader, writer = await self.daemon_connector.open_connection()

        listen_path_maddr_bytes = self.listen_maddr.to_bytes()
        stream_handler_req = p2pd_pb.StreamHandlerRequest(
            addr=listen_path_maddr_bytes, proto=[proto]
        )
        req = p2pd_pb.Request(
            type=p2pd_pb.Request.STREAM_HANDLER, streamHandler=stream_handler_req
        )
        await write_pbmsg(writer, req)

        resp = p2pd_pb.Response()
        await read_pbmsg_safe(reader, resp)
        writer.close()
        raise_if_failed(resp)

        # if success, add the handler to the dict
        self.handlers[proto] = handler_cb
