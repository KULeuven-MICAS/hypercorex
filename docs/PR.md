# s0-clean-slate

```
PR: s0-clean-slate          Branch: s0-clean-slate (from main at 96b8e9e)
Next free D: 26             Next free open item: 10
Last planned: 2026-09-30, claude.ai    Last updated: 2026-09-30, Claude Code
```

## Goal

Turn the old tree into a clean base for the SW rewrite, with the docs set in place, a minimal pixi environment, the old SW deleted, and a tested `sw/` package skeleton with golden fixtures from the old code. At the end, `pixi install && pixi run test && pixi run lint` pass on the branch.

## Context

- `s0-clean-slate` comes off `main` at `96b8e9e` and merges back into `main` (D24). That commit equals the tag `discontinue-old-hypercorex`, so all old code stays reachable at the tag.
- The old SW is `lib/` (vsax library), `app/` (six apps), `hdc_exp/` (experiments and helpers), `hemaia/` (trained AMs and test samples for HW tests) and `sw/` (the v1 assembler).
- The HW is parked at the root and must not change (D3).
- The old `pixi.toml` builds a large env (verilator, cocotb, compilers) through `activate.sh`. This PR replaces it with a SW-only env (D21).
- Old-app baselines are **not** part of this PR. They come in the next PR, `s0-baselines` (S0.11).

## Decisions

- D19 — Old baselines and golden fixtures come from a checkout of the tag, so deletion doesn't wait. The fixture format is in HOUSEKEEPING, "Formats".
- D24 — One named branch per PR, off `main` and merged or squash-merged into `main`. Replaces D20. Decided at S0.2.
- D21 — Only the `default` env exists until needed. The `hw` env comes at H0 and `docs` at S7. The old Sphinx setup is deleted now.
- D22 — Doc roles: STATUS covers the whole project, DECISIONS holds rules across PRs, PR.md holds the current PR only.
- D23 — Plan in claude.ai, execute in Claude Code, one step at a time in the working tree. Claude Code never commits.
- D25 — Minimal CI from S0: one workflow runs `pixi run test` and `pixi run lint`; the old workflows are deleted. Replaces D7. Decided after S0.9 (S0.10).
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

- **A1.** Branch `s0-clean-slate` is `main` at `96b8e9e` plus one commit holding these docs.
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
- Check: `git diff --stat main` lists only these 7 files.

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
- Check: `git diff --stat main -- rtl tests questa Bender.yml Makefile conftest.py LICENSE` prints nothing.

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
- Rewrite `README.md`: what Hypercorex is; that the SW is being rewritten one PR at a time into `main`; quick start (`pixi install`, `pixi run test`); pointers to `docs/`, the tag and `hypercorex_v1`; license.
- Add `hw/README.md`: the HW moves here at H0; until then it is parked at the root; see ARCHITECTURE, "HW".
- Check: `git ls-files | cut -d/ -f1 | sort -u` now also lists `hw` and `sw`.

**S0.9 — Close.**
- Set S0.1–S0.9 to done in STATUS and add the Done-PR row (Ryan fills in the merge commit).
- Fill in this file's Status.
- Set the sync header's "Last updated".

**S0.10 — Minimal CI (D25).** Added after S0.9, at Ryan's request.
- Replace `.github/workflows/ci.yml` with one job on `ubuntu-latest`: `actions/checkout@v7`, `prefix-dev/setup-pixi@v0.10.2` with `pixi-version: v0.46.0`, which installs from the lock with `--locked` and caches the env, then `pixi run test` and `pixi run lint`. It triggers on pull requests, pushes to `main`, and `workflow_dispatch`.
- Delete `.github/workflows/docs.yml` and `lint.yml`.
- Check: `pixi install --locked`, `pixi run test` and `pixi run lint` pass locally; `actionlint` and `check-yaml` pass on `ci.yml`; CI is green on the PR into `main`.

## Definition of done

- From a clean clone of the branch, `pixi install`, `pixi run smoke`, `pixi run test` (≥ 11 passed) and `pixi run lint` (clean) all succeed.
- `git diff --stat main -- rtl tests questa Bender.yml Makefile conftest.py LICENSE` prints nothing.
- The top-level listing is exactly the `.github .gitignore .pre-commit-config.yaml Bender.yml CLAUDE.md LICENSE Makefile README.md conftest.py docs hw pixi.lock pixi.toml questa rtl sw tests`.
- Regenerating the fixtures gives byte-identical files.
- CI is green on the PR into `main`.
- STATUS shows S0.1–S0.10 as done, DECISIONS holds D1–D25 with next free D26, and this Status section is complete.

## Status / Open questions

