# Hypercorex

The Hypercorex is a semi-data flow accelerator for binary [hyperdimensional computing](https://www.hd-computing.com/home) algorithms. The architecture is built using the same principles of building a generic CPU, but tailored for very large bit-widths. It also expects data to be streamed continuously for uninterrupted processing.

Unlike typical data flow accelerators with fixed kernel operations, Hypercorex's semi-data flow architecture allows more configurability to support various encoding schemes to support state-of-the-art binary HDC operations. The key aspects are: (1) the CPU-like architecture to get as much configurability as possible, and (2) the process being able to handle data that are contuously fed into the accelerator.

More details can be found in (TODO: insert docs page here).

# Getting Started

## Requirements

- You need [Verilator v5.006](https://verilator.org/guide/latest/install.html) for the open-source simulation tool. You may also use `modelsim` for a commercial tool.

- Install all Python (3.10) requirements with:

```bash
pip install -r requirements.txt
```

- Pre-built container can be downloaded using [Docker](https://docs.docker.com/engine/install/). This already contains all the necessary intallations needed. Highly recommended to start right away.

```bash
docker pull ghcr.io/kuleuven-micas/hypercorex:main
```

## Running a Program

There are several tests in the repository. To run a sample test:

```bash
pytest tests/test_hypercorex_char_recog.py
```

You can add `--simulator=modelsim` argument to run it in `modelsim`. The default uses `verilator`. You can also add `--waves=1` to dump waveforms. The `verilator` dumps a `.vcd` file, while `modelsim` dumps a `.wlf` file. For example:

```bash
pytest tests/test_hypercorex_char_recog.py --simulator=modelsim --waves=1
```

**Notes**:
- The tests are run using [Cocotb](https://www.cocotb.org/) to handle more complex verification tasks.
- Test descriptions can be found in the (TODO: insert link to test README)

# Directory Structure
- `hdc_exp`: Contains several HDC experiments for SW. Feel free to explore how some algorithms were tested.
- `rtl`: Main directory for the RTL source files. The testbench RTL can also be found in here.
- `sw`: This is for the compiled ASMs needed to feed into the instruction memory.
- `tests`: This is where all unit and system tests for the RTL reside.
- `util`: Contains utility functions tools like the Dockerfile, and generation scripts.