# s0-clean-slate

```
PR: s0-clean-slate          Branch: s0-clean-slate (from 96b8e9e)
Next free D: 24             Next free open item: 10
Last planned: 2026-09-30, claude.ai    Last updated: 2026-09-30, claude.ai
```

## Goal

Turn the old tree into a clean base for the SW rewrite, with the docs set in place, a minimal pixi environment, the old SW deleted, and a tested `sw/` package skeleton with golden fixtures from the old code. At the end, `pixi install && pixi run test && pixi run lint` pass on the branch.

## Context

- `v2` starts at `96b8e9e`. That commit equals the tag `discontinue-old-hypercorex`, so all old code stays reachable at the tag.
- The old SW is `lib/` (vsax library), `app/` (six apps), `hdc_exp/` (experiments and helpers), `hemaia/` (trained AMs and test samples for HW tests) and `sw/` (the v1 assembler).
- The HW is parked at the root and must not change (D3).
- The old `pixi.toml` builds a large env (verilator, cocotb, compilers) through `activate.sh`. This PR replaces it with a SW-only env (D21).
- Old-app baselines are **not** part of this PR. They come in the next PR, `s0-baselines` (S0.10).

## Decisions

- D19 — Old baselines and golden fixtures come from a checkout of the tag, so deletion doesn't wait. The fixture format is in HOUSEKEEPING, "Formats".
- D20 — `v2` is the integration branch; one named branch and one PR per piece of work into `v2`; `main` untouched until S7.4.
- D21 — Only the `default` env exists until needed. The `hw` env comes at H0 and `docs` at S7. The old Sphinx setup is deleted now.
- D22 — Doc roles: STATUS covers the whole project, DECISIONS holds rules across PRs, PR.md holds the current PR only.
- D23 — Plan in claude.ai, execute in Claude Code, one step at a time in the working tree. Claude Code never commits.
- PR-local — CI files are commented out, not deleted, so S7.2 can start from them.
- PR-local — Pre-commit hooks exclude the parked HW paths, so a hook can never touch them (D3).
- PR-local — Fixture set. It covers the one parked RTL LFSR test config, the app config, odd-dim and edge seeds, and the CA90 configs the parked RTL test uses. RI and CiM get no fixtures: RI can't match a new `Generator` stream, and the old CiM is buggy (HOUSEKEEPING, "Lessons").
  - `lfsr_im.npz`: seeds/dims/items (0x2a, 128, 32), (0x2a, 512, 1024), (0x0, 100, 16), (0xffffffff, 100, 16), (0x1234abcd, 100, 16), plus the LFSR start state per item.
  - `ca90_im.npz`: the HW iM at (512, 1024) and (256, 512), row-by-row and hierarchical expansions at 512 for the 8 HW seeds, and the seeds themselves.

## Constraints & interfaces

- **Files that must not change:** `rtl/`, `tests/`, `questa/`, `Bender.yml`, `Makefile`, `conftest.py`, `LICENSE`.
- **`pixi.toml` after S0.6** (platform per assumption A2):

  ```toml
  [workspace]
  name = "hypercorex"
  channels = ["conda-forge"]
  platforms = ["linux-64"]

  [dependencies]
  python = "3.12.*"
  numpy = ">=2,<3"
  pytest = ">=8"
  ruff = ">=0.6"
  pre-commit = ">=3"

  [pypi-dependencies]
  hypercorex = { path = "sw", editable = true }

  [tasks]
  smoke = "python -c \"import sys, numpy; print(sys.version.split()[0], numpy.__version__)\""
  test = "pytest sw/tests"
  lint = "ruff check sw && ruff format --check sw"
  fmt = "ruff format sw && ruff check --fix sw"
  ```
  S0.4 has everything except `[pypi-dependencies]`, `test`, `lint` and `fmt`.
- **`sw/pyproject.toml`:**
  - project `hypercorex`, version `0.0.0`, `requires-python = ">=3.12"`, dependency `numpy>=2`;
  - build backend hatchling, with src layout (`packages = ["src/hypercorex"]`);
  - ruff: line length 88, target `py312`, rules `E F W I B UP NPY`;
  - pytest: `testpaths = ["tests"]`.
- **Fixture file format:** as in HOUSEKEEPING, "Formats". The keys are listed in S0.7.
- **The fixture script** runs against the old code in a temporary Python 3.11 / numpy 1.26 env. It is never run by `pixi run test`.

## Assumptions to verify against the code