- **S0.1: done.** Commit `3e7c62a` on `s0-clean-slate`. `git diff --stat main` lists exactly the 7 docs.
- **S0.2: done** (sync check, 2026-09-30, Claude Code). The check itself edited only this section. The D24 doc edits below followed at Ryan's request.
  - **Sync header.** "Next free D: 24" matches DECISIONS. "Next free open item: 10" matches STATUS (items 1–6, 8, 9; item 7 was closed by D20). The branch line matches the repo (`main` at `96b8e9e`). After D24, the header reads "from main at 96b8e9e" and "Next free D: 25".
  - **A1: confirmed.** `s0-clean-slate` is `main` at `96b8e9e` plus the docs commit `3e7c62a`.
  - **A2: confirmed.** This machine is `x86_64`, so `linux-64` is right.
  - **A3: confirmed.** `pixi exec --spec "python=3.11" --spec "numpy=1.26" --spec tqdm --spec matplotlib --spec requests -- python …` runs with Python 3.11.16 and numpy 1.26.4 (pixi 0.46.0). A first try hung when two pixi runs overlapped. Run alone, it takes about 50 s cold and 4 s cached.
  - **A4: confirmed.** At the tag, `hdc_exp/hdc_util.py:11-20` imports `numpy`, `tqdm`, `collections`, `matplotlib.pyplot`, `requests`, `tarfile`, `io`, `copy`, `math` and `from FP_quantize_util import fp864_quantize` at module level. `FP_quantize_util.py` imports only numpy, so the fixture script must put `hdc_exp/` on `sys.path`.
  - **A5: confirmed.** At the tag, `tests/set_parameters.py:9` is its only import (`math`), and `ORTHO_IM_SEEDS` (`:67-76`) holds 8 seeds.
  - **A6: confirmed.** In a scratch copy of the planned layout, whose root `conftest.py` raises an error when loaded, `pixi run test` reports `rootdir: sw`, `configfile: pyproject.toml` and `1 passed`. The root conftest is never loaded.
  - **A7: confirmed.** In the same copy, `ruff check sw --show-settings` reports `Settings path: sw/pyproject.toml` with `line_length = 88` and target 3.12. A probe file using `typing.List` gets UP006 and UP035.
  - **A8: confirmed.** `pixi install` of the planned `pixi.toml` and `sw/pyproject.toml` succeeds with no extra config. `hypercorex` imports from `sw/src/hypercorex/`, the metadata version is `0.0.0`, and `direct_url.json` has `"editable": true`. `pixi run smoke` prints `3.12.14 2.5.3`, and `pixi run lint` prints `All checks passed!` and `2 files already formatted`.
  - **A9: confirmed.** `git ls-tree --name-only 96b8e9e` gives exactly the planned list.
  - **S0.7 values checked early.** These come from the old code at the tag, through A3:
    - `lfsr (0x2a, 512, 1024)` mean is `0.5000152587890625`.
    - For seed 0, row 0 is all zeros and the first two start states are `[0, 3652664798]`.
    - `hw_d512_n1024` mean is `0.48775482177734375`.
    - The `iter_d512` row means match.
    - `hw_d512_n1024[k*128] == hier_d512[k]` holds for all 8 seeds.
    - `hw_d256_n512` has shape (512, 256).
    - `characters.txt` has 26 lines of 35 characters.
  - **S0.7 details for the script.**
    - `gen_ca90_im_set` returns `(seed_list, ortho_im, conf_mat)`, so the iM is element 1.
    - The old arrays come back as int32 (LFSR) and int64 (CA90). Both must be cast to uint8 (D19).
  - **Other checks.**
    - The three workflows have 118, 35 and 27 live lines now.
    - Nothing in the parked HW references `util/`, `activate.sh` or `requirements.txt`, so S0.4 and S0.5 don't break its files.
    - The old `.pixi/` env in the working tree is gitignored and gets replaced at S0.4.
- **D24 (decided at S0.2 by Ryan).** One-level PR flow: each PR branch comes off `main` and merges or squash-merges into `main`. It replaces D20 and amends D2. Edited to match:
  - DECISIONS: D2, D20, D24, the index and next free D25;
  - STATUS: "Where the code lives", S7 and the Done-PRs header;
  - HOUSEKEEPING, "Commits and PRs";
  - WORKFLOW section 3.1 and the section 5 header;
  - CLAUDE.md;
  - ARCHITECTURE, "HW";
  - in this file: the header, Context, Decisions, the S0.1 and S0.5 checks, S0.8 and the Definition of done.
