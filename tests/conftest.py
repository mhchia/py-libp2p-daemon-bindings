import pytest


def pytest_addoption(parser):
    parser.addoption(
        "--daemon",
        action="store",
        type=str,
        default="p2pd",
        choices=("p2pd", "jsp2pd"),
        help="Select the P2P daemon to use (default: p2pd).",
    )


@pytest.fixture
def daemon_executable(request):
    return request.config.getoption("--daemon")


def pytest_collection_modifyitems(config, items):
    # No tests skipped when using the Go daemon at the moment
    if config.getoption("--daemon") == "p2pd":
        return

    skip_reasons = {
        "go_only": "this feature is not supported by jsp2pd.",
        "jsp2pd_probable_bug": "this test fails with jsp2pd, could be because of a bug.",
    }
    for item in items:
        for mark, reason in skip_reasons.items():
            if mark in item.keywords:
                item.add_marker(pytest.mark.skip(reason=reason))
