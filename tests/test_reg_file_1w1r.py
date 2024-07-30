"""
  Copyright 2024 KU Leuven
  Ryan Antonio <ryan.antonio@esat.kuleuven.be>

  Description:
  This tests the basic functionality of the
  register set with 1 write and 1 read port
"""

from util import setup_and_run, gen_rand_bits, clock_and_time, check_result

import cocotb
from cocotb.clock import Clock
import pytest

# Some local parameters for testing
DATA_WIDTH = 32
NUM_REGS = 32


# Set inputs to 0
def clear_inputs_no_clock(dut):
    # Write ports
    dut.clr_i.value = 0
    dut.wr_addr_i.value = 0
    dut.wr_data_i.value = 0
    dut.wr_en_i.value = 0
    # Read ports
    dut.rd_addr_i.value = 0
    return


# Writing register values
async def write_reg(dut, addr, data):
    # Write ports
    dut.wr_addr_i.value = addr
    dut.wr_data_i.value = data
    dut.wr_en_i.value = 1
    await clock_and_time(dut.clk_i)


# Clear registers
async def clr_reg(dut):
    # Write ports
    dut.clr_i.value = 1
    await clock_and_time(dut.clk_i)


# Read register values per port
async def read_reg(dut, addr):
    dut.rd_addr_i.value = addr
    await clock_and_time(dut.clk_i)
    return dut.rd_data_o.value.integer


# Generate random data first
def gen_rand_data_list(num_elem, datawidth):
    rand_data_list = []
    for i in range(num_elem):
        rand_data_list.append(gen_rand_bits(datawidth))
    return rand_data_list


@cocotb.test()
async def reg_file_1w1r_dut(dut):
    cocotb.log.info(" ------------------------------------------ ")
    cocotb.log.info("         Testing Resister Set 1W1R          ")
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
    cocotb.log.info("            Write to registers              ")
    cocotb.log.info(" ------------------------------------------ ")

    rand_data_list = gen_rand_data_list(NUM_REGS, DATA_WIDTH)

    for i in range(NUM_REGS):
        await write_reg(dut, i, rand_data_list[i])

    cocotb.log.info(" ------------------------------------------ ")
    cocotb.log.info("             Read from port                 ")
    cocotb.log.info(" ------------------------------------------ ")

    for i in range(NUM_REGS):
        reg_val = await read_reg(dut, i)
        check_result(reg_val, rand_data_list[i])

    cocotb.log.info(" ------------------------------------------ ")
    cocotb.log.info("         Clear and read registers           ")
    cocotb.log.info(" ------------------------------------------ ")

    clear_inputs_no_clock(dut)
    await clr_reg(dut)

    for i in range(NUM_REGS):
        reg_val = await read_reg(dut, i)
        check_result(reg_val, 0)


# Actual test run
@pytest.mark.parametrize(
    "parameters",
    [
        {
            "DataWidth": str(DATA_WIDTH),
            "NumRegs": str(NUM_REGS),
        }
    ],
)
def test_reg_file_1w1r(simulator, parameters, waves):
    verilog_sources = ["/rtl/common/reg_file_1w1r.sv"]

    toplevel = "reg_file_1w1r"

    module = "test_reg_file_1w1r"

    setup_and_run(
        verilog_sources=verilog_sources,
        toplevel=toplevel,
        module=module,
        simulator=simulator,
        parameters=parameters,
        waves=waves,
    )
