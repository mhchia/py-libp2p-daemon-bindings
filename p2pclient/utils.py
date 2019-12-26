import anyio
from google.protobuf.message import Message as PBMessage

from .exceptions import ControlFailure
from .pb import p2pd_pb2 as p2pd_pb
from .serialization import read_unsigned_varint, write_unsigned_varint


def raise_if_failed(response: p2pd_pb.Response) -> None:
    if response.type == p2pd_pb.Response.ERROR:
        raise ControlFailure(f"connect failed. msg={response.error.msg}")


async def write_pbmsg(stream: anyio.abc.Stream, pbmsg: PBMessage) -> None:
    size = pbmsg.ByteSize()
    await write_unsigned_varint(stream, size)
    msg_bytes: bytes = pbmsg.SerializeToString()
    await stream.send_all(msg_bytes)


async def read_pbmsg_safe(stream: anyio.abc.Stream, pbmsg: PBMessage) -> None:
    len_msg_bytes = await read_unsigned_varint(stream)
    msg_bytes = await stream.receive_exactly(len_msg_bytes)
    pbmsg.ParseFromString(msg_bytes)
