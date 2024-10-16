"""
  Copyright 2024 KU Leuven
  Ryan Antonio <ryan.antonio@esat.kuleuven.be>

  Description:
  This tests the basic functionality of the update counter
"""

import set_parameters
from util import setup_and_run, check_result

import cocotb
from cocotb.clock import Clock
from util import clock_and_time
import pytest
import math
import random


# Local parameters

COUNTER_WIDTH = int(math.log2(set_parameters.NUM_TOT_IM))


# Test functions


def clear_inputs_no_clock(dut):
    dut.en_i.value = 0
    dut.clr_i.value = 0
    dut.start_i.value = 0
    dut.start_count_i.value = 0
    dut.max_count_i.value = 0
    dut.addr_ready_i.value = 0


# Test routine
@cocotb.test()
async def update_counter_dut(dut):
    cocotb.log.info(" ------------------------------------------ ")
    cocotb.log.info("          Testing Update Counter            ")
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

    for i in range(set_parameters.TEST_RUNS):
        # Enable the counter
        dut.en_i.value = 1

        # Randomly increment the counter
        random_max_count = random.randint(10, (set_parameters.NUM_TOT_IM // 2))
        random_start_count = random.randint(10, (set_parameters.NUM_TOT_IM // 4))

        # Set the maximum and start counts
        dut.max_count_i.value = random_max_count
        dut.start_count_i.value = random_start_count

        # Set to 1 to load start counter
        dut.start_i.value = 1

        # Wait for setting to settle
        await clock_and_time(dut.clk_i)

        # Make sure to reset the signal
        dut.start_i.value = 0

        # Wait for the counter to increment
        # Minus 1 is necessary because address
        # is indexed 0
        for j in range(random_max_count - 1):
            dut.addr_ready_i.value = 1
            await clock_and_time(dut.clk_i)

        # Make sure to disable the ready signal
        # stalls or stops the processing
        dut.addr_ready_i.value = 0

        # Check the counter
        addr_o_value = dut.addr_o.value.integer
        check_result(addr_o_value, random_start_count + random_max_count - 1)

        # Clear the counter
        dut.clr_i.value = 1
        await clock_and_time(dut.clk_i)
        dut.clr_i.value = 0

    cocotb.log.info(" ------------------------------------------ ")
    cocotb.log.info("             Testing Overflow               ")
    cocotb.log.info(" ------------------------------------------ ")

    for i in range(set_parameters.TEST_RUNS):
        # Randomly increment the counter
        random_max_count = random.randint(10, set_parameters.NUM_TOT_IM)
        random_start_count = random.randint(10, (set_parameters.NUM_TOT_IM // 4))
        random_overflow_count = random.randint(5, random_max_count)
        # Run continuously with total number of overflows
        random_total_count = random_max_count + random_overflow_count

        # Set the maximum count
        dut.max_count_i.value = random_max_count
        dut.start_count_i.value = random_start_count

        # Set to 1 to load start counter
        dut.start_i.value = 1

        # Wait for setting to settle
        await clock_and_time(dut.clk_i)

        # Make sure to reset the signal
        dut.start_i.value = 0

        # Wait for the counter to increment
        # Minus 1 is necessary because address
        # is indexed 0
        for j in range(random_total_count - 1):
            dut.addr_ready_i.value = 1
            await clock_and_time(dut.clk_i)

        # Make sure to disable the ready signal
        # stalls or stops the processing
        dut.addr_ready_i.value = 0

        # Check the counter
        # Check if the overflow count is correct
        addr_o_value = dut.addr_o.value.integer
        check_result(addr_o_value, random_overflow_count + random_start_count - 1)

        # Clear the counter
        dut.clr_i.value = 1
        await clock_and_time(dut.clk_i)
        dut.clr_i.value = 0


# Config and run
@pytest.mark.parametrize(
    "parameters", [{"CsrDataWidth": str(set_parameters.REG_FILE_WIDTH)}]
)
def test_update_counter(simulator, parameters, waves):
    verilog_sources = ["/rtl/data_formatter/update_counter.sv"]

    toplevel = "update_counter"

    module = "test_update_counter"

    setup_and_run(
        verilog_sources=verilog_sources,
        toplevel=toplevel,
        module=module,
        simulator=simulator,
        parameters=parameters,
        waves=waves,
    )
