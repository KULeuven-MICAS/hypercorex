# Status

Overall progress of the Hypercorex rewrite. While a PR is in progress, its detail is in `docs/PR.md`; between PRs there is no PR.md (D26).

## Where the code lives

- The old state is the tag `discontinue-old-hypercorex` at `96b8e9e`. `main` is still at that commit until `s0-clean-slate` merges.
- Each PR branch comes off `main` and merges or squash-merges back into `main` (D24), so `main` holds the rewrite in progress.
- v1 lives on branch `hypercorex_v1`.
- **Current PR:** `None`.

## Milestones

| Milestone | Content | PRs | Status |
|---|---|---|---|
| S0 | Clean slate: docs set, minimal env, deletions, `sw/` skeleton, fixtures; old-app baselines | `s0-clean-slate`, `s0-baselines` | wip |
| S1 | Vertical slice: char recognition end to end (binary, bipolar, `ri`) | — | todo |
| S2 | HV types: uint, real, hooks for intN and FHRR | — | todo |
| S3 | Item memories: `lfsr`, `ca90`, `cim`, iM profiling | — | todo |
| S4 | Data and the six apps | — | todo |
| S5 | UCI-HAR | — | todo |
| S6 | Exploration: sweeps, profiling, plots | — | todo |
| S7 | SW close: interfaces frozen, docs site | — | todo |
| H0 | HW planning: a discussion that writes the HW section and the H milestones; `hw` env; parked HW check (D21) | — | todo |
| Later | intN, FHRR, cache-like iM, golden-vector export for HW (placed at H0) | — | — |
| Later | GPU support for the SW flow (note only) | — | — |

Status values are `todo`, `brief` (plan agreed), `wip`, `done` and `deferred`.

## Planned tasks

This is the roadmap. A PR's own steps live in its PR.md; when a PR closes, its rows here get their status and PR name.

### S0 — Clean slate

| ID | Scope | Acceptance | PR | Status |
|---|---|---|---|---|
| S0.1 | Context docs (this set) | Committed as the first commit of `s0-clean-slate` | s0-clean-slate | done |
| S0.2 | Sync check | Report in PR.md Status | s0-clean-slate | done |
| S0.3 | Comment out all CI workflows (D7) | Nothing runs on push or PR | s0-clean-slate | done |
| S0.4 | Minimal `pixi.toml` and new `pixi.lock` (D21) | `pixi run smoke` prints Python 3.12.x and numpy 2.x | s0-clean-slate | done |
| S0.5 | Delete the D4 and D21 lists | Only the kept and parked files remain | s0-clean-slate | done |
| S0.6 | `sw/` skeleton, test/lint/fmt tasks, `.gitignore`, pre-commit | `pixi run test` and `pixi run lint` pass | s0-clean-slate | done |
| S0.7 | Golden fixtures from the tag (D19) | Fixture tests pass; regeneration is byte-identical | s0-clean-slate | done |
| S0.8 | README and `hw/README.md` placeholder | Files describe the rewrite and point to the docs | s0-clean-slate | done |
| S0.9 | Close the PR | STATUS updated, PR.md done | s0-clean-slate | done |
| S0.10 | Minimal CI: one workflow runs the sw tests and lint (D25) | CI green on the PR into `main` | s0-clean-slate | wip |
| S0.11 | Old-app baselines: the six apps and the char self-test, run from the tag with external seeds (D19) | Baselines table below filled; open item 4 closed | s0-baselines | todo |

### S1 — Vertical slice (char recognition)

| ID | Scope | Depends | Acceptance | Status |
|---|---|---|---|---|
| S1.1 | `Config`: fields, CLI overrides, to/from dict | S0 | Round-trip test | todo |
| S1.2 | HV type interface; binary and bipolar | S0 | Property tests: self-similarity 1, random pairs ≈ 0, bind self-inverse, D11 mapping | todo |
| S1.3 | Item memory interface; `ri` generator | S1.2 | Exact density; same seed gives same memory | todo |
| S1.4 | AM: accumulate, retrain update, quantized copy (`am_bits` None or 1), search | S1.2 | Tests on small hand-checked data | todo |
| S1.5 | `Model` base class and runner: train, retrain, test, results object, save/load | S1.1–S1.4 | A reloaded model gives the same predictions | todo |
| S1.6 | Char recognition app | S1.5 | Accuracy ≥ the S0.11 baseline (see open item 8) | todo |

### S2 — HV types

| ID | Scope | Depends | Acceptance | Status |
|---|---|---|---|---|
| S2.1 | Settle open item 1 (uint semantics) | S1 | Decision logged | todo |
| S2.2 | uint type | S2.1 | Property tests | todo |
| S2.3 | real type (float32) | S1 | Property tests | todo |
| S2.4 | Hooks for intN and FHRR: interface points documented, stubs only | S2.2, S2.3 | Described in ARCHITECTURE; stubs raise `NotImplementedError` | todo |
| S2.5 | Char recognition under every type | S2.2–S2.4 | Accuracy per type recorded below | todo |

### S3 — Item memories

