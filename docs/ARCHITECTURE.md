# Architecture

What each component does and its interface. This file describes the current state. Components not built yet are marked **planned** with their milestone; each PR that builds one replaces its sketch with the real interface.

## Purpose

Hypercorex v2 is a clean, plug-and-play core for non-binary HDC/VSA.
- The SW comes first and is the golden reference. The HW is rebuilt against it afterwards, from H0.
- The SW keeps the idea of the old `app/` + `lib/`: one reusable model with item memories, a per-app encoder, associative-memory search, and switches.
- Later, the same Config drives both SW exploration and the HW build, with swappable iM, encoder and AM variants.

## Principles

1. The Python model is the source of truth, and the RTL is checked against it bit for bit.
2. Extend by adding a registered class (HV type, iM, similarity), not by editing core code.
3. One Config drives everything: a run, a sweep, and later the HW build.
4. Every run is seeded and reproducible.
5. Every saved artefact round-trips (Config, model, results).
6. Build one vertical slice end to end before generalising.

## Layout

Target layout. Entries marked (planned) don't exist yet.

```
hypercorex/
├── README.md  LICENSE  CLAUDE.md
├── pixi.toml  pixi.lock                     # default env only (D21)
├── .gitignore  .pre-commit-config.yaml
├── .github/workflows/                       # commented out until S7 (D7)
├── docs/                                    # WORKFLOW, ARCHITECTURE, DECISIONS, STATUS, HOUSEKEEPING, PR
├── sw/
│   ├── pyproject.toml                       # `hypercorex` package: src layout, hatchling, ruff, pytest
│   ├── src/hypercorex/
│   │   ├── __init__.py
│   │   ├── config.py                        # (planned, S1.1)
│   │   ├── hv/                              # (planned, S1.2, S2) base, binary, bipolar, uint, real
│   │   ├── im/                              # (planned, S1.3, S3) base, ri, lfsr, ca90, cim
│   │   ├── am.py                            # (planned, S1.4)
│   │   ├── model.py                         # (planned, S1.5)
│   │   ├── data.py                          # (planned, S4.1)
│   │   ├── run.py                           # (planned, S1.5)
│   │   ├── sweep.py                         # (planned, S6.1)
│   │   └── profile.py                       # (planned, S6.2)
│   ├── apps/                                # (planned, S1.6, S4, S5)
│   ├── examples/                            # (planned) walk-throughs
│   ├── tests/                               # one test file per block
│   │   └── fixtures/                        # golden data from the old code (D19)
│   └── data/                                # gitignored: datasets, trained models, results
├── hw/                                      # README placeholder until H0
└── rtl/ tests/ questa/ Bender.yml Makefile conftest.py   # parked HW (D3)
```

## SW components

A model is its item memories plus an app encoder plus an associative memory, all driven by one Config.

| Component | Status | Role |
|---|---|---|
| Package `hypercorex` | exists after S0.6 | Holds `__version__` only |
| Config | planned, S1.1 | All switches, e.g. `dim`, `hv`, `gen`, `encode_bits`, `am_bits`, `retrain_epochs`, `seed` (D8, D9) |
| HV type | planned, S1.2 / S2 | bind, bundle, quantize, similarity (D10–D13) |
| Item memories | planned, S1.3 / S3 | Declared by name per app, e.g. `{"id": ..., "level": ...}`, each with its own generator (D14) |
| Encoder | planned, S1.6 | The only code an app writes. Works on a batch where possible, per sample for variable-length input (language) |
| AM | planned, S1.4 | Accumulators and counts; the searchable copy (frozen, or quantized to `am_bits`); the retrain update; search with a pluggable similarity |
| Data | planned, S4.1 | `X, y` arrays, one seeded RNG, no in-place changes to the caller's data |
| Runner | planned, S1.5 | Download, split, train, retrain, test, save/load, and a results object (accuracy, per class, confusion matrix) |

App sketch (target shape, not a final API):

```python
class IdLevelDigit(Model):
    memories = {"id": ItemMem(n=784), "level": ItemMem(n=2, kind="cim")}

    def encode(self, x):                      # x: (batch, 784)
        return self.hv.bind(self.im["id"], self.im["level"][x]).sum(axis=1)

run(IdLevelDigit, datasets.mnist_bin,
    Config(dim=512, hv="bipolar", gen="lfsr", am_bits=1, retrain_epochs=1, seed=42))
```

