"""
Copyright 2024 KU Leuven
Ryan Antonio <ryan.antonio@esat.kuleuven.be>

Description:
This test verifies the functionality of the ID-level encoder.
Although it is a fixed design, it is sufficient to simulate the encoding function.
"""

from util import setup_and_run, clock_and_time

import cocotb
from cocotb.clock import Clock
import pytest
import numpy as np
import os
import sys

# Importing main lib library
curr_dir = os.path.dirname(os.path.abspath(__file__))
lib_path = curr_dir + "/../lib"

sys.path.append(lib_path)

# Importing VSAX libraries
import vsax  # noqa: E402

# Global parameters
HV_DIMENSION = 128
COUNTER_WIDTH = 8
NUM_INPUTS = 4
HV_TYPE = "binary"
NUM_ITEMS = 100

BASE_SEED1 = 42
BASE_SEED2 = 143

NUM_TESTS = 20

# Generate a set of random hypervectors
id_set = vsax.hv_gen_orthogonal_im(
    num_items=NUM_ITEMS,
    hv_size=HV_DIMENSION,
    hv_type=HV_TYPE,
    gen_lfsr_base_seed=BASE_SEED1,
)

level_set = vsax.hv_gen_orthogonal_im(
    num_items=NUM_ITEMS,
    hv_size=HV_DIMENSION,
    hv_type=HV_TYPE,
    gen_lfsr_base_seed=BASE_SEED2,
)


def hv_to_int(hv: np.ndarray) -> int:
    """Convert a binary hypervector (1D numpy array of 0s/1s) to an integer."""
    return int(np.packbits(hv, bitorder="big").tobytes().hex(), 16)


# Load input HVs of num inputs size
async def load_inputs(dut):
    # Make list of random indices
    id_indices = np.random.choice(NUM_ITEMS, NUM_INPUTS, replace=False)
    level_indices = np.random.choice(NUM_ITEMS, NUM_INPUTS, replace=False)
    bundled_hv = vsax.hv_gen_empty(HV_DIMENSION)
    for i in range(NUM_INPUTS):
        # Load vectors
        id_hv = id_set[id_indices[i]]
        level_hv = level_set[level_indices[i]]
        dut.hv_id_i[i].value = hv_to_int(id_hv)
        dut.hv_level_i[i].value = hv_to_int(level_hv)
        # Get XOR of them as expected output
        xor_hv = vsax.hv_bind(id_hv, level_hv)
        # Convert back to bipolar
        bundled_hv += (-2 * xor_hv) + 1
    dut.valid_i.value = (1 << NUM_INPUTS) - 1
    await clock_and_time(dut.clk_i)
    dut.valid_i.value = 0
    return bundled_hv


async def clear_bundler(dut):
    dut.clr_i.value = 1
    await clock_and_time(dut.clk_i)
    dut.clr_i.value = 0


def clear_inputs_no_clock(dut):
    for i in range(NUM_INPUTS):
        dut.hv_id_i[i].value = 0
        dut.hv_level_i[i].value = 0
    dut.valid_i.value = 0
    dut.clr_i.value = 0


@cocotb.test()
async def id_level_encoder_dut(dut):
    cocotb.log.info(" ------------------------------------------ ")
    cocotb.log.info("         Testing ID-Level Encoder           ")
    cocotb.log.info(" ------------------------------------------ ")

    clear_inputs_no_clock(dut)
    dut.rst_ni.value = 0

    clock = Clock(dut.clk_i, 10, units="ns")
    cocotb.start_soon(clock.start(start_high=False))

    await clock_and_time(dut.clk_i)
    dut.rst_ni.value = 1

    # Iterate through a number of tests
    for i in range(NUM_TESTS):
        # Randomized number of loads
        num_loads = np.random.randint(1, NUM_ITEMS + 1)
        print(f"Test {i+1}/{NUM_TESTS}: Loading {num_loads} input sets...")

        # Accumulate expected bundled HV over all loads
        expected_bundled_hv = vsax.hv_gen_empty(HV_DIMENSION)
        for _ in range(num_loads):
            expected_bundled_hv += await load_inputs(dut)
        expected_bundled_hv = expected_bundled_hv[::-1]
        # Read actual bundled HV from DUT output
        actual_bundled_hv = np.array(
            [dut.hv_encoded_o[j].value.signed_integer for j in range(HV_DIMENSION)]
        )

        # Compare expected and actual bundled hypervectors
        assert np.array_equal(
            expected_bundled_hv, actual_bundled_hv
        ), f"Expected: {expected_bundled_hv}, Actual: {actual_bundled_hv}"

        # Clear bundler first before next test
        await clear_bundler(dut)

    for _ in range(5):
        await clock_and_time(dut.clk_i)


# Config and run
@pytest.mark.parametrize(
    "parameters",
    [
        {
            "HVDimension": str(HV_DIMENSION),
            "NumInputs": str(NUM_INPUTS),
            "CounterWidth": str(COUNTER_WIDTH),
        },
    ],
)
def test_id_level_encoder(simulator, parameters, waves):
    verilog_sources = [
        "/rtl/common/adder_tree.sv",
        "/rtl/encoder/multi_in_bundler_unit.sv",
        "/rtl/encoder/multi_in_bundler_set.sv",
        "/rtl/encoder/id_level_encoder.sv",
    ]

    toplevel = "id_level_encoder"
    module = "test_id_level_encoder"

    setup_and_run(
        verilog_sources=verilog_sources,
        toplevel=toplevel,
        module=module,
        simulator=simulator,
        parameters=parameters,
        waves=waves,
    )