- **A1.** Branch `v2` is at `96b8e9e`, and `s0-clean-slate` is `v2` plus one commit holding these docs.
- **A2.** The platform Ryan runs pixi on. It is `linux-64` in the plan; add `osx-arm64` or others if needed.
- **A3.** `pixi exec --spec "python=3.11" --spec "numpy=1.26" --spec tqdm --spec matplotlib --spec requests -- python …` runs a script in a temporary env. Fallback: a throwaway venv with `pip install "numpy<2" tqdm matplotlib requests`.
- **A4.** At the tag, `hdc_exp/hdc_util.py` imports `matplotlib`, `requests`, `tqdm` and the local `FP_quantize_util` at module level, which is why A3 needs those packages. claude.ai checked this at the tag.
- **A5.** At the tag, `tests/set_parameters.py` imports only `math` and defines `ORTHO_IM_SEEDS` with 8 seeds. claude.ai checked this.
- **A6.** `pytest sw/tests` run from the root uses `sw/pyproject.toml` as its config, so the root `conftest.py` (parked) is not loaded.
- **A7.** `ruff check sw` run from the root picks up `[tool.ruff]` from `sw/pyproject.toml`.
- **A8.** pixi installs `hypercorex = { path = "sw", editable = true }` with hatchling without extra config.
- **A9.** The tracked top level at `96b8e9e` is: `.github .gitignore .pre-commit-config.yaml Bender.yml LICENSE Makefile README.md activate.sh app conftest.py docs hdc_exp hemaia lib pixi.lock pixi.toml questa requirements.txt rtl sw tests util`.

## Steps

Stop after each step for Ryan to check and commit.

**S0.1 — Context docs.** Ryan adds and commits the docs set: `CLAUDE.md`, `docs/WORKFLOW.md`, `ARCHITECTURE.md`, `DECISIONS.md`, `STATUS.md`, `HOUSEKEEPING.md` and `PR.md`.
- Check: `git diff --stat v2` lists only these 7 files.

