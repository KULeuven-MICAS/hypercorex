"""
  Copyright 2024 KU Leuven
  Ryan Antonio <ryan.antonio@esat.kuleuven.be>

  Description:
  This tests the hypercorex's CSR RW functionality.
"""

import set_parameters
from util import (
    # Filelist management
    get_dir,
    get_bender_filelist,
    # General imports
    get_root,
    setup_and_run,
    hvlist2num,
    clock_and_time,
    check_result,
    check_result_array,
    clear_tb_inputs,
    write_csr,
    read_csr,
    read_qhv,
    numbin2list,
    config_inst_ctrl,
    load_im_list,
)

import cocotb
from cocotb.clock import Clock
import sys
import pytest
import numpy as np

# Add hdc utility functions
hdc_util_path = get_root() + "/hdc_exp/"
print(f"Adding HDC utility functions from: {hdc_util_path}")
sys.path.append(hdc_util_path)

from system_regression import data_autofetch_bind  # noqa: E402

compiler_path = get_root() + "/sw/"
print(f"Adding SW functions from: {compiler_path}")
sys.path.append(compiler_path)

from hypercorex_compiler import compile_hypercorex_asm  # noqa: E402


# Actual test routines
@cocotb.test()
async def tb_hypercorex_dut(dut):
    cocotb.log.info(" ------------------------------------------ ")
    cocotb.log.info("       Testing Orthoginal iM Check          ")
    cocotb.log.info(" ------------------------------------------ ")

    # Extract data set
    ortho_im, golden_data = data_autofetch_bind(
        seed_size=set_parameters.SEED_DIM,
        hv_dim=set_parameters.HV_DIM,
        num_total_im=set_parameters.NUM_TOT_IM,
        num_per_im_bank=set_parameters.NUM_PER_IM_BANK,
        base_seeds=set_parameters.ORTHO_IM_SEEDS,
        gen_seed=True,
        ca90_mode=set_parameters.CA90_MODE,
    )

    # Extract asm file
    inst_file_path = get_dir() + "/../sw/asm/sysreg_imab_bind.asm"
    cocotb.log.info(f"Extracting instructions from: {inst_file_path}")
    inst_code_list, control_code_list = compile_hypercorex_asm(inst_file_path)

    # Convert each instruction to integers for input
    for i in range(len(inst_code_list)):
        inst_code_list[i] = hvlist2num(np.array(inst_code_list[i]))

    # Initialize input values
    clear_tb_inputs(dut)

    # Reset always
    dut.rst_ni.value = 0

    # We need to preload data into the memories
    dut.enable_mem_i.value = 0

    # Initialize clock always
    clock = Clock(dut.clk_i, 10, units="ns")
    cocotb.start_soon(clock.start(start_high=False))

    # Wait one cycle for reset
    await clock_and_time(dut.clk_i)

    # Release reset
    dut.rst_ni.value = 1

    # Assume CSR response is always ready to receive
    dut.csr_rsp_ready_i.value = 1

    cocotb.log.info(" ------------------------------------------ ")
    cocotb.log.info("          Load Data to HighDim IMA          ")
    cocotb.log.info(" ------------------------------------------ ")

    # Half of ortho_im to load
    half_ortho_im = len(ortho_im) // 2
    lower_ortho_im_half = []
    upper_ortho_im_half = []

    for i in range(half_ortho_im):
        lower_ortho_im_half.append(hvlist2num(ortho_im[i]))
        upper_ortho_im_half.append(hvlist2num(ortho_im[half_ortho_im + i]))

    # Load list to A
    await load_im_list(dut, lower_ortho_im_half, 0, "A", "high")

    # Load list to B
    await load_im_list(dut, upper_ortho_im_half, 0, "B", "high")

    # We need to preload data into the memories
    dut.enable_mem_i.value = 1
    await clock_and_time(dut.clk_i)

    cocotb.log.info(" ------------------------------------------ ")
    cocotb.log.info("         Write to Instruction Memory        ")
    cocotb.log.info(" ------------------------------------------ ")

    # Enable first the write mode and debug mode
    inst_ctrl_code = 0x0000_0003
    await write_csr(dut, set_parameters.INST_CTRL_REG_ADDR, inst_ctrl_code)

    # Write to instruction memory
    # While writing we can check the current program counter
    for i in range(len(inst_code_list)):
        read_inst_addr = await read_csr(dut, set_parameters.INST_PC_ADDR_REG_ADDR)
        check_result(i, read_inst_addr)
        await write_csr(dut, set_parameters.INST_WRITE_DATA_REG_ADDR, inst_code_list[i])

    # Using the debug address we can read the instructions
    for i in range(len(inst_code_list)):
        await write_csr(dut, set_parameters.INST_RDDBG_ADDR_REG_ADDR, i)
        read_inst = await read_csr(dut, set_parameters.INST_INST_AT_ADDR_ADDR_REG_ADDR)
        check_result(inst_code_list[i], read_inst)

    # Deactivate debug mode and clear program counter
    inst_ctrl_code = 0x0000_0004
    await write_csr(dut, set_parameters.INST_CTRL_REG_ADDR, inst_ctrl_code)

    cocotb.log.info(" ------------------------------------------ ")
    cocotb.log.info("         Encoding Loops and Jumps           ")
    cocotb.log.info(" ------------------------------------------ ")

    # Write loop control
    loop_ctrl_code = 0x0000_0001
    await write_csr(dut, set_parameters.INST_LOOP_CTRL_REG_ADDR, loop_ctrl_code)

    # Write loop jump address
    # Combination of loop 1, loop 2, and loop 3
    loop_jump_addr = await config_inst_ctrl(
        dut=dut,
        reg_addr=set_parameters.INST_LOOP_JUMP_ADDR_REG_ADDR,
        val1=0,
        val2=0,
        val3=0,
        data_width=set_parameters.INST_MEM_ADDR_WIDTH,
    )

    # Write loop end address
    loop_end_addr = await config_inst_ctrl(
        dut=dut,
        reg_addr=set_parameters.INST_LOOP_END_ADDR_REG_ADDR,
        val1=2,
        val2=0,
        val3=0,
        data_width=set_parameters.INST_MEM_ADDR_WIDTH,
    )

    # Write loop count
    # Note that we are reading out all ortho im values
    loop_count = await config_inst_ctrl(
        dut=dut,
        reg_addr=set_parameters.INST_LOOP_COUNT_REG_ADDR,
        val1=half_ortho_im,
        val2=0,
        val3=0,
        data_width=set_parameters.INST_MEM_ADDR_WIDTH,
    )

    # Check if the loop control is written correctly
    read_loop_ctrl = await read_csr(dut, set_parameters.INST_LOOP_CTRL_REG_ADDR)
    check_result(loop_ctrl_code, read_loop_ctrl)

    # Check if the loop jump address is written correctly
    read_loop_jump_addr = await read_csr(
        dut, set_parameters.INST_LOOP_JUMP_ADDR_REG_ADDR
    )
    check_result(loop_jump_addr, read_loop_jump_addr)

    # Check if the loop end address is written correctly
    read_loop_end_addr = await read_csr(dut, set_parameters.INST_LOOP_END_ADDR_REG_ADDR)
    check_result(loop_end_addr, read_loop_end_addr)

    # Check if the loop count is written correctly
    read_loop_count = await read_csr(dut, set_parameters.INST_LOOP_COUNT_REG_ADDR)
    check_result(loop_count, read_loop_count)

    cocotb.log.info(" ------------------------------------------ ")
    cocotb.log.info("          Set to get data from TCDM         ")
    cocotb.log.info(" ------------------------------------------ ")

    # Write to control registers
    core_ctrl_code = 0x0000_0030
    await write_csr(dut, set_parameters.CORE_SET_REG_ADDR, core_ctrl_code)

    cocotb.log.info(" ------------------------------------------ ")
    cocotb.log.info("               Start the Core               ")
    cocotb.log.info(" ------------------------------------------ ")

    # Write to control regiysters
    core_ctrl_code = 0x0000_0031
    await write_csr(dut, set_parameters.CORE_SET_REG_ADDR, core_ctrl_code)

    cocotb.log.info(" ------------------------------------------ ")
    cocotb.log.info("          Poll until Core Finishes          ")
    cocotb.log.info(" ------------------------------------------ ")

    while True:
        busy_signal = await read_csr(dut, set_parameters.CORE_SET_REG_ADDR)
        busy_signal = (busy_signal >> 1) & 0x0000_0001

        if not busy_signal:
            break

    # Check from QHV memory if we have the correct number of orthogonal signals
    # one is from the QHV memory, while the other is from
    # the lowdim AM prediction memory
    cocotb.log.info(" ------------------------------------------ ")
    cocotb.log.info("          Reading from QHV Memory           ")
    cocotb.log.info(" ------------------------------------------ ")

    for i in range(len(golden_data)):
        qhv_val = await read_qhv(dut, i)
        qhv_val = numbin2list(qhv_val, set_parameters.HV_DIM)
        check_result_array(golden_data[i], qhv_val)

    # Some trailing cycles only
    for i in range(100):
        await clock_and_time(dut.clk_i)


