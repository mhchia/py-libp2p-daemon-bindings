import pytest

from multiaddr import (
    Multiaddr,
)

from p2pclient import (
    config,
)
from p2pclient.p2pclient import (
    Client,
)


@pytest.mark.parametrize(
    "control_maddr_str, listen_maddr_str",
    (
        ("/unix/123", "/ip4/127.0.0.1/tcp/7777"),
        ("/ip4/127.0.0.1/tcp/6666", "/ip4/127.0.0.1/tcp/7777"),
        ("/ip4/127.0.0.1/tcp/6666", "/unix/123"),
        ("/unix/456", "/unix/123"),
    ),
)
def test_client_ctor_control_listen_maddr(control_maddr_str, listen_maddr_str):
    c = Client(Multiaddr(control_maddr_str), Multiaddr(listen_maddr_str))
    assert c.control_maddr == Multiaddr(control_maddr_str)
    assert c.listen_maddr == Multiaddr(listen_maddr_str)


def test_client_ctor_default_control_listen_maddr():
    c = Client()
    assert c.control_maddr == Multiaddr(config.control_maddr_str)
    assert c.listen_maddr == Multiaddr(config.listen_maddr_str)


def test_client_listen_path():
    c = Client(Multiaddr("/unix/456.sock"), Multiaddr("/unix/tmp/123.sock"))
    assert c.control_path == "/456.sock"
    assert c.listen_path == "/tmp/123.sock"
