import socket
import sys

import base58

import multiaddr

from p2pd.config import (
    control_path,
    listen_path,
)
from p2pd.constants import (
    BUFFER_SIZE,
)
from p2pd.serialization import (
    PBReadWriter,
)

import p2pd.pb.p2pd_pb2 as p2pd_pb


class Multiaddr(multiaddr.Multiaddr):
    """Currently use `multiaddr.Multiaddr` as the backend.
    """

    def __init__(self, maddr_bytes):
        # e.g. maddr_bytes = b'\x04\x7f\x00\x00\x01\x06\xc2\xc9'
        maddr_hex = maddr_bytes.hex()  # '047f00000106c2c9'
        maddr_hex_bytes = maddr_hex.encode()
        super().__init__(bytes_addr=maddr_hex_bytes)

    def to_bytes(self):
        strange_bytes = super().to_bytes()  # b'047f00000106c2c9'
        maddr_hex = str(strange_bytes)[2:-1]  # '047f00000106c2c9'
        return bytes.fromhex(maddr_hex)

    def to_string(self):
        return multiaddr.codec.bytes_to_string(self._bytes)


class Client:
    control_path = None
    listen_path = None
    listener = None

    mutex_handlers = None
    handlers = None

    def __init__(self, control_path, listen_path):
        self.control_path = control_path
        self.listen_path = listen_path
        # TODO: handlers
        # TODO: listen sock

    def _new_control_conn(self):
        s = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
        # TODO: handle `socket.error`?
        s.connect(self.control_path)
        return s

    def identify(self):
        s = self._new_control_conn()
        rw = PBReadWriter(s, BUFFER_SIZE)  # FIXME: why BUFFER_SIZE can't be too large?
        req = p2pd_pb.Request(type=p2pd_pb.Request.IDENTIFY)
        rw.write(req)

        resp = p2pd_pb.Response()
        rw.read(resp)
        assert resp.identify is not None
        peer_id_bytes = resp.identify.id
        maddrs_bytes = resp.identify.addrs

        # TODO: PeerID, MultiAddr
        maddrs = []
        for maddr_bytes in maddrs_bytes:
            # addr is
            # maddr_str = str(maddr)[2:-1]
            # maddr_bytes_m = bytes.fromhex(maddr_str)
            maddr = Multiaddr(maddr_bytes)
            assert maddr.to_bytes() == maddr_bytes
            maddr_str = maddr.to_string()
            maddrs.append(maddr_str)
        peer_id = base58.b58encode(peer_id_bytes)

        s.close()

        return peer_id, maddrs


def main():
    c = Client(control_path, listen_path)
    print(c.identify())


if __name__ == "__main__":
    main()
