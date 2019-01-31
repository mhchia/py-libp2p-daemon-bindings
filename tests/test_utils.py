import pytest

from p2pclient.utils import (
    trim_path_unix_prefix,
)


@pytest.mark.parametrize(
    "unix_path, expected",
    (
        ("/unix", ""),
        ("/unix/", "/"),
        ("/unix/path", "/path"),
        ("/unix/path/2", "/path/2"),
    ),
)
def test_trim_path_unix_prefix_success(unix_path, expected):
    assert trim_path_unix_prefix(unix_path) == expected


@pytest.mark.parametrize(
    "unix_path",
    (
        "",
        "/123",
        "/123/456",
        "//unix",
        " /unix",
        "unix",
    )
)
def test_trim_path_unix_prefix_failure(unix_path):
    with pytest.raises(ValueError):
        trim_path_unix_prefix(unix_path)


# TODO: `raise_if_failed`
def test_raise_if_failed():
    pass
