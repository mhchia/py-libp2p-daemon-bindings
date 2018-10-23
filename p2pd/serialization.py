from google.protobuf.internal.decoder import _DecodeVarint
from google.protobuf.internal.encoder import _VarintBytes

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


class PBReadWriter:

    socket = None
    read_max_size = BUFFER_SIZE  # FIXME: why BUFFER_SIZE can't be too large?

    def __init__(self, sock):
        self.socket = sock

    def write(self, pb_msg):
        pb_msg_bytes = serialize(pb_msg)
        self.socket.sendall(pb_msg_bytes)

    def read(self, pb_msg):
        data = self.socket.recv(self.read_max_size)
        deserialize(data, pb_msg)
