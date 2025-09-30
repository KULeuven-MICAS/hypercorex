"""
  Copyright 2024 KU Leuven
  Ryan Antonio <ryan.antonio@esat.kuleuven.be>

  Description:
  This tests the basic functionality
  of binary compare unit
"""

import set_parameters
from util import setup_and_run, check_result
import random

import cocotb
from cocotb.triggers import Timer
import pytest

# Some parameters
NUM_COMPARE_REGS = 32


# Return the max sim score and index given
# a set of scores already computed
def golden_binary_compare(compare_set):
    max_sim = 10e6
    max_idx = 0
    for i in range(len(compare_set)):
        if compare_set[i] < max_sim:
            max_sim = compare_set[i]
            max_idx = i
    return max_sim, max_idx


@cocotb.test()
async def ham_dist_dut(dut):
    cocotb.log.info(" ---------------------------------------- ")
    cocotb.log.info("          Testing Binary Compare          ")
    cocotb.log.info(" ---------------------------------------- ")

    for i in range(set_parameters.TEST_RUNS):
        compare_set = []
        for j in range(NUM_COMPARE_REGS):
            # Generate data
            data = random.randint(0, 255)
            compare_set.append(data)
            # Load the same data to DUT
            dut.compare_regs[j].value = data
        # Get golden score
        max_sim, max_idx = golden_binary_compare(compare_set)

        # Propagate logic through time
        await Timer(1, "ns")

        # Compare golden
        actual_min_val = dut.min_value_o.value.integer
        actual_min_idx = dut.min_index_o.value.integer
        check_result(actual_min_val, max_sim)
        check_result(actual_min_idx, max_idx)

        await Timer(1, "ns")
        await Timer(1, "ns")
        await Timer(1, "ns")


# Actual test run
@pytest.mark.parametrize(
    "parameters",
    [
        {
            "CompareRegsWidth": str(16),
        }
    ],
)
def test_binary_compare(simulator, parameters, waves):
    verilog_sources = ["/rtl/assoc_memory/binary_compare.sv"]

    toplevel = "binary_compare"

    module = "test_binary_compare"

    setup_and_run(
        verilog_sources=verilog_sources,
        toplevel=toplevel,
        module=module,
        simulator=simulator,
        parameters=parameters,
        waves=waves,
    )
