"""
  Copyright 2024 KU Leuven
  Ryan Antonio <ryan.antonio@esat.kuleuven.be>

  Description:
  This tests the vectorized bundler unit
"""


import set_parameters
from util import get_root, setup_and_run, gen_rand_bits, clock_and_time

import cocotb
from cocotb.clock import Clock
import numpy as np
import sys
import pytest
import random

# Add hdc utility functions
hdc_util_path = get_root() + "/hdc_exp/"
print(hdc_util_path)
sys.path.append(hdc_util_path)

from hdc_util import binarize_hv  # noqa: E402

"""
    Some useful local parameters
"""

UNSIGNED_MAX = int(2 ** (set_parameters.BUNDLER_COUNT_WIDTH) - 1)
UNSIGNED_MAX_HALF = int(UNSIGNED_MAX / 2)

"""
    Test functions
"""


# Convert a number in binary to a list
# Used to feed each bundler unit
def numbip2list(numbin, dim):
    # Convert binary inputs first
    bin_hv = np.array(list(map(int, format(numbin, f"0{dim}b"))))
    # Get marks that have 0s
    mask = bin_hv == 0
    # Convert 0s to -1s
    bin_hv[mask] = -1
    return bin_hv


# Set inputs to 0
def clear_inputs_no_clock(dut):
    dut.hv_i.value = 0
    dut.valid_i.value = 0
    dut.clr_i.value = 0
    return


# Load the hypervector into the bundler
def load_hv_bundler(dut, hv):
    dut.hv_i.value = hv
    dut.valid_i.value = 1
    return


# For clearing bundler unit
async def clear_bundler_unit(dut):
    dut.clr_i.value = 1
    await clock_and_time(dut.clk_i)
    dut.clr_i.value = 0
    return


# Checking each input of the bundler
def check_bundler_out(dut, hv_bundle, hv_dim, counter_width):
    # Iterate through number of elements
    for i in range(hv_dim):
        bundler_val = dut.counter_o.value[
            (i * counter_width) : ((i + 1) * counter_width) - 1
        ].signed_integer
        actual_val = int(hv_bundle[i])
        assert bundler_val == actual_val, "Error! Bundler output is incorrect."
        cocotb.log.info(
            f"Bundler {i}: Actual output: {actual_val}; Golden output: {bundler_val}"
        )

    return


# Checking the binarized output of each bundler unit
def check_binarize_out(dut, hv_bundle):
    # Taken from hdc_util in hdc_exp directory
    # Get golden binarized value, note that we used hv_bundle
    # as if it were bipolar, but the output is binary
    # so we set the threshold to 0 but the expected outputs
    # are in binary
    hv_binarized = binarize_hv(hv_bundle, 0)

    # Extract actual data
    actual_val = dut.binarized_hv_o.value.integer

    # Convert binarized output
    golden_val = "".join(hv_binarized.astype(str))
    golden_val = int(golden_val, 2)

    # Log
    cocotb.log.info(
        f"Binarize check! Actual output: {actual_val}; Golden output: {golden_val}"
    )

    assert (
        golden_val == actual_val
    ), f"Error! Actual output: {actual_val}; Golden output: {golden_val}"

    return


"""
    Actual test routines
"""


@cocotb.test()
async def bundler_set_dut(dut):
    cocotb.log.info(" ------------------------------------------ ")
    cocotb.log.info("             Testing Bunder Set             ")
    cocotb.log.info(" ------------------------------------------ ")

    # Initialize input values
    clear_inputs_no_clock(dut)
    dut.rst_ni.value = 0

    # Initialize clock always
    clock = Clock(dut.clk_i, 10, units="ns")
    cocotb.start_soon(clock.start(start_high=False))

    # Wait one cycle for reset
    await clock_and_time(dut.clk_i)

    dut.rst_ni.value = 1

    cocotb.log.info(" ------------------------------------------ ")
    cocotb.log.info("            Testing Increments              ")
    cocotb.log.info(" ------------------------------------------ ")

    # Do this for N number of TEST_RUNS
    for i in range(set_parameters.TEST_RUNS):
        # Working equations
        # Local test parameters
        NUM_BUNDLES = random.randint(0, UNSIGNED_MAX_HALF)

        # Initialize empty bundler vector
        hv_bundle = np.zeros(set_parameters.HV_DIM)

        # Accumulate with random hypervectors
        for i in range(NUM_BUNDLES):
            # Generate random HV
            hv = gen_rand_bits(set_parameters.HV_DIM)
            # Convert that to bipolar so we can simply
            # add the hvs normally
            hv_bundle += numbip2list(hv, set_parameters.HV_DIM)
            # Load the the binary hypervector
            load_hv_bundler(dut, hv)
            # Wait for the time
            await clock_and_time(dut.clk_i)

        # Clear outputs
        clear_inputs_no_clock(dut)

        # Check result per bundler
        check_bundler_out(
            dut, hv_bundle, set_parameters.HV_DIM, set_parameters.BUNDLER_COUNT_WIDTH
        )

        cocotb.log.info(" ------------------------------------------ ")
        cocotb.log.info("           Testing Binarization             ")
        cocotb.log.info(" ------------------------------------------ ")

        # Check result per bundler
        check_binarize_out(dut, hv_bundle)

        cocotb.log.info(" ------------------------------------------ ")
        cocotb.log.info("               Testing Clear                ")
        cocotb.log.info(" ------------------------------------------ ")

        # Clear bundler set
        await clear_bundler_unit(dut)

        # Re-initialize bundler to zeros
        hv_bundle = np.zeros(set_parameters.HV_DIM)

        # Check result per bundler
        check_bundler_out(
            dut, hv_bundle, set_parameters.HV_DIM, set_parameters.BUNDLER_COUNT_WIDTH
        )


# Config and run
@pytest.mark.parametrize(
    "parameters",
    [
        {
            "HVDimension": str(set_parameters.HV_DIM),
            "CounterWidth": str(set_parameters.BUNDLER_COUNT_WIDTH),
        }
    ],
)
def test_hv_alu_pe(simulator, parameters):
    verilog_sources = ["/rtl/bundler_unit.sv", "/rtl/bundler_set.sv"]

    toplevel = "bundler_set"

    module = "test_bundler_set"

    setup_and_run(
        verilog_sources=verilog_sources,
        toplevel=toplevel,
        module=module,
        simulator=simulator,
        parameters=parameters,
    )
