"""
Copyright 2024 KU Leuven
Ryan Antonio <ryan.antonio@esat.kuleuven.be>

Description:
This tests the basic functionality of the generic SRAM memory
module with byte-enable and configurable latency.

All addresses and data values are derived at runtime from
NUM_WORDS, DATA_WIDTH, and BYTE_WIDTH so the test is valid
for any parameterisation passed in via pytest.
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
NUM_WORDS = 256
BYTE_WIDTH = 8
LATENCY = 1

# Derived
NUM_BYTES = DATA_WIDTH // BYTE_WIDTH
ALL_BYTES_EN = (1 << NUM_BYTES) - 1


# --------------------------------------------------
# Helper: pick N unique random addresses within range
# --------------------------------------------------
def rand_addr(num_words, count=1):
    """Return `count` unique random addresses in [0, num_words)."""
    return random.sample(range(num_words), count)


# --------------------------------------------------
# Helper: generate a random value fitting in one byte
# --------------------------------------------------
def rand_byte():
    return random.randint(0x01, 0xFF)  # avoid 0 so changes are detectable


# --------------------------------------------------
# Helper: clear all inputs without clocking
# --------------------------------------------------
def clear_inputs_no_clock(dut):
    dut.req_i.value = 0
    dut.w_en_i.value = 0
    dut.addr_i.value = 0
    dut.w_data_i.value = 0
    dut.b_en_i.value = 0


# --------------------------------------------------
# Helper: write a word to the SRAM
# b_en defaults to all bytes enabled
# --------------------------------------------------
async def write_sram(dut, addr, data, b_en=ALL_BYTES_EN):
    dut.req_i.value = 1
    dut.w_en_i.value = 1
    dut.addr_i.value = addr
    dut.w_data_i.value = data
    dut.b_en_i.value = b_en
    await clock_and_time(dut.clk_i)
    clear_inputs_no_clock(dut)


# --------------------------------------------------
# Helper: read a word from the SRAM
# With Latency=1 the registered output is valid after the clock edge.
# --------------------------------------------------
async def read_sram(dut, addr):
    dut.req_i.value = 1
    dut.w_en_i.value = 0
    dut.addr_i.value = addr
    await clock_and_time(dut.clk_i)
    clear_inputs_no_clock(dut)
    return dut.r_data_o.value.integer


# --------------------------------------------------
# Main test
# --------------------------------------------------
@cocotb.test()
async def sram_memory_dut(dut):
    cocotb.log.info(" ------------------------------------------ ")
    cocotb.log.info("          Testing SRAM Memory Module        ")
    cocotb.log.info(" ------------------------------------------ ")

    cocotb.log.info(
        f" NumWords={NUM_WORDS}, DataWidth={DATA_WIDTH}, "
        f"ByteWidth={BYTE_WIDTH}, Latency={LATENCY}"
    )

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

    # --------------------------------------------------
    cocotb.log.info(" ------------------------------------------ ")
    cocotb.log.info("        Write and read back all words       ")
    cocotb.log.info(" ------------------------------------------ ")

    # One random data value per word — adapts to any NUM_WORDS/DATA_WIDTH
    rand_data_list = [gen_rand_bits(DATA_WIDTH) for _ in range(NUM_WORDS)]

    for i in range(NUM_WORDS):
        await write_sram(dut, i, rand_data_list[i])

    for i in range(NUM_WORDS):
        val = await read_sram(dut, i)
        check_result(val, rand_data_list[i])

    # --------------------------------------------------
    cocotb.log.info(" ------------------------------------------ ")
    cocotb.log.info("          Test byte-enable masking          ")
    cocotb.log.info(" ------------------------------------------ ")

    # Pick a random address and write a random full word as the baseline
    be_addr = rand_addr(NUM_WORDS)[0]
    base_word = gen_rand_bits(DATA_WIDTH)
    await write_sram(dut, be_addr, base_word)

    current_word = base_word

    # Walk through each byte lane: overwrite one byte at a time with a
    # random value and verify that only the targeted byte changes
    for byte_idx in range(NUM_BYTES):
        new_byte = rand_byte()
        byte_mask = 1 << byte_idx
        byte_shift = byte_idx * BYTE_WIDTH

        # Build expected: replace only the targeted byte in current_word
        byte_clear = ~(0xFF << byte_shift) & ((1 << DATA_WIDTH) - 1)
        expected = (current_word & byte_clear) | (new_byte << byte_shift)

        # Write only the new byte value aligned to its position
        await write_sram(dut, be_addr, new_byte << byte_shift, b_en=byte_mask)

        val = await read_sram(dut, be_addr)
        check_result(val, expected)

        # Track the accumulating state for the next iteration
        current_word = expected

    # --------------------------------------------------
    cocotb.log.info(" ------------------------------------------ ")
    cocotb.log.info("         Test reset clears memory           ")
    cocotb.log.info(" ------------------------------------------ ")

    # Write random data to a random address, then reset
    reset_addr = rand_addr(NUM_WORDS)[0]
    reset_data = gen_rand_bits(DATA_WIDTH)
    await write_sram(dut, reset_addr, reset_data)

    dut.rst_ni.value = 0
    await clock_and_time(dut.clk_i)
    dut.rst_ni.value = 1

    val = await read_sram(dut, reset_addr)
    check_result(val, 0)

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

    await write_sram(dut, overwrite_addr, overwrite_first)
    check_result(await read_sram(dut, overwrite_addr), overwrite_first)

    await write_sram(dut, overwrite_addr, overwrite_second)
    check_result(await read_sram(dut, overwrite_addr), overwrite_second)

    # --------------------------------------------------
    cocotb.log.info(" ------------------------------------------ ")
    cocotb.log.info("  Consecutive writes to different addresses ")
    cocotb.log.info(" ------------------------------------------ ")

    # Pick 3 unique random addresses and pair each with random data
    consec_addrs = rand_addr(NUM_WORDS, count=3)
    consec_pairs = [(a, gen_rand_bits(DATA_WIDTH)) for a in consec_addrs]

    for addr, data in consec_pairs:
        await write_sram(dut, addr, data)

    for addr, data in consec_pairs:
        check_result(await read_sram(dut, addr), data)

    # --------------------------------------------------
    cocotb.log.info(" ------------------------------------------ ")
    cocotb.log.info("      No-req: output should hold last value ")
    cocotb.log.info(" ------------------------------------------ ")

    # Write and read a random word to prime the output register
    noreq_addr = rand_addr(NUM_WORDS)[0]
    noreq_data = gen_rand_bits(DATA_WIDTH)
    await write_sram(dut, noreq_addr, noreq_data)

    val = await read_sram(dut, noreq_addr)
    check_result(val, noreq_data)

    # Issue no request — r_data_o must hold the last registered value
    clear_inputs_no_clock(dut)
    await clock_and_time(dut.clk_i)
    check_result(dut.r_data_o.value.integer, noreq_data)

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
            "ByteWidth": str(BYTE_WIDTH),
            "Latency": str(LATENCY),
        }
    ],
)
def test_sram_memory(simulator, parameters, waves):
    verilog_sources = ["/rtl/common/sram_memory.sv"]

    toplevel = "sram_memory"

    module = "test_sram_memory"

    setup_and_run(
        verilog_sources=verilog_sources,
        toplevel=toplevel,
        module=module,
        simulator=simulator,
        parameters=parameters,
        waves=waves,
    )
