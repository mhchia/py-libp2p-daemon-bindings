from google.protobuf.internal.decoder import (
    _DecodeVarint,
)
from google.protobuf.internal.encoder import (
    _EncodeVarint,
    _VarintBytes,
)

from p2pd.constants import (
    BUFFER_SIZE,
)


def serialize(pb_msg):
    size = pb_msg.ByteSize()
    # FIXME: change to another implementation which is also compatible with binary.Uvarint?
    size_prefix = _VarintBytes(size)
    return size_prefix + pb_msg.SerializeToString()


def deserialize(entire_bytes, msg):
    # FIXME: change to another implementation which is also compatible with binary.Uvarint?
    msg_len, new_pos = _DecodeVarint(entire_bytes, 0)
    msg_bytes = entire_bytes[new_pos:(new_pos + msg_len)]
    msg.ParseFromString(msg_bytes)
    return msg


def write_varint(s, value):
    _EncodeVarint(s.write, value, True)


async def read_byte(s):
    data = await s.readexactly(1)
    return data[0]


async def read_varint(s, read_byte):
    iteration = 0
    chunk_bits = 7
    result = 0
    has_next = True
    while has_next:
        c = await read_byte(s)
        value = (c & 0x7f)
        result |= (value << (iteration * chunk_bits))
        has_next = (c & 0x80)
        iteration += 1
        # valid `iteration` should be <= 10.
        # if `iteration` == 10, then there should be only 1 bit useful in the `value`
        #   in the last iteration
        if iteration > 10 or ((iteration == 10) and (value > 1)):
            raise OverflowError("Varint overflowed")
    return result


async def read_pbmsg_safe(s, pb_msg):
    len_msg_bytes = await read_varint(s, read_byte)
    msg_bytes = await s.readexactly(len_msg_bytes)
    pb_msg.ParseFromString(msg_bytes)
