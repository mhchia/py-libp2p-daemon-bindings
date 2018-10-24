import io

import pytest

from p2pd.serialization import (
    read_byte,
    read_varint,
    write_varint,
)


def test_serialize():
    pass


def test_deserialize():
    pass


def test_pb_readwriter():
    pass


def test_read_byte():
    msg_bytes = b"123"
    s = io.BytesIO(msg_bytes)
    assert read_byte(s) == msg_bytes[0]
    assert read_byte(s) == msg_bytes[1]
    assert read_byte(s) == msg_bytes[2]
    with pytest.raises(EOFError):
        read_byte(s)


@pytest.mark.parametrize(
    "value",
    (0, 1, 128, 2 ** 32, 2 ** 64 - 1),
)
def test_read_varint(value):
    s = io.BytesIO()
    write_varint(s, value)
    s.seek(0,0)
    result = read_varint(s)
    assert value == result


def test_read_varint_overflow():
    pass
