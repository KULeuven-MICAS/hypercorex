"""
Copyright 2024 KU Leuven
Ryan Antonio <ryan.antonio@esat.kuleuven.be>

Description:
This tests the basic functionality of the multi-input bundler set.
The set receives multiple full hypervectors and bundles them together
across all HV dimensions simultaneously.
"""

from util import setup_and_run

import cocotb
from cocotb.clock import Clock
from util import clock_and_time
import pytest
import random

# Local parameters
HV_DIMENSION = 128
COUNTER_WIDTH = 8
NUM_INPUTS = 4

MAX_VAL = 2 ** (COUNTER_WIDTH - 1) - 1
MIN_VAL = -(2 ** (COUNTER_WIDTH - 1))

NUM_TESTS = 20


async def clear_bundler(dut):
    dut.clr_i.value = 1
    await clock_and_time(dut.clk_i)
    dut.clr_i.value = 0


def clear_inputs_no_clock(dut):
    for i in range(NUM_INPUTS):
        dut.hv_i[i].value = 0
    dut.valid_i.value = 0
    dut.clr_i.value = 0


def check_binarized(dut, expected_counters):
    """Verify binarized_hv_o matches sign of each counter.
    SV logic: bit=0 if counter is negative (sign bit=1), bit=1 otherwise."""
    binarized = dut.binarized_hv_o.value.integer
    for j in range(HV_DIMENSION):
        expected_bit = 0 if expected_counters[j] < 0 else 1
        actual_bit = (binarized >> j) & 1
        assert actual_bit == expected_bit, (
            f"Binarized bit {j}: expected {expected_bit}, got {actual_bit} "
            f"(counter={expected_counters[j]})"
        )


async def increment_all(dut):
    """
    Drive all HV inputs to all-ones with all-valid —
    increments every counter by NumInputs.
    """
    all_valid = (1 << NUM_INPUTS) - 1
    for i in range(NUM_INPUTS):
        dut.hv_i[i].value = 0
    dut.valid_i.value = all_valid
    await clock_and_time(dut.clk_i)


async def decrement_all(dut):
    """Drive all HV inputs to all-zeros with all-valid —
    decrements every counter by NumInputs."""
    all_ones = (1 << HV_DIMENSION) - 1
    all_valid = (1 << NUM_INPUTS) - 1
    for i in range(NUM_INPUTS):
        dut.hv_i[i].value = all_ones
    dut.valid_i.value = all_valid
    await clock_and_time(dut.clk_i)


async def randomize_inputs(dut):
    """Randomize hv_i and valid_i. Returns per-dimension counter deltas."""
    valid_val = random.randint(0, (1 << NUM_INPUTS) - 1)
    hv_vals = [random.randint(0, (1 << HV_DIMENSION) - 1) for _ in range(NUM_INPUTS)]

    for i in range(NUM_INPUTS):
        dut.hv_i[i].value = hv_vals[i]
    dut.valid_i.value = valid_val

    # Compute expected delta for each dimension
    deltas = [0] * HV_DIMENSION
    for j in range(HV_DIMENSION):
        for i in range(NUM_INPUTS):
            if (valid_val >> i) & 1:
                bit = (hv_vals[i] >> j) & 1
                deltas[j] += -1 if bit else 1

    await clock_and_time(dut.clk_i)
    return deltas


@cocotb.test()
async def multi_in_bundler_set_dut(dut):
    cocotb.log.info(" ------------------------------------------ ")
    cocotb.log.info("       Testing Multi-In Bundler Set         ")
    cocotb.log.info(" ------------------------------------------ ")

    clear_inputs_no_clock(dut)
    dut.rst_ni.value = 0

    clock = Clock(dut.clk_i, 10, units="ns")
    cocotb.start_soon(clock.start(start_high=False))

    await clock_and_time(dut.clk_i)
    dut.rst_ni.value = 1

    expected_counters = [0] * HV_DIMENSION

    # ------------------------------------------
    cocotb.log.info(" ------------------------------------------ ")
    cocotb.log.info("            Testing Increments              ")
    cocotb.log.info(" ------------------------------------------ ")

    for _ in range(MAX_VAL // NUM_INPUTS + 5):
        await increment_all(dut)
        for j in range(HV_DIMENSION):
            expected_counters[j] = min(expected_counters[j] + NUM_INPUTS, MAX_VAL)

    # All counters should be saturated at MAX_VAL
    for j in range(HV_DIMENSION):
        actual = dut.counter_o[j].value.signed_integer
        assert actual == MAX_VAL, f"Dimension {j}: expected {MAX_VAL}, got {actual}"
    check_binarized(dut, expected_counters)

    clear_inputs_no_clock(dut)
    await clear_bundler(dut)
    expected_counters = [0] * HV_DIMENSION

    # ------------------------------------------
    cocotb.log.info(" ------------------------------------------ ")
    cocotb.log.info("            Testing Decrements              ")
    cocotb.log.info(" ------------------------------------------ ")

    for _ in range((-MIN_VAL) // NUM_INPUTS + 5):
        await decrement_all(dut)
        for j in range(HV_DIMENSION):
            expected_counters[j] = max(expected_counters[j] - NUM_INPUTS, MIN_VAL)

    # All counters should be saturated at MIN_VAL
    for j in range(HV_DIMENSION):
        actual = dut.counter_o[j].value.signed_integer
        assert actual == MIN_VAL, f"Dimension {j}: expected {MIN_VAL}, got {actual}"
    check_binarized(dut, expected_counters)

    clear_inputs_no_clock(dut)
    await clear_bundler(dut)
    expected_counters = [0] * HV_DIMENSION

    # ------------------------------------------
    cocotb.log.info(" ------------------------------------------ ")
    cocotb.log.info("          Testing Randomization             ")
    cocotb.log.info(" ------------------------------------------ ")

    for i in range(NUM_TESTS):
        deltas = await randomize_inputs(dut)

        for j in range(HV_DIMENSION):
            expected_counters[j] = max(
                MIN_VAL, min(MAX_VAL, expected_counters[j] + deltas[j])
            )

        for j in range(HV_DIMENSION):
            actual = dut.counter_o[j].value.signed_integer
            assert (
                actual == expected_counters[j]
            ), f"Test {i}, Dimension {j}: expected {expected_counters[j]}, got {actual}"

        check_binarized(dut, expected_counters)

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
def test_multi_in_bundler_set(simulator, parameters, waves):
    verilog_sources = [
        "/rtl/common/adder_tree.sv",
        "/rtl/encoder/multi_in_bundler_unit.sv",
        "/rtl/encoder/multi_in_bundler_set.sv",
    ]

    toplevel = "multi_in_bundler_set"
    module = "test_multi_in_bundler_set"

    setup_and_run(
        verilog_sources=verilog_sources,
        toplevel=toplevel,
        module=module,
        simulator=simulator,
        parameters=parameters,
        waves=waves,
    )
