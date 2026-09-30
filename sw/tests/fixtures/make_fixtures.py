"""Write the golden fixtures from a checkout of the old code (D19).

This script runs against the old code at the tag ``discontinue-old-hypercorex`` in a
temporary Python 3.11 / numpy 1.26 environment. It is never run by ``pixi run test``.
The command that made the committed files is in ``README.md`` next to this script.

Usage::

    python make_fixtures.py --old <checkout of the tag> --out <output dir>
"""

import argparse
import json
import subprocess
import sys
from pathlib import Path

import numpy as np

# (seed, dim, items) for the LFSR iM: the parked RTL test config, the app config,
# odd-dim and edge seeds.
LFSR_CASES = [
    (0x2A, 128, 32),
    (0x2A, 512, 1024),
    (0x0, 100, 16),
    (0xFFFFFFFF, 100, 16),
    (0x1234ABCD, 100, 16),
]

# (dim, items) for the HW CA90 iM, as in the parked RTL test.
CA90_HW_CASES = [(512, 1024), (256, 512)]

# Dim of the row-by-row and hierarchical CA90 expansions.
CA90_ROWS_DIM = 512

# Seed width of the CA90 generators.
CA90_SEED_BITS = 32


def import_old(old: Path) -> tuple:
    """Import the old ``vsax``, ``hdc_util`` and ``set_parameters`` modules.

    Parameters
    ----------
    old : Path
        Root of a checkout of the tag.

    Returns
    -------
    tuple
        The modules ``(vsax, hdc_util, set_parameters)``.
    """
    for sub in ("lib", "hdc_exp", "tests"):
        sys.path.insert(0, str(old / sub))
    import hdc_util
    import set_parameters
    import vsax

    return vsax, hdc_util, set_parameters


def to_binary(array: np.ndarray) -> np.ndarray:
    """Return ``array`` as uint8, after checking it holds only 0 and 1.

    Parameters
    ----------
    array : np.ndarray
        An iM in binary form, in any integer or float dtype.

    Returns
    -------
    np.ndarray
        The same values as uint8.
    """
    array = np.asarray(array)
    if not np.isin(array, (0, 1)).all():
        raise ValueError("expected an array in binary form, with values 0 and 1 only")
    return array.astype(np.uint8)


def lfsr_key(seed: int, dim: int, items: int) -> str:
    """Return the fixture key for one LFSR case, e.g. ``s0000002a_d512_n1024``."""
    return f"s{seed:08x}_d{dim}_n{items}"


def make_lfsr(vsax) -> tuple[dict[str, np.ndarray], dict[str, str]]:
    """Build the arrays and old calls for ``lfsr_im.npz``."""
    arrays = {}
    calls = {}
    for seed, dim, items in LFSR_CASES:
        key = lfsr_key(seed, dim, items)
        arrays[key] = to_binary(
            vsax.hv_gen_orthogonal_im(
                num_items=items,
                hv_size=dim,
                hv_type="binary",
                gen_type="lfsr",
                gen_lfsr_base_seed=seed,
            )
        )
        arrays[f"start_{key}"] = np.array(
            [vsax.lfsr_item_seed(seed, i) for i in range(items)], dtype=np.uint32
        )
        calls[key] = (
            f"vsax.hv_gen_orthogonal_im(num_items={items}, hv_size={dim}, "
            f'hv_type="binary", gen_type="lfsr", gen_lfsr_base_seed=0x{seed:08x})'
        )
    return arrays, calls


def make_ca90(hdc_util, set_parameters) -> tuple[dict[str, np.ndarray], dict[str, str]]:
    """Build the arrays and old calls for ``ca90_im.npz``."""
    seeds = list(set_parameters.ORTHO_IM_SEEDS)
    arrays = {"seeds": np.array(seeds, dtype=np.uint32)}
    calls = {}
    for dim, items in CA90_HW_CASES:
        key = f"hw_d{dim}_n{items}"
        # gen_ca90_im_set returns (seed_list, iM, conf_mat).
        _, im, _ = hdc_util.gen_ca90_im_set(
            CA90_SEED_BITS, dim, items, dim // 4, base_seeds=seeds, gen_seed=True
        )
        arrays[key] = to_binary(im)
        calls[key] = (
            f"hdc_util.gen_ca90_im_set({CA90_SEED_BITS}, {dim}, {items}, {dim // 4}, "
            "base_seeds=ORTHO_IM_SEEDS, gen_seed=True)[1]"
        )
    for key, name in (
        (f"iter_d{CA90_ROWS_DIM}", "gen_hv_ca90_iterate_rows"),
        (f"hier_d{CA90_ROWS_DIM}", "gen_hv_ca90_hierarchical_rows"),
    ):
        generate = getattr(hdc_util, name)
        arrays[key] = to_binary(
            [
                generate(hdc_util.numbin2list(seed, CA90_SEED_BITS), CA90_ROWS_DIM)
                for seed in seeds
            ]
        )
        calls[key] = (
            f"[hdc_util.{name}(hdc_util.numbin2list(seed, {CA90_SEED_BITS}), "
            f"{CA90_ROWS_DIM}) for seed in ORTHO_IM_SEEDS]"
        )
    return arrays, calls


def save(
    path: Path, arrays: dict[str, np.ndarray], calls: dict[str, str], commit: str
) -> None:
    """Write one fixture file with its ``meta`` entry.

    Parameters
    ----------
    path : Path
        The ``.npz`` file to write.
    arrays : dict[str, np.ndarray]
        The arrays, by key.
    calls : dict[str, str]
        The old call for each key except ``start_*`` and ``seeds``.
    commit : str
        The commit of the old checkout.
    """
    meta = {
        "source_commit": commit,
        "numpy": np.__version__,
        "calls": calls,
    }
    np.savez_compressed(path, **arrays, meta=np.array(json.dumps(meta, indent=1)))


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--old", type=Path, required=True, help="checkout of the tag")
    parser.add_argument("--out", type=Path, required=True, help="output directory")
    args = parser.parse_args()

    old = args.old.resolve()
    commit = subprocess.run(
        ["git", "-C", str(old), "rev-parse", "HEAD"],
        check=True,
        capture_output=True,
        text=True,
    ).stdout.strip()
    vsax, hdc_util, set_parameters = import_old(old)

    args.out.mkdir(parents=True, exist_ok=True)
    save(args.out / "lfsr_im.npz", *make_lfsr(vsax), commit)
    save(args.out / "ca90_im.npz", *make_ca90(hdc_util, set_parameters), commit)


if __name__ == "__main__":
    main()
