"""
  Copyright 2024 KU Leuven
  Ryan Antonio <ryan.antonio@esat.kuleuven.be>

  Description:
  This tests the basic functionality
  of the instruction control
"""

import set_parameters
import cocotb
from cocotb.clock import Clock
import pytest
import random

from util import setup_and_run, gen_rand_bits, clock_and_time, check_result


def clear_inputs_no_clock(dut):
    dut.start_i.value = 0
    dut.clr_i.value = 0
    dut.stall_i.value = 0
    dut.inst_wr_addr_i.value = 0
    dut.inst_wr_data_i.value = 0
    dut.inst_wr_en_i.value = 0
    dut.dbg_en_i.value = 0
    dut.dbg_addr_i.value = 0
    return


async def write_inst_mem(dut, inst_addr, inst_data):
    clear_inputs_no_clock(dut)
    dut.inst_wr_addr_i.value = inst_addr
    dut.inst_wr_data_i.value = inst_data
    dut.inst_wr_en_i.value = 1
    await clock_and_time(dut.clk_i)
    clear_inputs_no_clock(dut)
    return


async def read_dbg(dut, addr):
    clear_inputs_no_clock(dut)
    dut.dbg_en_i.value = 1
    dut.dbg_addr_i.value = addr
    await clock_and_time(dut.clk_i)
    clear_inputs_no_clock(dut)
    return