# Config and run
@pytest.mark.parametrize(
    "parameters",
    [
        {
            # Enable ROM IM
            "EnableRomIM": str(set_parameters.ENABLE_ROM_IM),
            # General parameters
            "HVDimension": str(set_parameters.HV_DIM),
            "LowDimWidth": str(set_parameters.NARROW_DATA_WIDTH),
            # CSR parameters
            "CsrDataWidth": str(set_parameters.REG_FILE_WIDTH),
            "CsrAddrWidth": str(set_parameters.REG_FILE_WIDTH),
            # Item memory parameters
            "NumTotIm": str(set_parameters.NUM_TOT_IM),
            "NumPerImBank": str(set_parameters.NUM_PER_IM_BANK),
            "ImAddrWidth": str(set_parameters.REG_FILE_WIDTH),
            "SeedWidth": str(set_parameters.REG_FILE_WIDTH),
            "HoldFifoDepth": str(set_parameters.IM_FIFO_DEPTH),
            # Instruction memory parameters
            "InstMemDepth": str(set_parameters.INST_MEM_DEPTH),
            # HDC encoder parameters
            "BundCountWidth": str(set_parameters.BUNDLER_COUNT_WIDTH),
            "BundMuxWidth": str(set_parameters.BUNDLER_MUX_WIDTH),
            "ALUMuxWidth": str(set_parameters.ALU_MUX_WIDTH),
            "ALUMaxShiftAmt": str(set_parameters.ALU_MAX_SHIFT),
            "RegMuxWidth": str(set_parameters.REG_MUX_WIDTH),
            "QvMuxWidth": str(set_parameters.QHV_MUX_WIDTH),
            "RegNum": str(set_parameters.REG_NUM),
        }
    ],
)
def test_hypercorex_imab_bind(simulator, parameters, waves):
    bender_path = bender_path = get_dir() + "/../."
    bender_filelist = get_bender_filelist(bender_path)
    verilog_sources = bender_filelist
    toplevel = "tb_hypercorex"

    module = "test_hypercorex_imab_bind"

    setup_and_run(
        verilog_sources=verilog_sources,
        toplevel=toplevel,
        module=module,
        simulator=simulator,
        parameters=parameters,
        waves=waves,
        bender_filelist=True,
    )