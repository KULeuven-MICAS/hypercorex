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
    clear_tb_inputs,
    write_csr,
    read_csr,
    load_im_list,
    load_am_list,
    read_predict,
    config_inst_ctrl,
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

from hdc_util import (  # noqa: E402
    load_am_model,
    load_dataset,
    pack_ld_to_hd,
)

compiler_path = get_root() + "/sw/"
print(f"Adding SW functions from: {compiler_path}")
sys.path.append(compiler_path)

from hypercorex_compiler import compile_hypercorex_asm  # noqa: E402

# Special function for packing data

# Some parameters about the digit recognition set
NUM_CLASSES = 10
NUM_FEATURES = 28 * 28
NUM_PREDICTIONS = 10


# Actual test routines
@cocotb.test()
async def tb_hypercorex_dut(dut):
    cocotb.log.info(" ------------------------------------------ ")
    cocotb.log.info("         Testing Digit Recognition          ")
    cocotb.log.info(" ------------------------------------------ ")

    # Extract data set
    assoc_mem_fp = get_dir() + "/../hemaia/trained_am/hypx_digit_am.txt"
    cocotb.log.info(f"Get trained AM: {assoc_mem_fp}")
    assoc_mem = load_am_model(assoc_mem_fp)

    # Assoc mem integer list
    assoc_mem_int = []
    for i in range(len(assoc_mem)):
        assoc_mem_int.append(hvlist2num(assoc_mem[i]))

    # Extract samples
    test_samples_fp = get_dir() + "/../hemaia/test_samples/hypx_digit_test.txt"
    cocotb.log.info(f"Get trained AM: {test_samples_fp}")
    test_samples = load_dataset(test_samples_fp)

    # Compress 8-bit data into a 64-bit data
    test_samples_compressed = []
    for i in range(len(test_samples)):
        compressed_sample = pack_ld_to_hd(test_samples[i], 4, 64)
        test_samples_compressed.append(compressed_sample)

    # Extract asm file
    inst_file_path = get_dir() + "/../sw/asm/test_digit_recog.asm"
    cocotb.log.info(f"Extracting instructions from: {inst_file_path}")
    inst_code_list, control_code_list = compile_hypercorex_asm(inst_file_path)

    # Convert each instruction to integers for input
    for i in range(len(inst_code_list)):
        inst_code_list[i] = hvlist2num(np.array(inst_code_list[i]))

    # Initialize input values
    clear_tb_inputs(dut)

    # Reset always
    dut.rst_ni.value = 0

    # Initialize hard static values
    dut.enable_mem_i.value = 0

    # This needs to be the number of classes to check
    dut.am_auto_loop_addr_i.value = NUM_CLASSES - 1

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
    cocotb.log.info("           Load Data to LowDim IMA          ")
    cocotb.log.info(" ------------------------------------------ ")

    # Load list to A
    test_sub_samples = test_samples_compressed[:NUM_PREDICTIONS]
    test_sub_samples_len = len(test_samples_compressed[0])
    for i in range(NUM_PREDICTIONS):
        await load_im_list(
            dut, test_sub_samples[i], i * test_sub_samples_len, "A", "low"
        )

    cocotb.log.info(" ------------------------------------------ ")
    cocotb.log.info("               Load Data to AM              ")
    cocotb.log.info(" ------------------------------------------ ")

    await load_am_list(dut, assoc_mem_int, 0)

    # Enable memories when done loading
    dut.enable_mem_i.value = 1

    cocotb.log.info(" ------------------------------------------ ")
    cocotb.log.info("       Write to Number of Predictions       ")
    cocotb.log.info(" ------------------------------------------ ")

    num_classes = NUM_CLASSES
    await write_csr(dut, set_parameters.AM_NUM_PREDICT_REG_ADDR, num_classes)

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
    loop_ctrl_code = 0x0000_0002
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
        val1=0,
        val2=3,
        val3=0,
        data_width=set_parameters.INST_MEM_ADDR_WIDTH,
    )

    # Write loop count
    loop_count = await config_inst_ctrl(
        dut=dut,
        reg_addr=set_parameters.INST_LOOP_COUNT_REG_ADDR,
        val1=NUM_FEATURES,
        val2=NUM_PREDICTIONS,
        val3=0,
        data_width=set_parameters.INST_LOOP_COUNT_WIDTH,
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
    cocotb.log.info("         Configure Data Slice Mode          ")
    cocotb.log.info(" ------------------------------------------ ")

    # Set port A to be the data slicing mode in 4bit sequence
    # Set port B to be coming from the auto generator
    data_src_ctrl = 0x0000_0022
    await write_csr(dut, set_parameters.DATA_SRC_CTRL_REG_ADDR, data_src_ctrl)

    # Check if write is correct
    read_data_src_ctrl = await read_csr(dut, set_parameters.DATA_SRC_CTRL_REG_ADDR)
    check_result(data_src_ctrl, read_data_src_ctrl)

    # Configure A number of elements to be auto-sliced
    data_slice_num_elem_a = NUM_FEATURES
    await write_csr(
        dut, set_parameters.DATA_SLICE_NUM_ELEM_A_REG_ADDR, data_slice_num_elem_a
    )

    # Check if write is correct
    read_data_slice_num_elem_a = await read_csr(
        dut, set_parameters.DATA_SLICE_NUM_ELEM_A_REG_ADDR
    )
    check_result(data_slice_num_elem_a, read_data_slice_num_elem_a)

    # Configure B for auto counting
    data_src_auto_start_b = 2
    data_src_auto_num_b = NUM_FEATURES

    await write_csr(
        dut, set_parameters.DATA_SRC_AUTO_START_B_REG_ADDR, data_src_auto_start_b
    )
    await write_csr(
        dut, set_parameters.DATA_SRC_AUTO_NUM_B_REG_ADDR, data_src_auto_num_b
    )

    # Check if write is correct
    read_data_src_auto_start_b = await read_csr(
        dut, set_parameters.DATA_SRC_AUTO_START_B_REG_ADDR
    )
    check_result(data_src_auto_start_b, read_data_src_auto_start_b)

    # Check if write is correct
    read_data_src_auto_num_b = await read_csr(
        dut, set_parameters.DATA_SRC_AUTO_NUM_B_REG_ADDR
    )
    check_result(data_src_auto_num_b, read_data_src_auto_num_b)

    cocotb.log.info(" ------------------------------------------ ")
    cocotb.log.info("               Start the Core               ")
    cocotb.log.info(" ------------------------------------------ ")

    # Write to control registers
    core_ctrl_code = 0x0000_0001
    await write_csr(dut, set_parameters.CORE_SET_REG_ADDR, core_ctrl_code)

    cocotb.log.info(" ------------------------------------------ ")
    cocotb.log.info("          Poll until Core Finishes          ")
    cocotb.log.info(" ------------------------------------------ ")

    while True:
        busy_signal = await read_csr(dut, set_parameters.CORE_SET_REG_ADDR)
        busy_signal = (busy_signal >> 1) & 0x0000_0001

        if not busy_signal:
            break

    cocotb.log.info(" ------------------------------------------ ")
    cocotb.log.info("        Reading from Predict Memory         ")
    cocotb.log.info(" ------------------------------------------ ")

    correct_set = list(range(NUM_PREDICTIONS))
    # A nasty workaround since 1st item is not a 0

    for i in range(set_parameters.TEST_RUNS):
        predict_val = await read_predict(dut, i)
        check_result(predict_val, correct_set[i])

    cocotb.log.info(" ------------------------------------------ ")
    cocotb.log.info("       Activate Reset to Run Again          ")
    cocotb.log.info(" ------------------------------------------ ")
    # First reset the memory
    dut.enable_mem_i.value = 0
    await clock_and_time(dut.clk_i)

    # Apply register resets
    core_ctrl_code = 0x0000_0380
    await write_csr(dut, set_parameters.CORE_SET_REG_ADDR, core_ctrl_code)

    # Enable the memory
    dut.enable_mem_i.value = 1
    await clock_and_time(dut.clk_i)

    # Start the system again
    core_ctrl_code = 0x0000_0001
    await write_csr(dut, set_parameters.CORE_SET_REG_ADDR, core_ctrl_code)

    cocotb.log.info(" ------------------------------------------ ")
    cocotb.log.info("          Poll until Core Finishes          ")
    cocotb.log.info(" ------------------------------------------ ")

    while True:
        busy_signal = await read_csr(dut, set_parameters.CORE_SET_REG_ADDR)
        busy_signal = (busy_signal >> 1) & 0x0000_0001

        if not busy_signal:
            break

    cocotb.log.info(" ------------------------------------------ ")
    cocotb.log.info("        Reading from Predict Memory         ")
    cocotb.log.info(" ------------------------------------------ ")

    correct_set = list(range(NUM_PREDICTIONS))
    # A nasty workaround since 1st item is not a 0

    for i in range(set_parameters.TEST_RUNS):
        predict_val = await read_predict(dut, i)
        check_result(predict_val, correct_set[i])

    # Some trailing cycles only
    for i in range(500):
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
def test_hypercorex_reset_run(simulator, parameters, waves):
    bender_path = bender_path = get_dir() + "/../."
    bender_filelist = get_bender_filelist(bender_path)
    verilog_sources = bender_filelist
    toplevel = "tb_hypercorex"

    module = "test_hypercorex_reset_run"

    setup_and_run(
        verilog_sources=verilog_sources,
        toplevel=toplevel,
        module=module,
        simulator=simulator,
        parameters=parameters,
        waves=waves,
        bender_filelist=True,
    )
