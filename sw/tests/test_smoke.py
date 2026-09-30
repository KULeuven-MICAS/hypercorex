"""Smoke tests for the package skeleton."""

from importlib.metadata import version

import numpy as np

import hypercorex


def test_version_matches_metadata() -> None:
    assert hypercorex.__version__ == version("hypercorex")


def test_numpy_major_is_at_least_2() -> None:
    assert int(np.__version__.split(".")[0]) >= 2
