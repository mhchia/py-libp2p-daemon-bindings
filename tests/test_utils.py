import pytest

from p2pclient.exceptions import ControlFailure
from p2pclient.pb import p2pd_pb2 as p2pd_pb
from p2pclient.utils import raise_if_failed


def test_raise_if_failed_raises():
    resp = p2pd_pb.Response()
    resp.type = p2pd_pb.Response.ERROR
    with pytest.raises(ControlFailure):
        raise_if_failed(resp)


def test_raise_if_failed_not_raises():
    resp = p2pd_pb.Response()
    resp.type = p2pd_pb.Response.OK
    raise_if_failed(resp)
