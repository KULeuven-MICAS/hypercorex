"""
Copyright 2024 KU Leuven
Ryan Antonio <ryan.antonio@esat.kuleuven.be>

Description:
This tests the basic functionality of the latch-based memory
module with a synchronous write controller and valid-ready
handshake. The write path takes 4 cycles (IDLE -> WRITE ->
CLEAR_WEN -> CLEAR_CAPTURES) and the read path is purely
combinational.

All addresses and data values are derived at runtime from
NUM_WORDS and DATA_WIDTH so the test is valid for any
parameterisation passed in via pytest.
"""

from util import setup_and_run, gen_rand_bits, clock_and_time, check_result

import random
import cocotb
from cocotb.clock import Clock
import pytest

# --------------------------------------------------
# Top-level parameters — change here and everywhere
# in the test adapts automatically
# --------------------------------------------------
DATA_WIDTH = 32
NUM_WORDS = 32
MAX_DATA = (1 << DATA_WIDTH) - 1


# --------------------------------------------------
# Helper: pick N unique random addresses within range
# --------------------------------------------------
def rand_addr(NUM_WORDS, count=1):
    """Return `count` unique random addresses in [0, NUM_WORDS)."""
    return random.sample(range(NUM_WORDS), count)


# --------------------------------------------------
# Helper: clear all inputs without clocking
# --------------------------------------------------
def clear_inputs_no_clock(dut):
    dut.valid_i.value = 0
    dut.w_en_i.value = 0
    dut.w_addr_i.value = 0
    dut.w_data_i.value = 0
    dut.r_addr_i.value = 0


# --------------------------------------------------
# Helper: perform a single write transaction
#
# Timing (4 cycles total):
#   Cycle 0 (IDLE)         : assert valid_i + write inputs, clock once
#                            → FSM captures inputs, ready_o goes low
#   Cycles 1-3 (WRITE /    : poll ready_o each cycle until it returns high
#               CLEAR_WEN /  → FSM completes WRITE, CLEAR_WEN, CLEAR_CAPTURES
#               CLEAR_CAPTURES)
# --------------------------------------------------
async def write_latch(dut, addr, data):
    # Cycle 0: present transaction to the FSM
    dut.valid_i.value = 1
    dut.w_en_i.value = 1
    dut.w_addr_i.value = addr
    dut.w_data_i.value = data
    await clock_and_time(dut.clk_i)

    # De-assert immediately after capture — inputs no longer needed
    clear_inputs_no_clock(dut)

    # Wait for the FSM to finish WRITE -> CLEAR_WEN -> CLEAR_CAPTURES
    # ready_o is registered, goes high at the end of CLEAR_CAPTURES
    while not dut.ready_o.value:
        await clock_and_time(dut.clk_i)


# --------------------------------------------------
# Helper: perform a no-op valid transaction (w_en_i=0)
#
# This exercises the path where valid_i fires but w_en_i is
# deasserted, so captured_w_en=0 and reg_word_w_en is never set.
# Memory content at the given address should remain unchanged.
# --------------------------------------------------
async def noop_latch(dut, addr, data):
    dut.valid_i.value = 1
    dut.w_en_i.value = 0  # no write
    dut.w_addr_i.value = addr
    dut.w_data_i.value = data
    await clock_and_time(dut.clk_i)

    clear_inputs_no_clock(dut)

    while not dut.ready_o.value:
        await clock_and_time(dut.clk_i)


# --------------------------------------------------
# Helper: combinational read — no clock required
#
# The read path is: r_data_o = memory[r_addr_i]
# Simply drive r_addr_i and sample r_data_o immediately.
# --------------------------------------------------
async def read_latch(dut, addr):
    dut.r_addr_i.value = addr
    await clock_and_time(dut.clk_i)
    return dut.r_data_o.value.integer


