# Test fixtures

Golden data from the old code, used to check the new generators bit for bit (D19).
Tests load these files only through `load_fixture` in `sw/tests/helpers.py`. The format
rules are in `docs/HOUSEKEEPING.md`, "Formats".

- **Source commit:** `96b8e9e1475daa3fef015482ab34817e62fdb4ff`, the tag
  `discontinue-old-hypercorex`.
- **Environment:** Python 3.11.16 and numpy 1.26.4, from `pixi exec`.

## Files

| File | What it holds |
|---|---|
| `lfsr_im.npz` | LFSR item memories from `vsax.hv_gen_orthogonal_im(..., gen_type="lfsr")`, plus each item's LFSR start state |
| `ca90_im.npz` | CA90 item memories from `hdc_util`: the HW iM, and the row-by-row and hierarchical expansions |
| `characters.txt` | 26 letter bitmaps, one letter per line as 35 characters `0` or `1`, copied from the tag's `hdc_exp/data_set/char_recog/characters.txt` |
| `make_fixtures.py` | The script that writes both `.npz` files |

Every array in the `.npz` files is in binary form, uint8 {0, 1}, with row `i` = item
`i`. Seeds and start states are uint32. Each file also has a `meta` entry: a JSON
string with `source_commit`, `numpy`, and, under `calls`, the old call behind each key
(except `start_*` and `seeds`).

### `lfsr_im.npz`

Keys are named `s{seed:08x}_d{dim}_n{items}`.

| Key | Seed | Dim | Items | Why |
|---|---|---|---|---|
| `s0000002a_d128_n32` | `0x2a` | 128 | 32 | The parked RTL LFSR test config |
| `s0000002a_d512_n1024` | `0x2a` | 512 | 1024 | The app config |
| `s00000000_d100_n16` | `0x0` | 100 | 16 | Seed 0; item 0 is all zeros (open item 9) |
| `sffffffff_d100_n16` | `0xffffffff` | 100 | 16 | All-ones seed |
| `s1234abcd_d100_n16` | `0x1234abcd` | 100 | 16 | Mixed seed |

For each key above, `start_<key>` holds `[vsax.lfsr_item_seed(seed, i) for i in range(items)]`,
with shape `(items,)`.

### `ca90_im.npz`

| Key | Shape | What |
|---|---|---|
| `seeds` | (8,) | `ORTHO_IM_SEEDS` from the tag's `tests/set_parameters.py` |
| `hw_d512_n1024` | (1024, 512) | `gen_ca90_im_set(32, 512, 1024, 128, base_seeds=seeds, gen_seed=True)[1]`: 8 banks of 128 items, the parked RTL test config |
| `hw_d256_n512` | (512, 256) | The same at dim 256 with 512 items: 8 banks of 64 |
| `iter_d512` | (8, 512) | `gen_hv_ca90_iterate_rows(numbin2list(seed, 32), 512)`, one row per seed |
| `hier_d512` | (8, 512) | `gen_hv_ca90_hierarchical_rows(numbin2list(seed, 32), 512)`, one row per seed |

Row `k * 128` of `hw_d512_n1024` equals row `k` of `hier_d512`: each bank starts with its
seed's hierarchical expansion.

## Regenerating

From the repo root:

```bash
git worktree add ../hypercorex-old discontinue-old-hypercorex
pixi exec --spec "python=3.11" --spec "numpy=1.26" --spec tqdm --spec matplotlib \
  --spec requests -- python sw/tests/fixtures/make_fixtures.py \
  --old ../hypercorex-old --out sw/tests/fixtures
```

`characters.txt` was copied with:

```bash
git show discontinue-old-hypercorex:hdc_exp/data_set/char_recog/characters.txt \
  > sw/tests/fixtures/characters.txt
```

The same environment gives byte-identical `.npz` files; check with `cmp` against a
second run into a temporary directory. `pixi run test` never runs the script.
