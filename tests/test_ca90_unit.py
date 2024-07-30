"""
  Copyright 2024 KU Leuven
  Ryan Antonio <ryan.antonio@esat.kuleuven.be>

  Description:
  This tests the basic functionality
  of the CA90 generation unit
"""

import set_parameters
import cocotb
from cocotb.triggers import Timer
import pytest
import sys

from util import (
    get_root,
    setup_and_run,
    gen_rand_bits,
    gen_randint,
    check_result,
    numbin2list,
    hvlist2num,
)

# Add hdc utility functions
hdc_util_path = get_root() + "/hdc_exp/"
sys.path.append(hdc_util_path)

from hdc_util import gen_ca90  # noqa: E402


@cocotb.test()
async def ca90_unit_dut(dut):
    cocotb.log.info(" ------------------------------------------ ")
    cocotb.log.info("          Testing CA90 Generation           ")
    cocotb.log.info("         with direct random shifts          ")
    cocotb.log.info(" ------------------------------------------ ")

    # The first test checks if the CA90 is working
    # For direct random shifts
    for i in range(set_parameters.TEST_RUNS):
        # Generate random input but convert
        seed_hv = gen_rand_bits(set_parameters.HV_DIM)
        # Random CA90 cycle time
        ca90_cycle_time = gen_randint(set_parameters.MAX_SHIFT_AMT - 1)

        # Load data into inputs
        dut.vector_i.value = seed_hv
        dut.shift_amt_i.value = ca90_cycle_time

        # Propagate time for logic
        await Timer(1, units="ps")

        # Extract output
        actual_val = dut.vector_o.value.integer

        # Calculating golden answer
        # First convert to list
        seed_hv = numbin2list(seed_hv, set_parameters.HV_DIM)

        # Get golden answer but convert
        # from array to binary number
        golden_val = gen_ca90(seed_hv, ca90_cycle_time)
        golden_val = hvlist2num(golden_val)

        # Compare outputs
        check_result(actual_val, golden_val)


# Actual test run
@pytest.mark.parametrize(
    "parameters",
    [
        {
            "Dimension": str(set_parameters.HV_DIM),
            "MaxShiftAmt": str(set_parameters.MAX_SHIFT_AMT),
        }
    ],
)
def test_ca90_unit(simulator, parameters, waves):
    verilog_sources = ["/rtl/item_memory/ca90_unit.sv"]

    toplevel = "ca90_unit"

    module = "test_ca90_unit"

    setup_and_run(
        verilog_sources=verilog_sources,
        toplevel=toplevel,
        module=module,
        simulator=simulator,
        parameters=parameters,
        waves=waves,
    )
