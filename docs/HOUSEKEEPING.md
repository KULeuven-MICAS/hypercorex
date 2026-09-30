# Housekeeping

Rules for code, docs, formats, files and tests. The workflow itself is in `docs/WORKFLOW.md`. Sections marked TBD get filled by the milestone named.

## Commits and PRs

- Claude Code never commits or pushes. Ryan commits each step after checking it (D23).
- Commit messages: `<step ID>: <what changed>`, e.g. `S0.4: minimal pixi environment`.
- PR title: the PR name, e.g. `s0-clean-slate`. PR description: the final text of `docs/PR.md`.
- Branches: a PR branch carries the PR name, comes off `main` and merges or squash-merges back into `main` (D24).

## Python style

- Python 3.12 and numpy 2 (D5, D21).
- `ruff format` and `ruff check` on `sw/`, line length 88.
  - Rule sets: `E`, `F`, `W`, `I`, `B`, `UP`, `NPY`.
  - The config lives in `sw/pyproject.toml`.
  - The parked HW Python under `tests/` is not linted (D3).
- Type hints on every public function and method.
- numpy-style docstrings on public functions and classes.
- No global RNG state: every random draw takes a `numpy.random.Generator` built from the Config seed.
- Library code never prints; it returns values. Apps and the runner may print.
- Never change an input array in place unless the function name says so.

## Markdown style (all docs)

- Plain, everyday words. Direct, complete sentences, no filler.
- Prose by default. Use tables or lists for steps, options and comparisons.
- Write for a reader who hasn't seen any chat: give decisions with their reasons, and never write "as discussed".
- Refer to decisions as `D<n>`, to tasks by ID (`S1.3`), and to open items as "open item <n>".
- One sentence per line is not required. Keep lines readable in a diff.

## Naming

- Modules and functions use `snake_case`; classes use `CapWords`; constants use `UPPER_SNAKE`.
- Registered names (HV types, generators) are short lowercase strings: `binary`, `bipolar`, `ri`, `lfsr`, `ca90`, `cim`.
- New apps are named after the task, not the encoding trick: `digit_bin.py`, not `vsax_bin_digit_recog.py`.
- Fixture keys are named by their parameters, e.g. `s0000002a_d512_n1024` for seed `0x2a`, dim 512, 1024 items.

## Where files go

- Library code: `sw/src/hypercorex/`.
- Apps: `sw/apps/`.
- Walk-throughs: `sw/examples/<name>/README.md`.
- Tests: `sw/tests/test_<block>.py`. Shared test helpers: `sw/tests/helpers.py`.
- Golden data: `sw/tests/fixtures/`, each file listed in `sw/tests/fixtures/README.md`.
- Downloaded datasets, trained models and results: `sw/data/`, which is gitignored.
- Nothing new goes into the parked HW paths until H0 (D3).

## Formats

**Fixtures (settled, D19).**
- One `np.savez_compressed` file per generator.
- Every array is in binary form, uint8 {0, 1}, with row `i` = item `i`.
- Seed arrays are uint32.
- A `meta` entry holds a JSON string with `source_commit`, `numpy` (the version used) and, for each key, the old call that produced it.
- Fixtures are written only by `sw/tests/fixtures/make_fixtures.py`, run against a checkout of the tag. Rerunning it with the same environment gives byte-identical files.

**HV arrays and dtypes.** TBD, S1.2 / S2.2 (open item 6).

**Saved models and results.** TBD, S1.5 (open item 5). The working proposal: `.npz` with the Config as JSON inside, and results as CSV.

## Tests

- Every test is seeded, so the same run gives the same result.
- `pixi run test` needs no network. Tests that need a dataset are marked and skipped when it's missing.
- Fixtures are loaded only from `sw/tests/fixtures/`, through one helper.
- One test file per block. A pixi task `test-<block>` is added when the block appears.
- The test count only goes up. A dropped or merged test is named in PR.md with the reason.
- Numbers stated in docs or walk-throughs are checked by a test.

## Lessons from the old code

Bugs the old code had, not to repeat:
- CiM flipped bits in place, so level 0 is not the seed, every level is off by one step, and the last two levels are identical.
- `gen_type="ca90"` filled only row 0 of the orthogonal iM.
- Empty memories were `float64`, so XOR binding on them fails.
- `split_data` used an unseeded `random.shuffle` on the caller's lists, and `convert_levels` changed its input.
- Per-sample, per-class Python loops (the LFSR ran bit by bit) are too slow for sweeps.
- The "bin" apps silently ran bipolar because `hv_type` fell back to a constructor default. New code has no silent defaults for the HV type; the Config always states it.