- **Commit messages are free-form (Ryan, after S0.2).** HOUSEKEEPING, "Commits and PRs", no longer asks for `<step ID>: …`. Steps are tracked in this Status, and a squash merge puts only the PR title on `main`.
- **For the next planning round:** upload the updated DECISIONS, STATUS, WORKFLOW, HOUSEKEEPING, CLAUDE.md and this file, so claude.ai plans from D24.
- **S0.3: done.**
  - Every non-blank line of `ci.yml`, `docs.yml` and `lint.yml` is prefixed with `# `, blank lines are unchanged, and each file starts with `# Disabled until S7 (D7).`
  - Check: `grep -v -e '^\s*#' -e '^\s*$' .github/workflows/*.yml` prints nothing.
  - Superseded by S0.10 (D25), which replaces `ci.yml` and deletes the other two.
  - To watch after the push: an all-comment workflow file parses as empty YAML, and GitHub's Actions tab may list it as invalid. Nothing runs either way.
- **S0.4: done.**
  - `pixi.toml` is replaced with the S0.4 part of the constraint. `pixi.lock` and `activate.sh` are deleted.
  - The old 2.9 GB `.pixi/` env was deleted before the install, so the new env is built from scratch. pixi's shared package cache was reused.
  - `pixi install` (pixi 0.46.0) wrote a new `pixi.lock`: 721 lines, 114 conda packages. The env is 383 MB.
  - Check: `pixi run smoke` prints `3.12.14 2.5.3`. The tools are pytest 9.1.1, ruff 0.16.9 and pre-commit 4.6.2.
- **S0.5: done.**
  - Deleted `lib/`, `app/`, `hdc_exp/`, `hemaia/`, `sw/`, `util/`, `requirements.txt`, `docs/Makefile`, `docs/source/` and `docs/README.md`. These are 83 tracked files, all reachable at the tag. The delete list held no untracked or ignored files.
  - Check 1: with the deletions staged, the listing prints exactly the planned list. The plan's `sort -u` needs `LC_ALL=C` for that order, because an `en_US` locale ignores leading dots when sorting.
  - Check 2: `git diff --stat main -- rtl tests questa Bender.yml Makefile conftest.py LICENSE` prints nothing.
  - Expected leftovers: the parked cocotb tests still import the deleted code (ARCHITECTURE, "HW"), and `.gitignore` still names `hdc_exp/` and `docs/build/`. S0.6 replaces `.gitignore`.
- **S0.6: done.**
  - Added `sw/pyproject.toml` exactly as in the constraint, `sw/src/hypercorex/__init__.py` (docstring and `__version__ = "0.0.0"`) and `sw/tests/test_smoke.py` with 2 tests:
    - `test_version_matches_metadata`;
    - `test_numpy_major_is_at_least_2`.
  - `pixi.toml` is now the full version from the constraint, and `pixi.lock` is updated for the editable `hypercorex`.
  - `.gitignore` is replaced as planned, with the parked-HW entries under a comment.
  - `.pre-commit-config.yaml` is replaced:
    - `pre-commit-hooks` pinned at `v6.0.0`, the latest tag;
    - a local `pixi run lint` hook on `^sw/`;
    - a top-level `exclude` for the parked HW.
  - Checks:
    - `pixi install` succeeds.
    - `pixi run test` prints `rootdir: .../sw`, `configfile: pyproject.toml` and `2 passed`.
    - `pixi run lint` prints `All checks passed!` and `2 files already formatted`.
  - Pre-commit:
    - `pre-commit validate-config` passes.
    - `pre-commit run --files` on this step's files passes all 5 hooks.
    - On `conftest.py` and `Makefile`, the hooks skip ("no files to check").
    - `pre-commit install` is left to Ryan.
  - Known: `.github/workflows/docs.yml` and `lint.yml` have trailing whitespace and no final newline, and `README.md` has trailing whitespace. These come from the originals. The hooks fire only when these files are staged, and `README.md` is rewritten in S0.8.
- **S0.7: not done yet.** Ryan chose to do S0.8 first. The two are independent.
- **S0.8: done.**
  - `README.md` is rewritten: what Hypercorex is, its status (the SW rewritten one PR at a time into `main`, the HW parked), quick start (`pixi install`, `smoke`, `test`, `lint`, `fmt`), the repo layout, pointers to `docs/`, the tag, `hypercorex_v1`, and the license (Apache 2.0). The old README's cocotb, Questa and app instructions describe the deleted setup and still exist at the tag.
  - Added `hw/README.md`: the HW moves here at H0, it is parked at the root until then, and it points to ARCHITECTURE, "HW".
  - Check: with the changes staged, `git ls-files | cut -d/ -f1 | LC_ALL=C sort -u` prints `.github .gitignore .pre-commit-config.yaml Bender.yml CLAUDE.md LICENSE Makefile README.md conftest.py docs hw pixi.lock pixi.toml questa rtl sw tests`, which is the Definition of done's list.
  - The pre-commit hooks pass on both files, and every relative link resolves.
