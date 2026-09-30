# Hypercorex

Hypercorex is a hardware accelerator for hyperdimensional computing (HDC) and
vector-symbolic architectures (VSA). It moves beyond binary HDC, whose accuracy is
limited by how little each dimension can hold, to non-binary representations. To keep
the cost of large, dense hypervectors down, it generates item memories on the fly and
uses an efficient associative-memory search.

The Python model in `sw/` is the golden reference: the RTL is checked against it bit for
bit.

## Status

The software is being rewritten from scratch, one pull request at a time into `main`.
The hardware is parked at the repo root (`rtl/`, `tests/`, `questa/`, `Bender.yml`,
`Makefile`, `conftest.py`) and moves into `hw/` later. Progress and the plan are in
[`docs/STATUS.md`](docs/STATUS.md).

## Quick start

Install [pixi](https://pixi.sh):

```bash
curl -fsSL https://pixi.sh/install.sh | sh
```

Clone the repo and set up the environment:

```bash
git clone git@github.com:KULeuven-MICAS/hypercorex.git
cd hypercorex
pixi install
```

Run the checks:

```bash
pixi run smoke   # prints the Python and numpy versions
pixi run test    # software tests
pixi run lint    # ruff check and format check on sw/
```

`pixi run fmt` formats `sw/`.

## Repository layout

| Path | Contents |
|---|---|
| `sw/` | The `hypercorex` Python package (`sw/src/hypercorex/`) and its tests (`sw/tests/`) |
| `hw/` | Placeholder; the hardware moves here later |
| `rtl/`, `tests/`, `questa/` | The parked hardware: RTL, cocotb tests and Questa files |
| `docs/` | Project docs, listed below |

## Docs

- [`docs/STATUS.md`](docs/STATUS.md): milestones, planned tasks and baselines.
- [`docs/ARCHITECTURE.md`](docs/ARCHITECTURE.md): components and their interfaces.
- [`docs/DECISIONS.md`](docs/DECISIONS.md): numbered decisions and their reasons.
- [`docs/HOUSEKEEPING.md`](docs/HOUSEKEEPING.md): code style, formats and file locations.
- [`docs/WORKFLOW.md`](docs/WORKFLOW.md): how the work is planned and carried out.
- [`docs/PR.md`](docs/PR.md): the current pull request.

## Earlier versions

- The code from before the rewrite, including the old apps, the `vsax` library and
  the old hardware setup, is at the tag
  [`discontinue-old-hypercorex`](https://github.com/KULeuven-MICAS/hypercorex/tree/discontinue-old-hypercorex):

  ```bash
  git checkout discontinue-old-hypercorex
  ```

- The original binary HDC accelerator lives on the branch
  [`hypercorex_v1`](https://github.com/KULeuven-MICAS/hypercorex/tree/hypercorex_v1).

## License

Apache License 2.0. See [`LICENSE`](LICENSE).
