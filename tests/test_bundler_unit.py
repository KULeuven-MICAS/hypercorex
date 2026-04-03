"""
Copyright 2024 KU Leuven
Ryan Antonio <ryan.antonio@esat.kuleuven.be>

Description:
This tests the basic functionality of the bundler unit
"""

import set_parameters
from util import setup_and_run

import cocotb
from cocotb.clock import Clock
from util import clock_and_time, gen_randint
import pytest


# Local parameters

UNSIGNED_MAX = int(2 ** (set_parameters.BUNDLER_COUNT_WIDTH) - 1)
UNSIGNED_MAX_HALF = int(UNSIGNED_MAX / 2)
MAX_VAL = int(2 ** (set_parameters.BUNDLER_COUNT_WIDTH - 1) - 1)
MIN_VAL = int(-1 * (2 ** (set_parameters.BUNDLER_COUNT_WIDTH - 1)))

# Test functions


# For clearing bundler unit
async def clear_bundler_unit(dut):
    dut.clr_i.value = 1
    await clock_and_time(dut.clk_i)
    dut.clr_i.value = 0
    return


# Printing of counter output
def print_counter_output(dut):
    cocotb.log.info(f"Counter output: {dut.counter_o.value.signed_integer}")
    return


# Printing of inputs
def print_all(dut):
    cocotb.log.info(f"bit_i: {dut.bit_i.value.integer}")
    cocotb.log.info(f"valid_i: {dut.valid_i.value.integer}")
    cocotb.log.info(f"clr_i: {dut.clr_i.value.integer}")
    cocotb.log.info(f"counter_o: {dut.counter_o.value.signed_integer}")
    return


# Incrementing input
async def increment_inputs(dut):
    dut.valid_i.value = 1
    dut.bit_i.value = 1
    await clock_and_time(dut.clk_i)
    return


# Decrementing input
async def decrement_inputs(dut):
    dut.valid_i.value = 1
    dut.bit_i.value = 0
    await clock_and_time(dut.clk_i)
    return


# Clearing inputs but
# without time progression
def clear_inputs_no_clock(dut):
    dut.bit_i.value = 0
    dut.valid_i.value = 0
    dut.clr_i.value = 0


# Actual test routines


# Test routine
@cocotb.test()
async def bundler_unit_dut(dut):
    cocotb.log.info(" ------------------------------------------ ")
    cocotb.log.info("           Testing Bundler Unit             ")
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

    # Let cycles run and check if output is positive
    for i in range(gen_randint(UNSIGNED_MAX_HALF)):
        await increment_inputs(dut)
        print_counter_output(dut)

    assert dut.counter_o.value.signed_integer >= 0, "Error! Bundler needs to increment!"

    cocotb.log.info(" ------------------------------------------ ")
    cocotb.log.info("        Testing Clearing of Bundler         ")
    cocotb.log.info(" ------------------------------------------ ")

    # Check if clear signal works
    await clear_bundler_unit(dut)
    print_counter_output(dut)

    assert (
        dut.counter_o.value.signed_integer == 0
    ), "Error! Bundler needs to be cleared to 0!"

    cocotb.log.info(" ------------------------------------------ ")
    cocotb.log.info("            Testing Decrements              ")
    cocotb.log.info(" ------------------------------------------ ")

    # Let cycles run and check if output is negative
    for i in range(gen_randint(UNSIGNED_MAX_HALF)):
        await decrement_inputs(dut)
        print_counter_output(dut)

    assert (
        dut.counter_o.value.signed_integer < 0
    ), "Error! Bundler needs to be cleared to 0!"

    cocotb.log.info(" ------------------------------------------ ")
    cocotb.log.info("       Testing Positive Saturation          ")
    cocotb.log.info(" ------------------------------------------ ")

    # First clear the bundler
    await clear_bundler_unit(dut)

    # Continuously count until maximum
    while dut.counter_o.value.signed_integer != MAX_VAL:
        await increment_inputs(dut)
        print_counter_output(dut)

    # Add 10 more increments and make sure
    # the counter still saturates
    for i in range(10):
        await increment_inputs(dut)
        print_counter_output(dut)

    assert (
        dut.counter_o.value.signed_integer == MAX_VAL
    ), f"Error! Bundler needs to saturate at {MAX_VAL}!"

    cocotb.log.info(" ------------------------------------------ ")
    cocotb.log.info("       Testing Negative Saturation          ")
    cocotb.log.info(" ------------------------------------------ ")

    # First clear the bundler
    await clear_bundler_unit(dut)

    # Continuously count until minimum (negative)
    while dut.counter_o.value.signed_integer != MIN_VAL:
        await decrement_inputs(dut)
        print_counter_output(dut)

    # Add 10 more decerements and make sure
    # the counter still saturates
    for i in range(10):
        await decrement_inputs(dut)
        print_counter_output(dut)

    assert (
        dut.counter_o.value.signed_integer == MIN_VAL
    ), f"Error! Bundler needs to saturate at {MIN_VAL}!"


# Config and run
@pytest.mark.parametrize(
    "parameters", [{"CounterWidth": str(set_parameters.BUNDLER_COUNT_WIDTH)}]
)
def test_bundler_unit(simulator, parameters, waves):
    verilog_sources = ["/rtl/encoder/bundler_unit.sv"]

    toplevel = "bundler_unit"

    module = "test_bundler_unit"

    setup_and_run(
        verilog_sources=verilog_sources,
        toplevel=toplevel,
        module=module,
        simulator=simulator,
        parameters=parameters,
        waves=waves,
    )