- **S0.7: done.**
  - `../hypercorex-old` is a worktree at `96b8e9e`, made with `git worktree add`. It is kept for regenerating the fixtures; remove it with `git worktree remove ../hypercorex-old`.
  - Added `sw/tests/fixtures/make_fixtures.py` (`--old` and `--out`). It is lint-clean under the `sw/` ruff rules and runs on Python 3.11.
  - Generated `lfsr_im.npz` (92 KB) and `ca90_im.npz` (99 KB) through A3: `pixi exec` with Python 3.11.16 and numpy 1.26.4.
  - Added `characters.txt` (identical to the tag's copy), the fixtures `README.md` and `sw/tests/helpers.py` with `load_fixture(name)`. The helper returns a dict of arrays for `.npz` files and text for anything else.
  - Added `sw/tests/test_fixtures.py`. It covers the 9 planned checks and adds `test_ca90_means`, which checks the recorded `hw_d512_n1024` and `iter_d512` means, so every number stated in this plan has a test (HOUSEKEEPING, "Tests"). The meta check runs once per file.
  - Test count: 13, not 11. The extras are `test_ca90_means` and the second `test_meta` case; no test was dropped.
  - `meta` keeps the calls under a `calls` key. HOUSEKEEPING, "Formats", is updated to say so.
  - Checks:
    - `pixi run test` gives `13 passed`.
    - `pixi run lint` gives `All checks passed!` and `5 files already formatted`.
    - Regenerating into a temp dir and running `cmp` on both `.npz` files prints nothing.
    - The pre-commit hooks pass on every new file.
- **S0.9: done.**
  - STATUS: S0.1–S0.9 are set to done, and the Done-PR row is added. Ryan fills in the merge commit. S0 stays `wip` until `s0-baselines` (S0.11).
  - The sync header's "Last updated" is `2026-09-30, Claude Code`.
- **Definition of done: met.** Checked on a fresh clone of `s0-clean-slate` at `7ce7f2e`, in a scratch directory:
  - `pixi install` succeeds and leaves `pixi.lock` unchanged. `pixi run smoke` prints `3.12.14 2.5.3`, `pixi run test` gives `13 passed`, and `pixi run lint` gives `All checks passed!` and `6 files already formatted`. Ruff 0.16 also checks `sw/tests/fixtures/README.md`, which is why the count is 6.
  - `git diff --stat main -- rtl tests questa Bender.yml Makefile conftest.py LICENSE` prints nothing.
  - The top-level listing, with `LC_ALL=C` sorting, is exactly the list in the Definition of done.
  - Regenerating the fixtures from `../hypercorex-old` gives byte-identical `.npz` files: `cmp` prints nothing.
  - STATUS showed S0.1–S0.9 as done. DECISIONS held D1–D24, next free D25. S0.10 was added after this check.
- **For the next planning round (`s0-baselines`):**
  - Upload CLAUDE.md, DECISIONS, STATUS, WORKFLOW, HOUSEKEEPING, ARCHITECTURE and this file. D24 (the one-level flow into `main`), D25 (minimal CI, replacing D7), the free-form commit messages and the renumbering of the old-app baselines from S0.10 to S0.11 are new since the plan.
  - `../hypercorex-old` (a worktree at the tag) and the A3 `pixi exec` command both work, so S0.11 can run the old apps the same way.
  - Check commands that sort file names should use `LC_ALL=C sort`, so the order doesn't depend on locale.
  - `pre-commit install` is Ryan's choice. The hooks are set up but not installed.
- **S0.10: done locally, waiting for CI.** Added after S0.9 at Ryan's request, with D25 replacing D7.
  - `.github/workflows/ci.yml` now holds one `sw` job: checkout, `setup-pixi` (pixi v0.46.0, locked install, cache), `pixi run test` and `pixi run lint`. It triggers on pull requests, pushes to `main` and by hand. `docs.yml` and `lint.yml` are deleted; the old versions stay at the tag.
  - The old-app baselines task is renumbered from S0.10 to S0.11 in STATUS, in this file's Context, and in open item 4 and S1.6. S7.2 ("minimal CI back on") is removed from STATUS, and "CI back on" is removed from S7's scope. ARCHITECTURE's layout shows `ci.yml` (D25).
  - Checks:
    - `pixi install --locked` succeeds, `pixi run test` gives `13 passed`, and `pixi run lint` gives `All checks passed!` and `6 files already formatted`.
    - `check-yaml` passes on `ci.yml`, and so does `actionlint` (run through `pixi exec`).
  - Still to confirm: CI is green on the PR into `main`. STATUS keeps S0.10 as `wip` until then.
