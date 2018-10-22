import socket
import sys

import base58

from multiaddr import (
    Multiaddr,
)

from google.protobuf.internal.decoder import _DecodeVarint32
from google.protobuf.internal.encoder import _VarintBytes

from config import (
    server_addr,
)
from constants import (
    BUFFER_SIZE,
)

import pb.p2pd_pb2 as p2pd_pb


s = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
try:
    s.connect(server_addr)
except socket.error as msg:
    print(msg)
    sys.exit(1)

# s.sendall(b"12345")
# data = s.recv(16)
# print('received {!r}'.format(data))

req = p2pd_pb.Request(type=p2pd_pb.Request.IDENTIFY)
size = req.ByteSize()
size_prefix = _VarintBytes(size)
to_send = size_prefix + req.SerializeToString()
s.sendall(to_send)

data = s.recv(BUFFER_SIZE)
print('received {!r}'.format(data))

msg_len, new_pos = _DecodeVarint32(data, 0)
msg_bytes = data[new_pos:(new_pos + msg_len)]
resp = p2pd_pb.Response()
resp.ParseFromString(msg_bytes)
assert resp.identify is not None
print(resp.identify)
peer_id_bytes = resp.identify.id
maddrs_bytes = resp.identify.addrs


def bytes_to_maddr(maddr_bytes):
    # maddr_bytes = b'\x04\x7f\x00\x00\x01\x06\xc2\xc9'
    maddr_hex = maddr_bytes.hex()  # '047f00000106c2c9'
    maddr_hex_bytes = maddr_hex.encode()
    return Multiaddr(bytes_addr=maddr_hex_bytes)


def maddr_to_bytes(maddr):
    strange_bytes = maddr.to_bytes()  # b'047f00000106c2c9'
    maddr_hex = str(strange_bytes)[2:-1]  # '047f00000106c2c9'
    return bytes.fromhex(maddr_hex)


maddrs = []
for maddr_bytes in maddrs_bytes:
    # addr is
    # maddr_str = str(maddr)[2:-1]
    # maddr_bytes_m = bytes.fromhex(maddr_str)
    assert maddr_to_bytes(bytes_to_maddr(maddr_bytes)) == maddr_bytes
    maddr = str(bytes_to_maddr(maddr_bytes))
    maddrs.append(maddr)

peer_id_str = base58.b58encode(peer_id)