| ID | Scope | Depends | Acceptance | Status |
|---|---|---|---|---|
| S3.1 | `lfsr`, vectorised (open item 9) | S1.3 | Matches `lfsr_im.npz` bit for bit | todo |
| S3.2 | `ca90` (open item 2) | S1.3 | Matches `ca90_im.npz` for the chosen variant | todo |
| S3.3 | `cim` (open item 3) | S1.3 | Level 0 is the seed; distance grows linearly with level; no duplicate levels | todo |
| S3.4 | iM profiling: density, pairwise similarity | S3.1–S3.3 | Functions with tests | todo |

### S4 — Data and apps

| ID | Scope | Depends | Acceptance | Status |
|---|---|---|---|---|
| S4.1 | `data.py`: registry, download, cache in `sw/data/`, `X, y`, seeded split | S1 | Same seed gives the same split | todo |
| S4.2 | `digit_bin`, `digit_idlvl`, `digit_gray` | S4.1, S3 | Within tolerance of the baselines (open item 4) | todo |
| S4.3 | `dna`, `isolet`, `lang` | S4.1, S3 | Within tolerance of the baselines | todo |

### S5 — UCI-HAR

| ID | Scope | Depends | Acceptance | Status |
|---|---|---|---|---|
| S5.1 | UCI-HAR in the dataset registry | S4.1 | Loads as `X, y` | todo |
| S5.2 | `ucihar` app, encoder taken from the old `hdc_exp/ucihar_recog.py` at the tag | S5.1 | Accuracy recorded as its baseline | todo |

### S6 — Exploration

| ID | Scope | Depends | Acceptance | Status |
|---|---|---|---|---|
| S6.1 | `sweep.py`: a grid of Configs → results table | S4 | Same seed gives the same table | todo |
| S6.2 | `profile.py`: capacity, per-class similarity | S3.4 | Functions with tests | todo |
| S6.3 | Plot helpers for sweep and profile results | S6.1 | Plots from a saved results table | todo |

### S7 — SW close

| ID | Scope | Depends | Acceptance | Status |
|---|---|---|---|---|
| S7.1 | Freeze the interfaces in ARCHITECTURE and the formats in HOUSEKEEPING | S6 | Docs match the code | todo |
| S7.3 | `docs` env and Sphinx docs for the package (D21) | S7.1 | Docs build | todo |

## Done PRs

| PR | Merged into `main` at | Tasks | Decisions |
|---|---|---|---|
| `s0-clean-slate` | _(Ryan fills in the merge commit)_ | S0.1–S0.10 | D19, D21, D22, D23, D24, D25 (D20 was replaced by D24, D7 by D25) |

## Baselines

These are old-app baselines, filled by `s0-baselines` (S0.11). Facts known about the old apps at the tag:
- All six old apps run **bipolar** HVs at dim 512, because none passes `hv_type`, so the constructor default applies. "bin" in their names refers to the input data.
- Generators: `lfsr` for five apps, `ri` for `vsax_digit_recog.py`.
- AM binarized for dna, isolet and lang; not for the digits.
- One retrain epoch on the validation split; splits 0.6 / 0.75.
- The old char self-test uses 10 classes (letters A–J), trains and tests on the same 10 samples, and scores 100%.

| App | Config (old) | Seeds | Accuracy (mean ± std, min–max) | Source |
|---|---|---|---|---|
| — | — | — | — | — |

## Open items

**Next free: 10**

1. **uint semantics (S2.1).** With multiplication binding and dot-product similarity on unsigned values:
   - Random HVs are not quasi-orthogonal, because all values are ≥ 0. For uniform values, cosine is about 0.75.
   - Multiplication can't be undone, and values grow.
   - Options: centre the values before similarity, or use addition mod q (discrete FHRR binding, as in Modular Composite Representations and residue HDC), which would double as the FHRR hook.
2. **CA90 iM variant (S3.2).** Row-by-row iteration or hierarchical expansion. The old `hdc_exp` had both. The RTL `ca90_hier_base` is hierarchical and matches the `hw_*` fixtures.
3. **CiM flavour (S3.3).** Bit flips from a seed, as in the old lib, or LFSR-chosen flip positions, as in the planned generalised `cim.sv`.
4. **Accuracy tolerance** against the old baselines (S0.11 / S4). The proposal to settle in `s0-baselines`: new mean over seeds 0–4 ≥ old mean − 2·std, and char exactly 100%.
5. **Saved-file formats for the model and results**, e.g. `.npz` with the Config as JSON inside, and results as CSV. They go in HOUSEKEEPING at S1.5. The fixture format is settled by D19.
6. **dtype per HV type** (binary uint8, bipolar int8, uint width). Goes in HOUSEKEEPING at S1.2 / S2.2.
8. **Char recognition classes (S1.6).** Keep the old self-test's 10 letters (A–J), which makes it directly comparable to the baseline, or use all 26 in `characters.txt`, which makes a harder and more useful test. The old test trains and tests on the same samples, so either way accuracy only moves in steps of 1/classes.
9. **LFSR seed 0 (S3.1).** In the old `lfsr_item_seed`, base seed 0 and item 0 give LFSR state 0, so that item is all zeros forever (fixture `s00000000_d100_n16`, row 0). Options: reproduce it (bit-exact with the old code and the RTL, if the RTL has the same path) or forbid seed 0 in the Config.
