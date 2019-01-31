from .exceptions import ControlFailure
from .pb import p2pd_pb2 as p2pd_pb


def raise_if_failed(response):
    if response.type == p2pd_pb.Response.ERROR:
        raise ControlFailure(
            "connect failed. msg={}".format(
                response.error.msg,
            )
        )