@cocotb.test()
async def inst_control_dut(dut):
    cocotb.log.info(" ------------------------------------------ ")
    cocotb.log.info("        Testing Instruction Control         ")
    cocotb.log.info(" ------------------------------------------ ")

    # Initialize input values
    clear_inputs_no_clock(dut)
    dut.rst_ni.value = 0

    # Initialize CSR related values
    dut.start_i.value = 0

    dut.inst_loop_mode_i.value = 0
    dut.inst_loop_jump_addr1_i.value = 0
    dut.inst_loop_jump_addr2_i.value = 0
    dut.inst_loop_jump_addr3_i.value = 0
    dut.inst_loop_end_addr1_i.value = 0
    dut.inst_loop_end_addr2_i.value = 0
    dut.inst_loop_end_addr3_i.value = 0
    dut.inst_loop_count_addr1_i.value = 0
    dut.inst_loop_count_addr2_i.value = 0
    dut.inst_loop_count_addr3_i.value = 0

    # Initialize clock always
    clock = Clock(dut.clk_i, 10, units="ns")
    cocotb.start_soon(clock.start(start_high=False))

    # Wait one cycle for reset
    await clock_and_time(dut.clk_i)

    dut.rst_ni.value = 1

    cocotb.log.info(" ------------------------------------------ ")
    cocotb.log.info("       Writing to Instruction Memory        ")
    cocotb.log.info(" ------------------------------------------ ")

    # Generate golden data to write
    golden_data_list = []
    for i in range(set_parameters.INST_MEM_DEPTH):
        golden_data_list.append(gen_rand_bits(set_parameters.REG_FILE_WIDTH))

    cocotb.log.info(" ------------------------------------------ ")
    cocotb.log.info("     Check values with program counter      ")
    cocotb.log.info(" ------------------------------------------ ")

    # Need to configure loop by setting loop mode to 1
    # For the first temporal loop only
    # Set jump address to 0 to set where it goes after
    # Set value to be all the instruction memories
    # Set the count to 1 to set the end
    dut.inst_loop_mode_i.value = 1
    dut.inst_loop_jump_addr1_i.value = 0
    dut.inst_loop_end_addr1_i.value = set_parameters.INST_MEM_DEPTH - 1
    dut.inst_loop_count_addr1_i.value = 1

    # Write the data to instruction memory
    for i in range(set_parameters.INST_MEM_DEPTH):
        await write_inst_mem(dut, i, golden_data_list[i])

    # Check result immediatley through program counter
    # first activate or enable the program counter
    # then for every clock cycle check the output data
    dut.start_i.value = 1

    await clock_and_time(dut.clk_i)

    dut.start_i.value = 0

    for i in range(set_parameters.INST_MEM_DEPTH):
        # Extract the 1st data that is readily available
        pc_val = dut.inst_pc_o.value.integer
        inst_data_val = dut.inst_rd_o.value.integer

        check_result(pc_val, i)
        check_result(inst_data_val, golden_data_list[i])

        await clock_and_time(dut.clk_i)

    # Redo the test but this time use the debug port
    cocotb.log.info(" ------------------------------------------ ")
    cocotb.log.info("        Check values with debug mode        ")
    cocotb.log.info(" ------------------------------------------ ")

    # Clear first
    clear_inputs_no_clock(dut)
    await clock_and_time(dut.clk_i)

    # Load the address then check immediateley
    for i in range(set_parameters.INST_MEM_DEPTH):
        await read_dbg(dut, i)
        inst_data_val = dut.inst_rd_o.value.integer
        check_result(inst_data_val, golden_data_list[i])

    # This is for waveform checking later
    for i in range(set_parameters.TEST_RUNS):
        # Propagate time for logic
        await clock_and_time(dut.clk_i)

    cocotb.log.info(" ------------------------------------------ ")
    cocotb.log.info("             Test clear signal              ")
    cocotb.log.info(" ------------------------------------------ ")

    # Clear first
    clear_inputs_no_clock(dut)
    await clock_and_time(dut.clk_i)

    dut.clr_i.value = 1
    await clock_and_time(dut.clk_i)
    clear_inputs_no_clock(dut)

    # Enable again
    dut.start_i.value = 1
    await clock_and_time(dut.clk_i)
    clear_inputs_no_clock(dut)

    # Check only the output and results need to be 0
    for i in range(set_parameters.INST_MEM_DEPTH):
        # Extract the 1st data that is readily available
        inst_data_val = dut.inst_rd_o.value.integer

        check_result(inst_data_val, 0)

        await clock_and_time(dut.clk_i)

    cocotb.log.info(" ------------------------------------------ ")
    cocotb.log.info("             Test loop control              ")
    cocotb.log.info(" ------------------------------------------ ")

    # Clear inputs
    clear_inputs_no_clock(dut)

    # Write the data to instruction memory
    for i in range(set_parameters.INST_MEM_DEPTH):
        await write_inst_mem(dut, i, golden_data_list[i])

    # Clear first
    clear_inputs_no_clock(dut)

    # Chunk size chosen
    # arbitrarily for test purposes only
    chunk_size = 10
    loop_size = 3

    # Loop values
    loop1_end_addr = random.randint(5, 5 + chunk_size)
    loop2_end_addr = random.randint(loop1_end_addr + 1, loop1_end_addr + chunk_size)
    loop3_end_addr = random.randint(loop2_end_addr + 1, loop2_end_addr + chunk_size)

    loop1_count = random.randint(2, 2 + loop_size)
    loop2_count = random.randint(loop1_count + 1, loop1_count + loop_size)
    loop3_count = random.randint(loop2_count + 1, loop2_count + loop_size)

    cocotb.log.info(" ------------------------------------------ ")
    cocotb.log.info(
        f"loop1_end: {loop1_end_addr}; \
        loop2_end: {loop2_end_addr}; \
        loop3_end: {loop3_end_addr};"
    )
    cocotb.log.info(
        f"loop1_count: {loop1_count}; \
        loop2_count: {loop2_count}; \
        loop3_count: {loop3_count};"
    )
    cocotb.log.info(" ------------------------------------------ ")

    # Start the system
    dut.start_i.value = 1

    dut.inst_loop_mode_i.value = 3
    dut.inst_loop_jump_addr1_i.value = 0
    dut.inst_loop_jump_addr2_i.value = 0
    dut.inst_loop_jump_addr3_i.value = 0
    dut.inst_loop_end_addr1_i.value = loop1_end_addr
    dut.inst_loop_end_addr2_i.value = loop2_end_addr
    dut.inst_loop_end_addr3_i.value = loop3_end_addr
    dut.inst_loop_count_addr1_i.value = loop1_count
    dut.inst_loop_count_addr2_i.value = loop2_count
    dut.inst_loop_count_addr3_i.value = loop3_count

    await clock_and_time(dut.clk_i)

    # Clear
    dut.start_i.value = 0

    # Check for PC if it's correct
    # But consider the 3D loop

    # Initialize the golden workgin address
    current_addr = 0

    for i in range(loop3_count):
        for j in range(loop2_count):
            for k in range(loop1_count):
                current_addr = 0
                while current_addr <= loop1_end_addr:
                    # Extract the 1st data that is readily available
                    pc_val = dut.inst_pc_o.value.integer
                    inst_data_val = dut.inst_rd_o.value.integer

                    check_result(pc_val, current_addr)
                    check_result(inst_data_val, golden_data_list[current_addr])

                    await clock_and_time(dut.clk_i)
                    current_addr += 1

            while current_addr <= loop2_end_addr:
                # Extract the 1st data that is readily available
                pc_val = dut.inst_pc_o.value.integer
                inst_data_val = dut.inst_rd_o.value.integer

                check_result(pc_val, current_addr)
                check_result(inst_data_val, golden_data_list[current_addr])

                await clock_and_time(dut.clk_i)
                current_addr += 1

        while current_addr <= loop3_end_addr:
            # Extract the 1st data that is readily available
            pc_val = dut.inst_pc_o.value.integer
            inst_data_val = dut.inst_rd_o.value.integer

            check_result(pc_val, current_addr)
            check_result(inst_data_val, golden_data_list[current_addr])

            await clock_and_time(dut.clk_i)
            current_addr += 1

    for i in range(10):
        await clock_and_time(dut.clk_i)


# Actual test run
@pytest.mark.parametrize(
    "parameters",
    [
        {
            "RegAddrWidth": str(set_parameters.REG_FILE_WIDTH),
            "InstMemDepth": str(set_parameters.INST_MEM_DEPTH),
        }
    ],
)
def test_inst_control(simulator, parameters, waves):
    verilog_sources = [
        "/rtl/common/reg_file_1w1r.sv",
        "/rtl/inst_memory/inst_loop_control.sv",
        "/rtl/inst_memory/inst_control.sv",
    ]

    toplevel = "inst_control"

    module = "test_inst_control"

    setup_and_run(
        verilog_sources=verilog_sources,
        toplevel=toplevel,
        module=module,
        simulator=simulator,
        parameters=parameters,
        waves=waves,
    )
