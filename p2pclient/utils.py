from .exceptions import ControlFailure
from .pb import p2pd_pb2 as p2pd_pb


def raise_if_failed(response):
    print("response = ", response)
    if response.type == p2pd_pb.Response.ERROR:
        raise ControlFailure(
            "connect failed. msg={}".format(
                response.error.msg,
            )
        )


def trim_path_unix_prefix(path):
    unix_prefix = "/unix"
    # TODO: is it possible the path after "/unix" is a relative path?
    if not path.startswith(unix_prefix):
        raise ValueError(f"path {path} should start with the unix prefix {unix_prefix}")
    return path[len(unix_prefix):]