# --------------------------------------------------
# Main test
# --------------------------------------------------
@cocotb.test()
async def latch_memory_dut(dut):
    cocotb.log.info(" ------------------------------------------ ")
    cocotb.log.info("        Testing Latch Memory Module         ")
    cocotb.log.info(" ------------------------------------------ ")

    cocotb.log.info(f" NumWords={NUM_WORDS}, DataWidth={DATA_WIDTH}")

    # Initialize inputs and hold reset
    clear_inputs_no_clock(dut)
    dut.rst_ni.value = 0

    # Start clock (10 ns period)
    clock = Clock(dut.clk_i, 10, units="ns")
    cocotb.start_soon(clock.start(start_high=False))

    # Hold reset for two cycles to ensure all flops settle
    await clock_and_time(dut.clk_i)
    await clock_and_time(dut.clk_i)
    dut.rst_ni.value = 1

    # Verify ready_o is asserted after reset before proceeding
    await clock_and_time(dut.clk_i)
    check_result(dut.ready_o.value.integer, 1)

    # --------------------------------------------------
    cocotb.log.info(" ------------------------------------------ ")
    cocotb.log.info("      Write and read back all words         ")
    cocotb.log.info(" ------------------------------------------ ")

    # One random data value per word — adapts to any NUM_WORDS/DATA_WIDTH
    rand_data_list = [gen_rand_bits(DATA_WIDTH) for _ in range(NUM_WORDS)]
    print(rand_data_list)
    for i in range(NUM_WORDS):
        await write_latch(dut, i, rand_data_list[i])

    # Verify all words — read is combinational so no clocking needed
    for i in range(NUM_WORDS):
        val = await read_latch(dut, i)
        check_result(val, rand_data_list[i])

    # --------------------------------------------------
    cocotb.log.info(" ------------------------------------------ ")
    cocotb.log.info("    Verify ready_o handshake timing         ")
    cocotb.log.info(" ------------------------------------------ ")

    # Use a random valid address and data for the timing probe
    timing_addr = rand_addr(NUM_WORDS)[0]
    timing_data = gen_rand_bits(DATA_WIDTH)

    dut.valid_i.value = 1
    dut.w_en_i.value = 1
    dut.w_addr_i.value = timing_addr
    dut.w_data_i.value = timing_data

    # Cycle 0 → IDLE: clock the capture, ready_o should go low
    await clock_and_time(dut.clk_i)
    clear_inputs_no_clock(dut)
    check_result(dut.ready_o.value.integer, 0)

    # Cycle 1 → WRITE: still busy
    await clock_and_time(dut.clk_i)
    check_result(dut.ready_o.value.integer, 0)

    # Cycle 2 → CLEAR_WEN: still busy
    await clock_and_time(dut.clk_i)
    check_result(dut.ready_o.value.integer, 0)

    # Cycle 3 → CLEAR_CAPTURES: ready_o goes high at end of this cycle
    await clock_and_time(dut.clk_i)
    check_result(dut.ready_o.value.integer, 1)

    # Confirm the data was actually committed at the random address
    val = await read_latch(dut, timing_addr)
    check_result(val, timing_data)

    # --------------------------------------------------
    cocotb.log.info(" ------------------------------------------ ")
    cocotb.log.info("    Read is combinational (no clock)        ")
    cocotb.log.info(" ------------------------------------------ ")

    # Pick two distinct random addresses — guaranteed valid for any NUM_WORDS
    addr_a, addr_b = rand_addr(NUM_WORDS, count=2)
    data_a = gen_rand_bits(DATA_WIDTH)

    # Write to addr_a then read back immediately without a clock edge
    await write_latch(dut, addr_a, data_a)
    val = await read_latch(dut, addr_a)
    check_result(val, data_a)

    # Switching r_addr_i to addr_b instantly reflects that word —
    # addr_b was written during the "write and read back all words" test
    val = await read_latch(dut, addr_b)
    check_result(val, rand_data_list[addr_b])

    # --------------------------------------------------
    cocotb.log.info(" ------------------------------------------ ")
    cocotb.log.info("  No-op transaction does not modify memory  ")
    cocotb.log.info(" ------------------------------------------ ")

    # Pick a random address, write a known value, then issue a no-op
    # with different data and confirm the word is unchanged
    noop_addr = rand_addr(NUM_WORDS)[0]
    noop_data_original = gen_rand_bits(DATA_WIDTH)
    noop_data_intruder = gen_rand_bits(DATA_WIDTH)

    # Ensure the intruder value is actually different
    while noop_data_intruder == noop_data_original:
        noop_data_intruder = gen_rand_bits(DATA_WIDTH)

    await write_latch(dut, noop_addr, noop_data_original)
    check_result(await read_latch(dut, noop_addr), noop_data_original)

    await noop_latch(dut, noop_addr, noop_data_intruder)
    check_result(await read_latch(dut, noop_addr), noop_data_original)

    # --------------------------------------------------
    cocotb.log.info(" ------------------------------------------ ")
    cocotb.log.info("  Overwrite: second write replaces first    ")
    cocotb.log.info(" ------------------------------------------ ")

    overwrite_addr = rand_addr(NUM_WORDS)[0]
    overwrite_first = gen_rand_bits(DATA_WIDTH)
    overwrite_second = gen_rand_bits(DATA_WIDTH)

    # Ensure both values differ so the overwrite is detectable
    while overwrite_second == overwrite_first:
        overwrite_second = gen_rand_bits(DATA_WIDTH)

    await write_latch(dut, overwrite_addr, overwrite_first)
    check_result(await read_latch(dut, overwrite_addr), overwrite_first)

    await write_latch(dut, overwrite_addr, overwrite_second)
    check_result(await read_latch(dut, overwrite_addr), overwrite_second)

    # --------------------------------------------------
    cocotb.log.info(" ------------------------------------------ ")
    cocotb.log.info("  Consecutive writes to different addresses ")
    cocotb.log.info(" ------------------------------------------ ")

    # Pick 3 unique random addresses and pair each with random data
    consec_addrs = rand_addr(NUM_WORDS, count=3)
    consec_pairs = [(a, gen_rand_bits(DATA_WIDTH)) for a in consec_addrs]

    for addr, data in consec_pairs:
        await write_latch(dut, addr, data)

    for addr, data in consec_pairs:
        check_result(await read_latch(dut, addr), data)

    cocotb.log.info(" ------------------------------------------ ")
    cocotb.log.info("         All tests passed!                  ")
    cocotb.log.info(" ------------------------------------------ ")


# --------------------------------------------------
# Pytest entry point
# --------------------------------------------------
@pytest.mark.parametrize(
    "parameters",
    [
        {
            "NumWords": str(NUM_WORDS),
            "DataWidth": str(DATA_WIDTH),
        }
    ],
)
def test_latch_memory(simulator, parameters, waves):
    verilog_sources = ["/rtl/common/latch_memory.sv"]

    toplevel = "latch_memory"

    module = "test_latch_memory"

    setup_and_run(
        verilog_sources=verilog_sources,
        toplevel=toplevel,
        module=module,
        simulator=simulator,
        parameters=parameters,
        waves=waves,
    )
