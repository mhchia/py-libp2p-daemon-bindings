import asyncio

from google.protobuf.message import Message as PBMessage

from .exceptions import ControlFailure
from .pb import p2pd_pb2 as p2pd_pb
from .serialization import read_unsigned_varint, write_unsigned_varint


def raise_if_failed(response: p2pd_pb.Response) -> None:
    if response.type == p2pd_pb.Response.ERROR:
        raise ControlFailure(f"connect failed. msg={response.error.msg}")


async def write_pbmsg(writer: asyncio.StreamWriter, pbmsg: PBMessage) -> None:
    size = pbmsg.ByteSize()
    write_unsigned_varint(writer, size)
    msg_bytes: bytes = pbmsg.SerializeToString()
    writer.write(msg_bytes)
    await writer.drain()


async def read_pbmsg_safe(reader: asyncio.StreamReader, pbmsg: PBMessage) -> None:
    len_msg_bytes = await read_unsigned_varint(reader)
    msg_bytes = await reader.readexactly(len_msg_bytes)
    pbmsg.ParseFromString(msg_bytes)
