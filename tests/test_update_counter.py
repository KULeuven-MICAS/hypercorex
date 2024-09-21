"""
  Copyright 2024 KU Leuven
  Ryan Antonio <ryan.antonio@esat.kuleuven.be>

  Description:
  This tests the basic functionality of the update counter
"""

import set_parameters
from util import setup_and_run

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
    dut.update_i.value = 0


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
        random_count = random.randint(1, set_parameters.NUM_TOT_IM)
        for j in range(random_count):
            dut.update_i.value = 1
            await clock_and_time(dut.clk_i)

        # Check the counter
        assert dut.addr_o.value == random_count

        # Clear the counter
        dut.clr_i.value = 1
        await clock_and_time(dut.clk_i)
        dut.clr_i.value = 0


# Config and run
@pytest.mark.parametrize(
    "parameters", [{"CounterWidth": str(set_parameters.BUNDLER_COUNT_WIDTH)}]
)
def test_update_counter(simulator, parameters, waves):
    verilog_sources = ["/rtl/item_memory/update_counter.sv"]

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
