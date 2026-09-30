# Decisions

Numbered decisions that hold across PRs. Numbers never change and are never reused. Rules for writing entries are in `docs/WORKFLOW.md`, section 2.

**Next free: D26**

## Index by area

| Area | Decisions |
|---|---|
| scope | D1, D2, D3, D4, D16, D18, D20, D23, D24 |
| env | D5, D6, D21 |
| sw | D8, D9, D10, D11, D12, D13, D14, D15 |
| hw | — |
| test | D7, D19, D25 |
| docs | D17, D22 |

## Entries

### D1 · scope · Top-level split
The top level has `sw/` (all software) and `hw/` (all hardware). `sw/` never imports from `hw/`, so the Python model stays the independent reference.

### D2 · scope · Fresh start on a rewrite branch
The SW is rewritten from scratch on a branch off `main` and merged back when the SW flow runs end to end. The old state is kept by the tag `discontinue-old-hypercorex`; v1 lives on branch `hypercorex_v1`.
Amended by D20 (branch name and PR flow). Amended by D24 (no rewrite branch: each PR merges into `main`).

### D3 · scope · HW parked at the root
`rtl/`, `tests/`, `questa/`, `Bender.yml`, `Makefile` and `conftest.py` stay at the root, untouched, until H0 moves them under `hw/`. This keeps the SW rewrite from mixing with HW changes.

### D4 · scope · What the rewrite deletes
The rewrite deletes `lib/`, `app/`, `hdc_exp/`, `hemaia/`, the old `sw/` (v1 assembler), `util/`, `requirements.txt`, `activate.sh`, the old `pixi.lock` and the old lib doc pages. All of it stays reachable at the tag.
Amended by D21 (the whole old Sphinx setup goes too).

### D5 · env · One pixi workspace
There is one pixi workspace at the root, with `default` (sw), `hw` and `docs` environments in one solve group, Python 3.12 and numpy 2.
Amended by D21 (only `default` exists until the others are needed).

### D6 · env · CPU and numpy only
numpy only, on CPU, for now. GPU support is a later milestone.

### D7 · test · CI off until S7
Said: all CI workflows stay commented out until S7, because the old ones test code the rewrite deletes.
Replaced by D25.

### D8 · sw · One Config
One `Config` dataclass holds every switch. It is saved with the model, parsed from the CLI, and it is the unit of a sweep.

### D9 · sw · Quantize instead of binarize
Binarize becomes quantize with a bit width: `encode_bits` and `am_bits`. None means full precision and 1 means binarize.

### D10 · sw · HV types as classes
An HV type is a class with bind, bundle, quantize and similarity. The first round is binary, bipolar, uint and real. intN and FHRR are hooks only.

### D11 · sw · Bipolar mapping
Binary 0 maps to +1 and binary 1 maps to −1, so XOR binding in binary matches multiplication in bipolar. The old `hv_gen_lfsr` used the opposite mapping, which is why fixtures are stored in binary form (D19).

### D12 · sw · uint binding and similarity
For uint, bind is element-wise multiplication and similarity is the dot product. This may change when open item 1 is settled.

### D13 · sw · Real HVs are float32

### D14 · sw · Named, pluggable item memories
Each app declares its item memories by name, each with its own generator (`ri`, `lfsr`, `ca90`, `cim`, later `cache`).

### D15 · sw · No compatibility with the old code
The new code does not run the old app scripts or load the `vsax_trained_models_*` files.

### D16 · scope · Vertical slice first
Char recognition goes end to end in S1. Types, item memories and apps are widened only after that.

### D17 · docs · Docs set
The repo keeps its own memory in docs rather than in chats.
Amended by D22 (adds WORKFLOW and PR.md, and fixes each doc's role).

### D18 · scope · UCI-HAR is ported
UCI-HAR is ported after the six existing apps, in S5.

### D19 · test · Old baselines and fixtures come from the tag
Old-app baselines and golden fixtures are produced from a checkout of the tag `discontinue-old-hypercorex`, so deleting old code doesn't have to wait for them.
- Fixtures are one compressed `.npz` per generator, with arrays in binary form as uint8 {0, 1} and keys named by their parameters.
- A `meta` entry holds JSON describing the old call that made each array.
- They are written by `sw/tests/fixtures/make_fixtures.py`.

Closes the fixture part of open item 5. Detail is in HOUSEKEEPING, "Formats".

### D20 · scope · Branch and PR flow
Said: a separate integration branch takes every PR, and `main` changes only at the SW close. Closed open item 7 and amended D2.
Replaced by D24.

### D21 · env · Minimal environment until needed
- S0 sets up only the `default` env: Python 3.12, numpy 2, pytest, ruff and pre-commit.
- The `hw` env comes at H0 and the `docs` env at S7. The old Sphinx setup (`docs/Makefile`, `docs/source/`, `docs/README.md`) is deleted in S0 and rebuilt at S7.3.
- Until H0, the parked HW runs from a checkout of the tag. The old task "check parked HW in the hw env" moves to H0.

A small env solves fast and only holds what the SW rewrite uses. Amends D4 and D5.

### D22 · docs · Doc roles
The docs set is `CLAUDE.md`, `docs/WORKFLOW.md`, `docs/ARCHITECTURE.md`, `docs/DECISIONS.md`, `docs/STATUS.md`, `docs/HOUSEKEEPING.md` and `docs/PR.md`.
- STATUS tracks the whole project.
- DECISIONS holds rules that span PRs.
- PR.md holds only the current PR and becomes its GitHub PR description.

This keeps long-lived state apart from one PR's plan. Amends D17. Detail is in WORKFLOW.

### D23 · scope · Plan in claude.ai, execute in Claude Code
- Planning happens in a claude.ai Project and execution in Claude Code. The two are linked only by repo files, which Ryan moves by hand.
- Claude Code starts each PR with a sync check in plan mode, then works one step at a time in the working tree and never commits or pushes. Ryan reviews, tests and commits each step.

This keeps every change of plan and every code change visible to Ryan. Detail is in WORKFLOW.

### D24 · scope · One-level PR flow into `main`
- Each PR has a name that is used for its branch (off `main`) and for its GitHub PR (into `main`), merged or squash-merged.
- `main` holds the rewrite in progress from the first merged PR on. The old state stays at the tag `discontinue-old-hypercorex`.

One level of branches is simpler, and the tag already keeps the old code. Replaces D20. Amends D2.

### D25 · test · Minimal CI from S0
- One workflow, `.github/workflows/ci.yml`, runs `pixi run test` (including the golden fixtures) and `pixi run lint`. It runs on pull requests, on pushes to `main`, and by hand.
- It installs from `pixi.lock` with `--locked`, with pixi pinned to the version used locally.
- The old workflows are deleted, not kept commented out; they stay at the tag.
- Later milestones add jobs when they need them, e.g. the docs build at S7.3.

A working CI from the start guards every PR into `main` (D24). Replaces D7.