**S0.2 — Sync check** (plan mode, no edits except this file's Status). Follow WORKFLOW section 3, step 5, and report on A1–A9.

**S0.3 — CI off (D7).** Comment out every line of `.github/workflows/ci.yml`, `docs.yml` and `lint.yml`, and add a first line `# Disabled until S7 (D7).`
- Check: `grep -v -e '^\s*#' -e '^\s*$' .github/workflows/*.yml` prints nothing.

**S0.4 — Minimal pixi (D21).**
- Replace `pixi.toml` with the S0.4 part of the constraint above.
- Delete `pixi.lock` and `activate.sh`.
- Run `pixi install` to make the new lock.
- Check: `pixi run smoke` prints `3.12.<x> 2.<y>.<z>`.

**S0.5 — Delete old SW (D4, D21).** Delete `lib/`, `app/`, `hdc_exp/`, `hemaia/`, `sw/`, `util/`, `requirements.txt`, `docs/Makefile`, `docs/source/` and `docs/README.md`.
- Check: `git ls-files | cut -d/ -f1 | sort -u | tr '\n' ' '` prints `.github .gitignore .pre-commit-config.yaml Bender.yml CLAUDE.md LICENSE Makefile README.md conftest.py docs pixi.lock pixi.toml questa rtl tests`.
- Check: `git diff --stat v2 -- rtl tests questa Bender.yml Makefile conftest.py LICENSE` prints nothing.

**S0.6 — `sw/` skeleton.**
- Add:
  - `sw/pyproject.toml`;
  - `sw/src/hypercorex/__init__.py`, with a module docstring and `__version__ = "0.0.0"`;
  - `sw/tests/test_smoke.py`, with two tests: the package imports and `__version__` equals the installed metadata version; numpy's major version is ≥ 2;
  - the full `pixi.toml` from the constraint.
- Replace `.gitignore` with `__pycache__/`, `.pixi/`, `.pytest_cache/`, `.ruff_cache/`, `*.egg-info/`, `sw/data/`, and, kept for the parked HW, `sim_build/` and `Bender.lock`.
- Replace `.pre-commit-config.yaml` with:
  - `pre-commit-hooks` (`check-yaml`, `check-toml`, `end-of-file-fixer`, `trailing-whitespace`);
  - a local hook running `pixi run lint` on `^sw/`;
  - a top-level `exclude` for `^(rtl|tests|questa)/` and `^(Bender.yml|Makefile|conftest.py)$`.
- Check: `pixi install`; then `pixi run test` gives `2 passed`; then `pixi run lint` gives `All checks passed!` and "already formatted".

**S0.7 — Golden fixtures (D19).**
- Write `sw/tests/fixtures/make_fixtures.py` (arguments `--old <checkout>` and `--out <dir>`). It imports the old `lib/vsax.py`, `hdc_exp/hdc_util.py` and `tests/set_parameters.py` from the checkout and writes:
  - **`lfsr_im.npz`:**
    - For each case (seed, dim, n): key `s{seed:08x}_d{dim}_n{n}` = `vsax.hv_gen_orthogonal_im(num_items=n, hv_size=dim, hv_type="binary", gen_type="lfsr", gen_lfsr_base_seed=seed)` as uint8.
    - Key `start_<same>` = `[vsax.lfsr_item_seed(seed, i) for i in range(n)]` as uint32.
  - **`ca90_im.npz`:**
    - `seeds` = `ORTHO_IM_SEEDS` as uint32.
    - `hw_d{dim}_n{n}` = the iM from `hdc_util.gen_ca90_im_set(32, dim, n, dim // 4, base_seeds=seeds, gen_seed=True)` for (512, 1024) and (256, 512).
    - `iter_d512` and `hier_d512` = `gen_hv_ca90_iterate_rows` / `gen_hv_ca90_hierarchical_rows(numbin2list(seed, 32), 512)`, one row per seed.
  - **Both files:** a `meta` JSON string with `source_commit`, `numpy`, and the old call for each non-`start_`, non-`seeds` key.
- Also add:
  - `sw/tests/fixtures/characters.txt`, copied with `git show discontinue-old-hypercorex:hdc_exp/data_set/char_recog/characters.txt`;
  - `sw/tests/fixtures/README.md`, listing each file, its keys, the command that made it and the source commit;
  - `sw/tests/helpers.py` with `load_fixture(name)`.
- Generate the fixtures:
  1. `git worktree add ../hypercorex-old discontinue-old-hypercorex`
  2. Run the script via A3 with `--old ../hypercorex-old --out sw/tests/fixtures`.
- Add `sw/tests/test_fixtures.py`, with at least these 9 tests:
  1. `lfsr_im.npz` has exactly the expected keys.
  2. Every iM array is uint8 with values in {0, 1} and shape (n, dim) from its key.
  3. Every `start_*` array is uint32 with shape (n,).
  4. `s0000002a_d512_n1024.mean()` equals `0.5000152587890625` exactly.
  5. `s00000000_d100_n16[0]` is all zeros, and `start_s00000000_d100_n16[:2]` equals `[0, 3652664798]` (open item 9).
  6. `ca90_im.npz` keys and shapes: `hw_d512_n1024` (1024, 512), `hw_d256_n512` (512, 256), `iter_d512` and `hier_d512` (8, 512), `seeds` (8,).
  7. For k in 0..7, `hw_d512_n1024[k*128]` equals `hier_d512[k]`.
  8. `meta` parses as JSON and has `source_commit`, `numpy` and one entry per array key (excluding `start_*` and `seeds`).
  9. `characters.txt` has 26 lines of 35 characters, each `0` or `1`.
- Expected values, from claude.ai's run with numpy 1.26.4 at the tag:
  - `hw_d512_n1024.mean()` = `0.48775482177734375`;
  - `iter_d512.mean(axis=1)` = `[0.5234375, 0.4609375, 0.5, 0.5234375, 0.4609375, 0.5, 0.5234375, 0.4609375]`.
- Check: `pixi run test` gives `11 passed`, and `pixi run lint` is clean.
- Check: rerunning the script into a temp dir and running `cmp` against both `.npz` files prints nothing.

**S0.8 — README and `hw/` placeholder.**
- Rewrite `README.md`: what Hypercorex is; that the SW is being rewritten on `v2`; quick start (`pixi install`, `pixi run test`); pointers to `docs/`, the tag and `hypercorex_v1`; license.
- Add `hw/README.md`: the HW moves here at H0; until then it is parked at the root; see ARCHITECTURE, "HW".
- Check: `git ls-files | cut -d/ -f1 | sort -u` now also lists `hw` and `sw`.

**S0.9 — Close.**
- Set S0.1–S0.9 to done in STATUS and add the Done-PR row (Ryan fills in the merge commit).
- Fill in this file's Status.
- Set the sync header's "Last updated".

## Definition of done

- From a clean clone of the branch, `pixi install`, `pixi run smoke`, `pixi run test` (≥ 11 passed) and `pixi run lint` (clean) all succeed.
- `git diff --stat v2 -- rtl tests questa Bender.yml Makefile conftest.py LICENSE` prints nothing.
- The top-level listing is exactly the `.github .gitignore .pre-commit-config.yaml Bender.yml CLAUDE.md LICENSE Makefile README.md conftest.py docs hw pixi.lock pixi.toml questa rtl sw tests`.
- Regenerating the fixtures gives byte-identical files.
- STATUS shows S0.1–S0.9 as done, DECISIONS holds D1–D23 with next free D24, and this Status section is complete.

## Status / Open questions

- S0.1: done once Ryan commits this file.
- Next: S0.2, the sync check.
