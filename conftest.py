import pytest


def pytest_addoption(parser):
    parser.addoption(
        "--simulator",
        dest="simulator",
        default="verilator",
        help="simulator used by cocotb",
    )
    parser.addoption(
        "--waves",
        dest="waves",
        default=0,
        help="enabling wave generation. verilator \
            generates .fst; modelsim generats .wlf ",
    )


@pytest.fixture
def simulator(request):
    return request.config.getoption("--simulator")


@pytest.fixture
def waves(request):
    return request.config.getoption("--waves")
