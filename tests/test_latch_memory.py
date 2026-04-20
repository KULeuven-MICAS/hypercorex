"""
Copyright 2024 KU Leuven
Ryan Antonio <ryan.antonio@esat.kuleuven.be>

Description:
This tests the basic functionality of the latch-based memory
module with a synchronous write controller and valid-ready
handshake on both the write and read paths.

Write path (4 cycles):
  Cycle 0 (IDLE)          : assert w_valid_i + inputs, FSM captures,
                             w_ready_o and r_req_ready_o go low
  Cycle 1 (WRITE)         : reg_word_w_en asserted
  Cycle 2 (CLEAR_WEN)     : reg_word_w_en cleared, latch closes
  Cycle 3 (CLEAR_CAPTURES): captured regs cleared, w_ready_o and
                             r_req_ready_o restored

Read path (2 cycles):
  Cycle 0: assert r_req_valid_i + r_addr_i (when r_req_ready_o is high)
           → r_resp_data_o and r_resp_valid_o registered at posedge
  Cycle 1: assert r_resp_ready_i to consume response
           → r_resp_valid_o cleared at posedge

All addresses and data values are derived from NUM_WORDS and DATA_WIDTH
so the test is valid for any parameterisation passed in via pytest.
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


# --------------------------------------------------
# Helper: pick N unique random addresses within range
# --------------------------------------------------
def rand_addr(num_words, count=1):
    """Return `count` unique random addresses in [0, num_words)."""
    return random.sample(range(num_words), count)


# --------------------------------------------------
# Helper: clear all inputs without clocking
# --------------------------------------------------
def clear_inputs_no_clock(dut):
    dut.w_valid_i.value = 0
    dut.w_en_i.value = 0
    dut.w_addr_i.value = 0
    dut.w_data_i.value = 0
    dut.r_req_valid_i.value = 0
    dut.r_addr_i.value = 0
    dut.r_resp_ready_i.value = 0


# --------------------------------------------------
# Helper: perform a single write transaction
#
# Timing (4 cycles total):
#   Cycle 0 (IDLE)          : assert w_valid_i + inputs, clock once
#                             → FSM captures, w_ready_o and r_req_ready_o go low
#   Cycles 1-3 (WRITE /
#               CLEAR_WEN /
#               CLEAR_CAPTURES): poll w_ready_o until it returns high
# --------------------------------------------------
async def write_latch(dut, addr, data):
    # Cycle 0: present the transaction
    dut.w_valid_i.value = 1
    dut.w_en_i.value = 1
    dut.w_addr_i.value = addr
    dut.w_data_i.value = data
    await clock_and_time(dut.clk_i)

    # De-assert immediately — inputs no longer needed after capture
    clear_inputs_no_clock(dut)

    # Wait for FSM to finish WRITE → CLEAR_WEN → CLEAR_CAPTURES
    while not dut.w_ready_o.value:
        await clock_and_time(dut.clk_i)


# --------------------------------------------------
# Helper: perform a no-op valid transaction (w_en_i=0)
#
# valid_i fires but w_en_i is deasserted, so captured_w_en=0
# and reg_word_w_en is never set. Memory must remain unchanged.
# --------------------------------------------------
async def noop_latch(dut, addr, data):
    dut.w_valid_i.value = 1
    dut.w_en_i.value = 0
    dut.w_addr_i.value = addr
    dut.w_data_i.value = data
    await clock_and_time(dut.clk_i)

    clear_inputs_no_clock(dut)

    while not dut.w_ready_o.value:
        await clock_and_time(dut.clk_i)


# --------------------------------------------------
# Helper: perform a synchronous read transaction
#
# Timing (2 cycles):
#   Cycle 0: assert r_req_valid_i + r_addr_i (only when r_req_ready_o=1)
#            → at posedge: r_resp_data_o and r_resp_valid_o are registered
#   Cycle 1: assert r_resp_ready_i to consume the response
#            → at posedge: r_resp_valid_o is cleared
#
# Returns r_resp_data_o sampled after cycle 0 posedge.
# --------------------------------------------------
async def read_latch(dut, addr):
    # Wait until the read channel is ready (blocked during write FSM)
    while not dut.r_req_ready_o.value:
        await clock_and_time(dut.clk_i)

    # Cycle 0: issue the read request
    dut.r_req_valid_i.value = 1
    dut.r_addr_i.value = addr
    await clock_and_time(dut.clk_i)

    # De-assert the request
    dut.r_req_valid_i.value = 0
    dut.r_addr_i.value = 0

    # r_resp_valid_o is now high and r_resp_data_o holds the result
    # Sample the data before consuming so we can return it
    result = dut.r_resp_data_o.value.integer

    # Cycle 1: acknowledge the response to clear r_resp_valid_o
    dut.r_resp_ready_i.value = 1
    await clock_and_time(dut.clk_i)
    dut.r_resp_ready_i.value = 0

    return result


# --------------------------------------------------
# Main test
# --------------------------------------------------
@cocotb.test()
async def latch_memory_dut(dut):
    cocotb.log.info(" ------------------------------------------ ")
    cocotb.log.info("        Testing Latch Memory Module         ")
    cocotb.log.info(" ------------------------------------------ ")

    cocotb.log.info(f" NumWords={NUM_WORDS}, DataWidth={DATA_WIDTH}")

    # Initialize all inputs and hold reset
    clear_inputs_no_clock(dut)
    dut.rst_ni.value = 0

    # Start clock (10 ns period)
    clock = Clock(dut.clk_i, 10, units="ns")
    cocotb.start_soon(clock.start(start_high=False))

    # Hold reset for two cycles to ensure all flops settle
    await clock_and_time(dut.clk_i)
    await clock_and_time(dut.clk_i)
    dut.rst_ni.value = 1

    # Verify both ready signals are asserted after reset
    await clock_and_time(dut.clk_i)
    check_result(dut.w_ready_o.value.integer, 1)
    check_result(dut.r_req_ready_o.value.integer, 1)

    # --------------------------------------------------
    cocotb.log.info(" ------------------------------------------ ")
    cocotb.log.info("      Write and read back all words         ")
    cocotb.log.info(" ------------------------------------------ ")

    rand_data_list = [gen_rand_bits(DATA_WIDTH) for _ in range(NUM_WORDS)]

    for i in range(NUM_WORDS):
        await write_latch(dut, i, rand_data_list[i])

    for i in range(NUM_WORDS):
        val = await read_latch(dut, i)
        check_result(val, rand_data_list[i])

    # --------------------------------------------------
    cocotb.log.info(" ------------------------------------------ ")
    cocotb.log.info("    Verify w_ready_o handshake timing       ")
    cocotb.log.info(" ------------------------------------------ ")

    timing_addr = rand_addr(NUM_WORDS)[0]
    timing_data = gen_rand_bits(DATA_WIDTH)

    dut.w_valid_i.value = 1
    dut.w_en_i.value = 1
    dut.w_addr_i.value = timing_addr
    dut.w_data_i.value = timing_data

    # Cycle 0 → IDLE: capture — w_ready_o and r_req_ready_o go low
    await clock_and_time(dut.clk_i)
    clear_inputs_no_clock(dut)
    check_result(dut.w_ready_o.value.integer, 0)
    check_result(dut.r_req_ready_o.value.integer, 0)

    # Cycle 1 → WRITE: reg_word_w_en asserted — still busy
    await clock_and_time(dut.clk_i)
    check_result(dut.w_ready_o.value.integer, 0)
    check_result(dut.r_req_ready_o.value.integer, 0)

    # Cycle 2 → CLEAR_WEN: latch closes — still busy
    await clock_and_time(dut.clk_i)
    check_result(dut.w_ready_o.value.integer, 0)
    check_result(dut.r_req_ready_o.value.integer, 0)

    # Cycle 3 → CLEAR_CAPTURES: both ready signals restored
    await clock_and_time(dut.clk_i)
    check_result(dut.w_ready_o.value.integer, 1)
    check_result(dut.r_req_ready_o.value.integer, 1)

    # Confirm data was committed
    val = await read_latch(dut, timing_addr)
    check_result(val, timing_data)

    # --------------------------------------------------
    cocotb.log.info(" ------------------------------------------ ")
    cocotb.log.info("    Verify read request-response timing     ")
    cocotb.log.info(" ------------------------------------------ ")

    read_addr = rand_addr(NUM_WORDS)[0]
    read_data = gen_rand_bits(DATA_WIDTH)
    await write_latch(dut, read_addr, read_data)

    # Cycle 0: issue read request
    dut.r_req_valid_i.value = 1
    dut.r_addr_i.value = read_addr
    await clock_and_time(dut.clk_i)
    dut.r_req_valid_i.value = 0
    dut.r_addr_i.value = 0

    # r_resp_valid_o must be high and r_resp_data_o must hold the result
    check_result(dut.r_resp_valid_o.value.integer, 1)
    check_result(dut.r_resp_data_o.value.integer, read_data)

    # Cycle 1: consume the response — r_resp_valid_o must clear
    dut.r_resp_ready_i.value = 1
    await clock_and_time(dut.clk_i)
    dut.r_resp_ready_i.value = 0
    check_result(dut.r_resp_valid_o.value.integer, 0)

    # --------------------------------------------------
    cocotb.log.info(" ------------------------------------------ ")
    cocotb.log.info("  r_req_ready_o blocked during write        ")
    cocotb.log.info(" ------------------------------------------ ")

    # Start a write and verify r_req_ready_o is low for all 3 busy cycles
    dut.w_valid_i.value = 1
    dut.w_en_i.value = 1
    dut.w_addr_i.value = rand_addr(NUM_WORDS)[0]
    dut.w_data_i.value = gen_rand_bits(DATA_WIDTH)
    await clock_and_time(dut.clk_i)
    clear_inputs_no_clock(dut)

    # WRITE, CLEAR_WEN — r_req_ready_o must stay low
    for _ in range(2):
        check_result(dut.r_req_ready_o.value.integer, 0)
        await clock_and_time(dut.clk_i)

    # CLEAR_CAPTURES — r_req_ready_o must still be low going in
    check_result(dut.r_req_ready_o.value.integer, 0)
    await clock_and_time(dut.clk_i)

    # After CLEAR_CAPTURES — r_req_ready_o restored
    check_result(dut.r_req_ready_o.value.integer, 1)

    # --------------------------------------------------
    cocotb.log.info(" ------------------------------------------ ")
    cocotb.log.info("  No-op transaction does not modify memory  ")
    cocotb.log.info(" ------------------------------------------ ")

    noop_addr = rand_addr(NUM_WORDS)[0]
    noop_data_original = gen_rand_bits(DATA_WIDTH)
    noop_data_intruder = gen_rand_bits(DATA_WIDTH)

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
