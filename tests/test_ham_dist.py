"""
  Copyright 2024 KU Leuven
  Ryan Antonio <ryan.antonio@esat.kuleuven.be>

  Description:
  This tests the basic functionality
  of the hamming distance unit
"""

import set_parameters
from util import setup_and_run, gen_rand_bits

import cocotb
from cocotb.triggers import Timer
import pytest


# ALU PE model
def ham_dist_golden_out(A, B):
    return bin(A ^ B).count("1")


@cocotb.test()
async def ham_dist_dut(dut):
    cocotb.log.info(" ------------------------------------------ ")
    cocotb.log.info("          Testing Hamming Distance          ")
    cocotb.log.info(" ------------------------------------------ ")

    for i in range(set_parameters.TEST_RUNS):
        # Generate data
        A = gen_rand_bits(set_parameters.HV_DIM)
        B = gen_rand_bits(set_parameters.HV_DIM)

        # Load into the inputs
        dut.A_i.value = A
        dut.B_i.value = B

        # Propagate logic through time
        await Timer(1, "ps")

        # Extract actual and golden data
        actual_val = dut.hamming_dist_o.value.integer
        golden_val = ham_dist_golden_out(A, B)

        # Log
        cocotb.log.info(f"Actual val: {actual_val}; Golden val: {golden_val}")
        assert (
            actual_val == golden_val
        ), f"Error! Hamming distance mismatch! A: {actual_val}; B: {golden_val}"


# Actual test run
@pytest.mark.parametrize(
    "parameters",
    [
        {
            "HVDimension": str(set_parameters.HV_DIM),
            "DataWidth": str(set_parameters.REG_FILE_WIDTH),
        }
    ],
)
def test_ham_dist(simulator, parameters, waves):
    verilog_sources = ["/rtl/assoc_memory/ham_dist.sv"]

    toplevel = "ham_dist"

    module = "test_ham_dist"

    setup_and_run(
        verilog_sources=verilog_sources,
        toplevel=toplevel,
        module=module,
        simulator=simulator,
        parameters=parameters,
        waves=waves,
    )
