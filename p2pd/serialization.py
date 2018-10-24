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


class SockStream:
    """Wrap read/write to socket
    """
    socket = None

    def __init__(self, sock):
        self.socket = sock

    def read(self, num_bytes):
        return self.socket.recv(num_bytes)

    def write(self, data_bytes):
        self.socket.sendall(data_bytes)

    def close(self):
        self.socket.close()


# TODO: if we want to use it in sockets, it is possibly blocked?
def read_byte(s):
    b = s.read(1)
    if len(b) == 0:
        raise EOFError
    return b[0]


def read_varint(s):
    iteration = 0
    chunk_bits = 7
    result = 0
    has_next = True
    while has_next:
        c = read_byte(s)
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


def write_varint(s, value):
    _EncodeVarint(s.write, value, True)


class PBReadWriter:

    iostream = None
    read_max_size = BUFFER_SIZE

    def __init__(self, iostream):
        self.iostream = iostream

    def write_msg(self, pb_msg):
        pb_msg_bytes = serialize(pb_msg)
        self.iostream.write(pb_msg_bytes)

    def read_msg(self, pb_msg):
        data = self.iostream.read(self.read_max_size)
        deserialize(data, pb_msg)

    def read_varint(self):
        # TODO: get use of `self.read_one_byte`, read a complete varint
        return read_varint(self.iostream)

    def read_msg_bytes_safe(self):
        # TODO: call `len = self.read_varint`, get the len of the data in varint type
        # TODO: `data = self._read_bytes(len)`, and do `deserialize(data, pbmsg)`
        len_msg_bytes = self.read_varint()
        msg_bytes = self.iostream.read(len_msg_bytes)
        return msg_bytes

    def read_msg_safe(self, pb_msg):
        msg_bytes = self.read_msg_bytes_safe()
        pb_msg.ParseFromString(msg_bytes)
