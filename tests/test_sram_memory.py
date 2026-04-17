"""
Copyright 2024 KU Leuven
Ryan Antonio <ryan.antonio@esat.kuleuven.be>

Description:
This tests the basic functionality of the
generic SRAM memory module with byte-enable
and configurable latency
"""

from util import setup_and_run, gen_rand_bits, clock_and_time, check_result

import cocotb
from cocotb.clock import Clock
import pytest

# Some local parameters for testing
DATA_WIDTH = 32
NUM_WORDS = 256
BYTE_WIDTH = 8
LATENCY = 1

# Derived
NUM_BYTES = DATA_WIDTH // BYTE_WIDTH
ALL_BYTES_EN = (1 << NUM_BYTES) - 1


# Set inputs to 0
def clear_inputs_no_clock(dut):
    dut.req_i.value = 0
    dut.w_en_i.value = 0
    dut.addr_i.value = 0
    dut.w_data_i.value = 0
    dut.b_en_i.value = 0


# Write a word to the SRAM (all bytes enabled)
async def write_sram(dut, addr, data, b_en=ALL_BYTES_EN):
    dut.req_i.value = 1
    dut.w_en_i.value = 1
    dut.addr_i.value = addr
    dut.w_data_i.value = data
    dut.b_en_i.value = b_en
    await clock_and_time(dut.clk_i)
    clear_inputs_no_clock(dut)


# Read a word from the SRAM (with latency=1, data valid after the clock)
async def read_sram(dut, addr):
    dut.req_i.value = 1
    dut.w_en_i.value = 0
    dut.addr_i.value = addr
    await clock_and_time(dut.clk_i)
    clear_inputs_no_clock(dut)
    return dut.r_data_o.value.integer


@cocotb.test()
async def sram_memory_dut(dut):
    cocotb.log.info(" ------------------------------------------ ")
    cocotb.log.info("          Testing SRAM Memory Module        ")
    cocotb.log.info(" ------------------------------------------ ")

    # Initialize inputs
    clear_inputs_no_clock(dut)
    dut.rst_ni.value = 0

    # Initialize clock
    clock = Clock(dut.clk_i, 10, units="ns")
    cocotb.start_soon(clock.start(start_high=False))

    # Hold reset for one cycle
    await clock_and_time(dut.clk_i)
    dut.rst_ni.value = 1

    # --------------------------------------------------
    cocotb.log.info(" ------------------------------------------ ")
    cocotb.log.info("        Write and read back all words       ")
    cocotb.log.info(" ------------------------------------------ ")

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

    # Write a known full word first
    await write_sram(dut, 0, 0xDEADBEEF)

    # Overwrite only the lowest byte (b_en=0b0001) with 0xAB
    new_byte = 0xAB
    await write_sram(dut, 0, new_byte, b_en=0b0001)

    val = await read_sram(dut, 0)
    expected = (0xDEADBE00) | new_byte
    check_result(val, expected)

    # Overwrite only the highest byte (b_en=0b1000) with 0x12
    new_byte_high = 0x12
    await write_sram(dut, 0, new_byte_high << 24, b_en=0b1000)

    val = await read_sram(dut, 0)
    expected = (0x12ADBE00) | new_byte
    check_result(val, expected)

    # --------------------------------------------------
    cocotb.log.info(" ------------------------------------------ ")
    cocotb.log.info("         Test reset clears memory           ")
    cocotb.log.info(" ------------------------------------------ ")

    # Write something, then reset
    await write_sram(dut, 5, 0xCAFEBABE)

    dut.rst_ni.value = 0
    await clock_and_time(dut.clk_i)
    dut.rst_ni.value = 1

    val = await read_sram(dut, 5)
    check_result(val, 0)

    # --------------------------------------------------
    cocotb.log.info(" ------------------------------------------ ")
    cocotb.log.info("      No-req: output should not change      ")
    cocotb.log.info(" ------------------------------------------ ")

    # Write a known value
    await write_sram(dut, 10, 0x12345678)
    # Read it once to latch
    val = await read_sram(dut, 10)
    check_result(val, 0x12345678)

    # Issue no request; r_data_o should hold last latched value
    clear_inputs_no_clock(dut)
    await clock_and_time(dut.clk_i)
    check_result(dut.r_data_o.value.integer, 0x12345678)


# Actual test run
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
