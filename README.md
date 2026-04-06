# :electron: Hypercorex-v2 (VSAX)

## :hammer_and_wrench: Under Construction

This project contains ongoing development for Hypercorex version 2. It is a VSA (vector-symbolic architecture) variant, in contrast to the original [binary HDC variant](https://github.com/KULeuven-MICAS/hypercorex/tree/hypercorex_v1).

## What's so special about VSAX?

This project addresses the key limitations of binary HDC, where accuracy suffers due to restricted information capacity. The core idea is to move to non-binary representations, which offer richer information encoding. However, non-binary representations introduce significant computational costs for high-dimensional dense vectors. We tackle this challenge through on-the-fly generation of item memories and an efficient associative memory search.

As the VSA field continues to evolve, this hardware framework is designed to be extensible across both the hardware and software domains. Throughout these expansions, the focus remains on building an efficient and scalable VSA accelerator.

## Getting Started
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





## :book: Development Checklist
### General House Keeping
- [ ] Setting general pixi shell.
- [ ] Updating documentation.
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


