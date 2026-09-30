"""Tests for the golden fixtures made from the old code (D19)."""

import json
import re

import numpy as np
import pytest
from helpers import load_fixture

LFSR_IM_KEYS = [
    "s0000002a_d128_n32",
    "s0000002a_d512_n1024",
    "s00000000_d100_n16",
    "sffffffff_d100_n16",
    "s1234abcd_d100_n16",
]
KEY_PATTERN = re.compile(r"s[0-9a-f]{8}_d(\d+)_n(\d+)")


@pytest.fixture(scope="module")
def lfsr() -> dict[str, np.ndarray]:
    return load_fixture("lfsr_im.npz")


@pytest.fixture(scope="module")
def ca90() -> dict[str, np.ndarray]:
    return load_fixture("ca90_im.npz")


def test_lfsr_keys(lfsr: dict[str, np.ndarray]) -> None:
    expected = {"meta", *LFSR_IM_KEYS, *(f"start_{key}" for key in LFSR_IM_KEYS)}
    assert set(lfsr) == expected


def test_lfsr_ims_are_binary_uint8_with_shape_from_key(
    lfsr: dict[str, np.ndarray],
) -> None:
    for key in LFSR_IM_KEYS:
        dim, items = map(int, KEY_PATTERN.fullmatch(key).groups())
        im = lfsr[key]
        assert im.dtype == np.uint8, key
        assert im.shape == (items, dim), key
        assert np.isin(im, (0, 1)).all(), key


def test_lfsr_start_states_are_uint32(lfsr: dict[str, np.ndarray]) -> None:
    for key in LFSR_IM_KEYS:
        _, items = map(int, KEY_PATTERN.fullmatch(key).groups())
        start = lfsr[f"start_{key}"]
        assert start.dtype == np.uint32, key
        assert start.shape == (items,), key


def test_lfsr_app_config_mean(lfsr: dict[str, np.ndarray]) -> None:
    assert lfsr["s0000002a_d512_n1024"].mean() == 0.5000152587890625


def test_lfsr_seed_zero_gives_all_zero_item(lfsr: dict[str, np.ndarray]) -> None:
    # Open item 9: base seed 0 and item 0 give LFSR state 0.
    assert not lfsr["s00000000_d100_n16"][0].any()
    assert lfsr["start_s00000000_d100_n16"][:2].tolist() == [0, 3652664798]


def test_ca90_keys_and_shapes(ca90: dict[str, np.ndarray]) -> None:
    shapes = {key: value.shape for key, value in ca90.items() if key != "meta"}
    assert shapes == {
        "hw_d512_n1024": (1024, 512),
        "hw_d256_n512": (512, 256),
        "iter_d512": (8, 512),
        "hier_d512": (8, 512),
        "seeds": (8,),
    }
    assert ca90["seeds"].dtype == np.uint32
    for key in ("hw_d512_n1024", "hw_d256_n512", "iter_d512", "hier_d512"):
        assert ca90[key].dtype == np.uint8, key
        assert np.isin(ca90[key], (0, 1)).all(), key


def test_ca90_hw_bank_heads_are_hierarchical_rows(
    ca90: dict[str, np.ndarray],
) -> None:
    # Each of the 8 banks of 128 items starts with its seed's hierarchical expansion.
    for k in range(8):
        np.testing.assert_array_equal(
            ca90["hw_d512_n1024"][k * 128], ca90["hier_d512"][k]
        )


def test_ca90_means(ca90: dict[str, np.ndarray]) -> None:
    assert ca90["hw_d512_n1024"].mean() == 0.48775482177734375
    assert ca90["iter_d512"].mean(axis=1).tolist() == [
        0.5234375,
        0.4609375,
        0.5,
        0.5234375,
        0.4609375,
        0.5,
        0.5234375,
        0.4609375,
    ]


@pytest.mark.parametrize("name", ["lfsr_im.npz", "ca90_im.npz"])
def test_meta(name: str) -> None:
    arrays = load_fixture(name)
    meta = json.loads(str(arrays["meta"]))
    assert {"source_commit", "numpy", "calls"} <= set(meta)
    array_keys = {
        key
        for key in arrays
        if key not in ("meta", "seeds") and not key.startswith("start_")
    }
    assert set(meta["calls"]) == array_keys


def test_characters() -> None:
    lines = load_fixture("characters.txt").splitlines()
    assert len(lines) == 26
    for line in lines:
        assert len(line) == 35
        assert set(line) <= {"0", "1"}
