# Hypercorex

Hypercorex is an HDC/VSA accelerator. `sw/` is the Python model and the golden
reference; the RTL is checked against it bit for bit. The SW is being rewritten from
scratch, one PR at a time into `main` (D24); the old code stays at the tag
`discontinue-old-hypercorex`. The HW is parked at the repo root (`rtl/`, `tests/`,
`questa/`, `Bender.yml`, `Makefile`, `conftest.py`) until milestone H0.

## Read first, in this order
1. `docs/WORKFLOW.md`: how planning (claude.ai) and execution (Claude Code) work together.
2. `docs/PR.md`: the current PR. Start with its sync header and Status / Open questions.
   It exists only while a PR is in progress (D26). If it's missing, stop and ask what to
   work on.
3. `docs/DECISIONS.md`: check every change against it. Never go against a decision
   quietly; propose a new one with the next free number.
4. `docs/STATUS.md`, `docs/ARCHITECTURE.md`, `docs/HOUSEKEEPING.md` as the step needs.

## How work runs (details in WORKFLOW)
- Every PR starts with a **sync check in plan mode, no edits**:
  - Compare PR.md's sync header with the repo.
  - Verify each "Assumption to verify" (file and line).
  - Report any conflict with the code or with DECISIONS.
  - Stop and wait.
- Then do **one step at a time**:
  - Edit the working tree only; **never commit or push**.
  - Run the step's checks and only the affected block's tests.
  - Update PR.md's Status and every doc the step touches.
  - Report and stop. Ryan reviews, tests, may edit, and commits. His edits win.
- A new decision gets the next free D-number in `docs/DECISIONS.md` in the same step.
- A behaviour change, even a bug fix, never hides inside a cleanup step.

## Commands
- `pixi install`: set up the default environment.
- `pixi run smoke`: print the Python and numpy versions.
- `pixi run test`: sw tests. `pixi run lint`: ruff check and format check on `sw/`. `pixi run fmt`: format `sw/`.
- Per-block tasks (`pixi run test-hv`, `test-im`, …) are added as the blocks appear.
- There is no `hw` env until H0. The parked HW runs from a checkout of the tag
  `discontinue-old-hypercorex`.

## Conventions
- Python 3.12, numpy 2, CPU only.
- ruff format and check, line length 88.
- Type hints on public functions, numpy-style docstrings.
- Every random draw comes from a seeded `numpy.random.Generator`, never from global RNG state.
- Tests live in `sw/tests/`, one file per block. Fixtures live in `sw/tests/fixtures/`.
- Full rules are in HOUSEKEEPING.

## Guard rails (every step)
- `pixi run lint` is clean, and the sw test count only goes up. A dropped test is named, with the reason.
- `sw/` never imports from `hw/` or from the parked HW files (D1).
- The parked HW files are not touched until H0 (D3).
- The same Config and seed give identical results.
- Recorded accuracies in STATUS don't drop without a logged reason.
