# :electron: Hypercorex-v2 (VSAX)

## :hammer_and_wrench: Under Construction

This project contains ongoing development for Hypercorex version 2. It is a VSA (vector-symbolic architecture) variant, in contrast to the original [binary HDC variant](https://github.com/KULeuven-MICAS/hypercorex/tree/hypercorex_v1).

## What's so special about VSAX?

This project addresses the key limitations of binary HDC, where accuracy suffers due to restricted information capacity. The core idea is to move to non-binary representations, which offer richer information encoding. However, non-binary representations introduce significant computational costs for high-dimensional dense vectors. We tackle this challenge through on-the-fly generation of item memories and an efficient associative memory search.

As the VSA field continues to evolve, this hardware framework is designed to be extensible across both the hardware and software domains. Throughout these expansions, the focus remains on building an efficient and scalable VSA accelerator.

## Initial Pixi Shell Setup
VSAX uses [pixi-shell](https://pixi.prefix.dev/v0.28.1/) as its environment manager. Make sure to install pixi first:

```bash
curl -fsSL https://pixi.sh/install.sh | sh
```

Clone the repo and make sure to be inside:

```bash
git clone git@github.com:KULeuven-MICAS/hypercorex.git
```

Install the pixi environment. For more details of the versions used, please check the [pixi.toml](./pixi.toml).

```bash
pixi install
```

Activate the pixi shell.

```bash
pixi shell
```

Run the smoke-test to see if it works.

```bash
pixi run smoke-test
```

## Running Sample HW Testbenches

By default, we use [cocotb-test](https://github.com/themperek/cocotb-test) while using [Verilator](https://www.veripool.org/verilator/) as our testbench since it uses Python as the backend and simulations are fast.

You can select one of the tests from the `tests` directory. To invoke a test use:

```bash
pytest tests/test_bundler_unit.py
```

To display a log of what the test looks like, add `-o log_cli=True` arguments.

```bash
pytest tests/test_bundler_unit.py -o log_cli=True
```

If you want to dump waveforms, please add the `--waves=1` argument.

```bash
pytest tests/test_bundler_unit.py --waves=1 -o log_cli=True
```

This will create a `dump.vcd` file inside the `tests/sim_build/<path to designated test bench>` which you can view with:

```bash
gtkwave tests/sim_build/bundler_unit/dump.vcd
```

Make sure you have [gtkwave](https://github.com/gtkwave/gtkwave) installed. 

## Running with Commercial Tools

VSAX currently supports the use of questasim, so make sure to have the proper questasim installation. Make sure you are inside the pixi environment. To invoke questasim simply add the `--simulator=questa` argument:

```bash
pytest tests/test_bundler_unit.py --simulator=questa -o log_cli=True
```

You can also view waveforms but questasim dumps `vsim.wlf` waveform which you can read with `vsim vsim.wlf`.

```bash
pytest tests/test_bundler_unit.py --simulator=questa -o --waves=1 log_cli=True
```

## :book: Development Checklist
### General House Keeping
- [x] Setting general pixi shell.
- [x] Updated pixi shell with correct cocotb and verilator versions that enable correct waveform viewing.
- [x] Updating README documentation with getting started steps.
### Software Development
- [ ] Improving SW VSA model generation.
- [ ] Creating expansion of VSA models to include data-type conversions.
- [ ] Enabling customization flows for non-streaming VSA processes.
### Hardware Development
- [ ] Creating comparison suite for different item-memory generators.
- [ ] Creating multi-input HV ALU system.
- [ ] Creating `int8` associative memory search.
- [ ] Synthesis scripts.
- [ ] PnR scripts.