### HV types

| Type | Elements | Bind | Similarity | Milestone |
|---|---|---|---|---|
| binary | {0, 1} | XOR | Hamming (normalised) | S1 |
| bipolar | {+1, −1}, with 0 → +1 and 1 → −1 (D11) | multiply | dot / cosine | S1 |
| uint | unsigned integers | multiply | dot (open item 1) | S2 |
| real | float32 | multiply | cosine | S2 |
| intN | int2/4/8 | — | — | hook only |
| FHRR | phases | — | — | hook only |

### Apps

| Old (at the tag) | New | Milestone |
|---|---|---|
| char recognition (`lib/vsax_models.py` self-test) | `char.py` | S1 |
| `app/vsax_bin_digit_recog.py` | `digit_bin.py` | S4 |
| `app/vsax_bin_idlvl_digit_recog.py` | `digit_idlvl.py` | S4 |
| `app/vsax_digit_recog.py` | `digit_gray.py` | S4 |
| `app/vsax_bin_dna_recog.py` | `dna.py` | S4 |
| `app/vsax_bin_isolet_recog.py` | `isolet.py` | S4 |
| `app/vsax_bin_lang_recog.py` | `lang.py` | S4 |
| `hdc_exp/ucihar_recog.py` | `ucihar.py` | S5 |

Dataset sources:
- mnist uint/bin, dna, isolet and lang: `rgantonio/chronomatica` GitHub releases.
- UCI-HAR: the hypercorex release `ds_hdc_ucihar_recog_v0.0.1` (`ucihar_recog.tar.gz`).

## HW (parked until H0)

The HW files stay at the root, untouched (D3). There is no `hw` env on `v2` until H0 (D21), so the parked tests run from a checkout of the tag.

After S0, many parked cocotb tests can't run on `v2` even with an env, because their golden values come from deleted code:
- 24 files import `hdc_exp`;
- 12 import the old assembler in `sw/`;
- 6 read `hemaia/`;
- 3 import `lib/`.

H0 moves them onto the new package.

Notes recorded for H0:
- **The v1 top doesn't build.** `hypercorex_top.sv` uses `assoc_mem`, and `Bender.yml` lists `assoc_mem.sv`, but that file is gone. `Bender.yml` lists no v2 files.
- **The bundler output is likely inverted.** `multi_in_bundler_unit.sv` maps bit 1 → −1, then `multi_in_bundler_set.sv` outputs 0 for a negative counter, so a majority of 1s gives 0. `test_vsax_id_level_top.py` never checks `predict_o` against a golden class.
- **The iM variants have different ports.** ROM and CA90 have 2 fixed ports, LFSR has N, `cim` has 1, and seeds are sometimes a port and sometimes a parameter. This is the main blocker for plug-and-play.
  - Proposed iM contract: N read ports `(valid, ready, idx) → (valid, ready, hv[ElemWidth×D])`, with seed and config as a parameter struct, so a cache-like iM can stall behind the same ports.
- **The generalised `cim.sv` is not on `main`.** `main` has the CA90 one with `NumCimLevels = HVDimension/2`.
- **The AM is fixed at 32 classes** (`binary_compare` tree, `bin_sim_search` localparams), and Hamming scoring is built into the search FSM. Split it into memory + iteration and a swappable scoring unit.
- **Everything is 1 bit per dimension.** There is no element-width parameter.
- **Generation uses Mako,** and `ca90_hier_base.sv.tpl` references a module that no longer exists. Redo it with Jinja2.
- **Some sizes are hardcoded.** `ca90_hier_base` only works at 512 dims with a 32-bit seed, the ROM iM is fixed at 512×1024, and `extend_count_i` is `[4:0]`.
- **Small cleanups.** `sram_memory.sv` isn't used anywhere. The Questa filelist has an absolute home path. Parameter names are inconsistent.
- **The fixture `ca90_im.npz` keys `hw_d512_n1024` and `hw_d256_n512`** hold the old golden CA90 iM for the parked `test_ca90_item_memory.py` configs.

## Build order

S0 clean slate → S1 char recognition end to end → S2 HV types → S3 item memories → S4 data and six apps → S5 UCI-HAR → S6 exploration → S7 SW close → H0 HW planning. STATUS tracks progress.

## Non-goals (for now)

- GPU support (D6).
- Running the old app scripts or loading the old trained models (D15).
- intN and FHRR beyond interface hooks.
