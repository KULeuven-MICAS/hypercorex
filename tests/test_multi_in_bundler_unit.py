"""
Copyright 2024 KU Leuven
Ryan Antonio <ryan.antonio@esat.kuleuven.be>

Description:
This tests the basic functionality of the multi-input bundler unit.
The idea is that there can be multiple inputs that contribute
to the same counter, and the bundler unit needs to correctly
increment or decrement the counter based on the valid and bit inputs.
"""

from util import setup_and_run

import cocotb
from cocotb.clock import Clock
from util import clock_and_time, gen_randint
import pytest


# Local parameters
COUNTER_WIDTH = 8
NUM_INPUTS = 4

MAX_VAL = 2 ** (COUNTER_WIDTH - 1) - 1
MIN_VAL = -(2 ** (COUNTER_WIDTH - 1))

NUM_TESTS = 20


# Test functions
# For clearing bundler unit
async def clear_bundler(dut):
    dut.clr_i.value = 1
    await clock_and_time(dut.clk_i)
    dut.clr_i.value = 0
    return


# Printing of counter output
def print_counter_output(dut):
    cocotb.log.info(f"Counter output: {dut.counter_o.value.signed_integer}")
    return


# Incrementing input
async def increment_inputs(dut):
    input_increment = [0] * NUM_INPUTS
    data_in = int("".join(str(b) for b in input_increment), 2)
    dut.bit_i.value = data_in
    valid_in = [1] * NUM_INPUTS
    valid_in = int("".join(str(b) for b in valid_in), 2)
    dut.valid_i.value = valid_in
    await clock_and_time(dut.clk_i)
    return


# Decrementing input
async def decrement_inputs(dut):
    input_decrement = [1] * NUM_INPUTS
    data_in = int("".join(str(b) for b in input_decrement), 2)
    dut.bit_i.value = data_in
    valid_in = [1] * NUM_INPUTS
    valid_in = int("".join(str(b) for b in valid_in), 2)
    dut.valid_i.value = valid_in
    await clock_and_time(dut.clk_i)
    return


# Randomizing inputs
async def randomize_inputs(dut):
    valid_set = []
    bit_set = []
    for i in range(NUM_INPUTS):
        valid_set.append(gen_randint(0, 1))
        bit_set.append(gen_randint(0, 1))
    valid_in = int("".join(str(b) for b in valid_set), 2)
    bit_in = int("".join(str(b) for b in bit_set), 2)
    dut.valid_i.value = valid_in
    dut.bit_i.value = bit_in
    # Calculate that for valid index
    # If valid and bit is 1, increment by 1
    # If valid and bit is 0, decrement by 1
    total_value = 0
    for i in range(NUM_INPUTS):
        if valid_set[i] == 1:
            if bit_set[i] == 1:
                total_value -= 1
            else:
                total_value += 1
    await clock_and_time(dut.clk_i)
    return total_value


# Clearing inputs but
# without time progression
def clear_inputs_no_clock(dut):
    dut.bit_i.value = 0
    dut.valid_i.value = 0
    dut.clr_i.value = 0


# Test routine
@cocotb.test()
async def multi_in_bundler_unit_dut(dut):
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

    for i in range(
        MAX_VAL // NUM_INPUTS + 5
    ):  # Test incrementing beyond max value to check saturation
        await increment_inputs(dut)

    # Check final value is saturated at MAX_VAL
    assert (
        dut.counter_o.value.signed_integer == MAX_VAL
    ), "Counter did not saturate at MAX_VAL as expected"

    # Clear inputs before next test
    clear_inputs_no_clock(dut)
    await clear_bundler(dut)

    cocotb.log.info(" ------------------------------------------ ")
    cocotb.log.info("            Testing Decrements              ")
    cocotb.log.info(" ------------------------------------------ ")

    for i in range(
        -MIN_VAL // NUM_INPUTS + 5
    ):  # Test decrementing beyond min value to check saturation
        await decrement_inputs(dut)

    # Check final value is saturated at MIN_VAL
    assert (
        dut.counter_o.value.signed_integer == MIN_VAL
    ), "Counter did not saturate at MIN_VAL as expected"

    # Clear inputs before next test
    clear_inputs_no_clock(dut)
    await clear_bundler(dut)

    cocotb.log.info(" ------------------------------------------ ")
    cocotb.log.info("          Testing Randomization             ")
    cocotb.log.info(" ------------------------------------------ ")

    expected_value = 0
    for i in range(NUM_TESTS):  # Test with 20 random input combinations
        increment_val = await randomize_inputs(dut)
        expected_value += increment_val

        # Check for saturation
        if expected_value > MAX_VAL:
            expected_value = MAX_VAL
        elif expected_value < MIN_VAL:
            expected_value = MIN_VAL

        assert dut.counter_o.value.signed_integer == expected_value, (
            f"Counter value {dut.counter_o.value.signed_integer} "
            f"does not match expected {expected_value}"
        )

    # Wait 5 clock cycles
    for _ in range(5):
        await clock_and_time(dut.clk_i)


# Config and run
@pytest.mark.parametrize(
    "parameters",
    [
        {"CounterWidth": str(COUNTER_WIDTH), "NumInputs": str(NUM_INPUTS)},
    ],
)
def test_multi_in_bundler_unit(simulator, parameters, waves):
    verilog_sources = [
        "/rtl/common/adder_tree.sv",
        "/rtl/encoder/multi_in_bundler_unit.sv",
    ]

    toplevel = "multi_in_bundler_unit"

    module = "test_multi_in_bundler_unit"

    setup_and_run(
        verilog_sources=verilog_sources,
        toplevel=toplevel,
        module=module,
        simulator=simulator,
        parameters=parameters,
        waves=waves,
    )
