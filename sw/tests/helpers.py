"""Shared test helpers."""

from pathlib import Path

import numpy as np

FIXTURES = Path(__file__).parent / "fixtures"


def load_fixture(name: str) -> dict[str, np.ndarray] | str:
    """Load a fixture file from ``sw/tests/fixtures/``.

    Parameters
    ----------
    name : str
        File name, e.g. ``"lfsr_im.npz"`` or ``"characters.txt"``.

    Returns
    -------
    dict[str, np.ndarray] | str
        For ``.npz``, every array by key, read fully so the file is closed.
        For any other file, its text.
    """
    path = FIXTURES / name
    if path.suffix == ".npz":
        with np.load(path) as data:
            return {key: data[key] for key in data.files}
    return path.read_text()
