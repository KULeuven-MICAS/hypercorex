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
    load_im_list,
    load_am_list,
    read_qhv,
    read_predict,
    numbin2list,
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

from hdc_util import gen_ca90_im_set  # noqa: E402
from char_recog import (  # noqa: E402
    train_char_recog,
    convert_to_data_indices,
    char_recog_dataset,
)

compiler_path = get_root() + "/sw/"
print(f"Adding SW functions from: {compiler_path}")
sys.path.append(compiler_path)

from hypercorex_compiler import compile_hypercorex_asm  # noqa: E402

# Some parameters about the character recognition set
TOTAL_PIXEL_FEATURES = 35
THRESHOLD = TOTAL_PIXEL_FEATURES / 2
NUM_CLASSES = 26


# Actual test routines
@cocotb.test()
async def tb_hypercorex_dut(dut):
    cocotb.log.info(" ------------------------------------------ ")
    cocotb.log.info("       Testing Character Recognition        ")
    cocotb.log.info(" ------------------------------------------ ")

    # Extract data set
    dataset_file_path = get_dir() + "/../hdc_exp/data_set/char_recog/characters.txt"
    cocotb.log.info(f"Extracting data from: {dataset_file_path}")
    dataset = char_recog_dataset(dataset_file_path)

    # Extract asm file
    inst_file_path = get_dir() + "/../sw/asm/train_char_recog.asm"
    cocotb.log.info(f"Extracting instructions from: {inst_file_path}")
    inst_code_list, control_code_list = compile_hypercorex_asm(inst_file_path)

    # Convert each instruction to integers for input
    for i in range(len(inst_code_list)):
        inst_code_list[i] = hvlist2num(np.array(inst_code_list[i]))

    # Convert data set to index-based encoding
    index_based_dataset = convert_to_data_indices(dataset)

    # Get a CA90 seed that's working
    im_seed_list, ortho_im, conf_mat = gen_ca90_im_set(
        seed_size=set_parameters.SEED_DIM,
        hv_dim=set_parameters.HV_DIM,
        num_total_im=set_parameters.NUM_TOT_IM,
        num_per_im_bank=set_parameters.NUM_PER_IM_BANK,
        base_seeds=set_parameters.ORTHO_IM_SEEDS,
        gen_seed=True,
        ca90_mode=set_parameters.CA90_MODE,
    )

    # Train the character recognition model
    assoc_mem = train_char_recog(
        dataset=dataset,
        hv_dim=set_parameters.HV_DIM,
        ortho_im=ortho_im,
        threshold=THRESHOLD,
        non_perm_encode=True,
        hv_type="binary",
    )

    # Assoc mem integer list
    assoc_mem_int = []
    for i in range(len(assoc_mem)):
        assoc_mem_int.append(hvlist2num(assoc_mem[i]))

    # Correct data set
    correct_set = list(range(NUM_CLASSES))

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
    for i in range(set_parameters.TEST_RUNS):
        await load_im_list(
            dut, index_based_dataset[i], i * len(index_based_dataset[i]), "A", "low"
        )

    cocotb.log.info(" ------------------------------------------ ")
    cocotb.log.info("               Load Data to AM              ")
    cocotb.log.info(" ------------------------------------------ ")

    await load_am_list(dut, assoc_mem_int, 0)

    # Enable memories when done loading
    dut.enable_mem_i.value = 1

    cocotb.log.info(" ------------------------------------------ ")
    cocotb.log.info("              Write IM Seeds                ")
    cocotb.log.info(" ------------------------------------------ ")

    # This writes to IM seeds
    for i in range(set_parameters.NUM_IM_SETS):
        await write_csr(dut, set_parameters.IM_BASE_SEED_REG_ADDR + i, im_seed_list[i])

    # Next check the IM seeds
    for i in range(set_parameters.NUM_IM_SETS):
        read_im_seed = await read_csr(dut, set_parameters.IM_BASE_SEED_REG_ADDR + i)
        check_result(im_seed_list[i], read_im_seed)

    cocotb.log.info(" ------------------------------------------ ")
    cocotb.log.info("       Write to Number of Predictions       ")
    cocotb.log.info(" ------------------------------------------ ")

    num_predict = NUM_CLASSES
    await write_csr(dut, set_parameters.AM_NUM_PREDICT_REG_ADDR, num_predict)

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
        val2=4,
        val3=0,
        data_width=set_parameters.INST_MEM_ADDR_WIDTH,
    )

    # Write loop count
    loop_count = await config_inst_ctrl(
        dut=dut,
        reg_addr=set_parameters.INST_LOOP_COUNT_REG_ADDR,
        val1=TOTAL_PIXEL_FEATURES,
        val2=set_parameters.TEST_RUNS,
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

    # There are two ways to check the output
    # one is from the QHV memory, while the other is from
    # the lowdim AM prediction memory
    cocotb.log.info(" ------------------------------------------ ")
    cocotb.log.info("          Reading from QHV Memory           ")
    cocotb.log.info(" ------------------------------------------ ")

    for i in range(set_parameters.TEST_RUNS):
        qhv_val = await read_qhv(dut, i)
        qhv_val = numbin2list(qhv_val, set_parameters.HV_DIM)
        check_result_array(assoc_mem[i], qhv_val)

    cocotb.log.info(" ------------------------------------------ ")
    cocotb.log.info("        Reading from Predict Memory         ")
    cocotb.log.info(" ------------------------------------------ ")

    for i in range(set_parameters.TEST_RUNS):
        predict_val = await read_predict(dut, i)
        check_result(predict_val, correct_set[i])

    # Some trailing cycles only
    for i in range(100):
        await clock_and_time(dut.clk_i)


# Config and run
@pytest.mark.parametrize(
    "parameters",
    [
        {
            # General parameters
            "HVDimension": str(set_parameters.HV_DIM),
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
def test_hypercorex_char_recog(simulator, parameters, waves):
    bender_path = bender_path = get_dir() + "/../."
    bender_filelist = get_bender_filelist(bender_path)
    print(bender_filelist)
    verilog_sources = bender_filelist
    toplevel = "tb_hypercorex"

    module = "test_hypercorex_char_recog"

    setup_and_run(
        verilog_sources=verilog_sources,
        toplevel=toplevel,
        module=module,
        simulator=simulator,
        parameters=parameters,
        waves=waves,
        bender_filelist=True,
    )
