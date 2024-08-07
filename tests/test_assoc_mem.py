"""
  Copyright 2024 KU Leuven
  Ryan Antonio <ryan.antonio@esat.kuleuven.be>

  Description:
  This tests the vectorized bundler unit
"""

import set_parameters
from util import (
    get_root,
    setup_and_run,
    gen_rand_bits,
    clock_and_time,
    hvlist2num,
    numbin2list,
    check_result,
)

import cocotb
from cocotb.clock import Clock
import sys
import pytest
import random

# Add hdc utility functions
hdc_util_path = get_root() + "/hdc_exp/"
print(hdc_util_path)
sys.path.append(hdc_util_path)

from hdc_util import binarize_hv  # noqa: E402


# Test functions


# Set inputs to 0
def clear_inputs_no_clock(dut):
    dut.query_hv_i.value = 0
    dut.am_start_i.value = 0
    dut.class_hv_i.value = 0
    dut.class_hv_valid_i.value = 0
    dut.am_num_class_i.value = 0
    dut.am_predict_valid_clr_i.value = 0
    return


# Loading of query hv
async def load_query_hv(dut, query_hv):
    dut.query_hv_i.value = query_hv
    dut.am_start_i.value = 1
    await clock_and_time(dut.clk_i)
    dut.am_start_i.value = 0
    return


async def load_am_hv(dut, am_hv):
    dut.class_hv_i.value = am_hv
    dut.class_hv_valid_i.value = 1
    await clock_and_time(dut.clk_i)
    dut.class_hv_i.value = 0
    dut.class_hv_valid_i.value = 0
    return


# Generate sample associative memory
# with one of the classes having the
# closest similarity
# Returns both assoc mem and query hv
def gen_am_and_qv(num_classes, hv_dim):
    # First generate the associative memory
    assoc_mem = []
    for i in range(num_classes):
        assoc_mem.append(gen_rand_bits(hv_dim))

    # Next select a random class
    random_idx = random.randrange(num_classes)

    # Flip random bits in the selected random index
    # We do this with the bind function by
    # bundling 2 other HVs to the selected class
    # then after bundling the noise added by the 2
    # reduces the similarity score
    temp_hv1 = numbin2list(gen_rand_bits(hv_dim), hv_dim)
    temp_hv2 = numbin2list(gen_rand_bits(hv_dim), hv_dim)
    class_hv = numbin2list(assoc_mem[random_idx], hv_dim)

    query_hv = temp_hv1 + temp_hv2 + class_hv

    # Threshold is 1.5 = 3/2
    query_hv = binarize_hv(query_hv, 1.5)

    # Bring back into an integer itself!
    # Sad workaround is to convert to str
    # The convert to integer
    query_hv = hvlist2num(query_hv)

    return random_idx, query_hv, assoc_mem


# Actual test routines


@cocotb.test()
async def assoc_mem_dut(dut):
    cocotb.log.info(" ------------------------------------------ ")
    cocotb.log.info("         Testing Associative Memory         ")
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
    cocotb.log.info("             Initialize Values              ")
    cocotb.log.info(" ------------------------------------------ ")

    for i in range(set_parameters.TEST_RUNS):
        # Set random number of classes more than 10
        NUM_CLASSES = random.randint(10, 32)

        # Clear every new test run
        clear_inputs_no_clock(dut)

        # Generate the golde index answer, the query hv and the assoc mem
        golden_idx, query_hv, assoc_mem = gen_am_and_qv(
            NUM_CLASSES, set_parameters.HV_DIM
        )

        # Set this as a CSR controlled value
        dut.am_num_class_i.value = NUM_CLASSES

        # Assume prediction port is always ready
        dut.predict_ready_i.value = 1

        # Start of data loop
        await load_query_hv(dut, query_hv)

        # Randomly between the number of classes checked
        # Set the index where the stall will be asserted
        random_stall = random.randint(0, NUM_CLASSES - 1)

        # Feed associative memory data
        # And allow the similarity search to progress
        for i in range(NUM_CLASSES):
            # Check if stall does assert
            if i == random_stall:
                dut.am_start_i.value = 1

                # Allow time to propagate
                await clock_and_time(dut.clk_i)

                # Check if stall signal is high
                am_stall = dut.am_stall_o.value.integer
                check_result(am_stall, 1)

                # Clear the stall signal
                dut.am_start_i.value = 0

                # Allow time to propagate
                await clock_and_time(dut.clk_i)

                # Check if stall signal is low
                am_stall = dut.am_stall_o.value.integer
                check_result(am_stall, 0)

            # Check if predict valid is low
            predict_valid = dut.predict_valid_o.value.integer
            check_result(predict_valid, 0)

            # Check if CSR predict valid is low
            csr_predict_valid = dut.am_predict_valid_o.value.integer
            check_result(csr_predict_valid, 0)

            # Load the associative memory
            await load_am_hv(dut, assoc_mem[i])

        # Check if predicted result is the correct HV
        actual_idx = dut.predict_o.value.integer
        check_result(actual_idx, golden_idx)

        # Check if predict valid is high
        predict_valid = dut.predict_valid_o.value.integer
        check_result(predict_valid, 1)

        # Check if CSR predict valid is high
        csr_predict_valid = dut.am_predict_valid_o.value.integer
        check_result(csr_predict_valid, 1)

        # Assert clear to see if the csr valid signal is brought down
        dut.am_predict_valid_clr_i.value = 1

        # Time proagation
        await clock_and_time(dut.clk_i)

        # Check if predict valid is brought down
        predict_valid = dut.predict_valid_o.value.integer
        check_result(predict_valid, 0)

        # Check if CSR predict valid is high
        csr_predict_valid = dut.am_predict_valid_o.value.integer
        check_result(csr_predict_valid, 0)

    for i in range(set_parameters.TEST_RUNS):
        await clock_and_time(dut.clk_i)


# Config and run
@pytest.mark.parametrize(
    "parameters",
    [
        {
            "HVDimension": str(set_parameters.HV_DIM),
            "DataWidth": str(set_parameters.REG_FILE_WIDTH),
        }
    ],
)
def test_assoc_mem(simulator, parameters, waves):
    verilog_sources = [
        "/rtl/assoc_memory/ham_dist.sv",
        "/rtl/assoc_memory/assoc_mem.sv",
    ]

    toplevel = "assoc_mem"

    module = "test_assoc_mem"

    setup_and_run(
        verilog_sources=verilog_sources,
        toplevel=toplevel,
        module=module,
        simulator=simulator,
        parameters=parameters,
        waves=waves,
    )
