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
    gen_rand_bits,
    clock_and_time,
    check_result,
    clear_tb_inputs,
    write_csr,
    read_csr,
)

import cocotb
from cocotb.clock import Clock
import sys
import pytest

# Add hdc utility functions
hdc_util_path = get_root() + "/hdc_exp/"
print(hdc_util_path)
sys.path.append(hdc_util_path)


# Actual test routines
@cocotb.test()
async def tb_hypercorex_dut(dut):
    cocotb.log.info(" ------------------------------------------ ")
    cocotb.log.info("            Testing Hypercorex              ")
    cocotb.log.info(" ------------------------------------------ ")

    # Initialize input values
    clear_tb_inputs(dut)

    # Reset always
    dut.rst_ni.value = 0

    # Initialize hard static values
    dut.am_auto_loop_addr_i.value = 0
    dut.enable_mem_i.value = 0

    # Initialize clock always
    clock = Clock(dut.clk_i, 10, units="ns")
    cocotb.start_soon(clock.start(start_high=False))

    # Wait one cycle for reset
    await clock_and_time(dut.clk_i)

    dut.rst_ni.value = 1

    # Assume CSR response is always ready to receive
    dut.csr_rsp_ready_i.value = 1

    cocotb.log.info(" ------------------------------------------ ")
    cocotb.log.info("         Write to CiM and IM Seeds          ")
    cocotb.log.info(" ------------------------------------------ ")

    # Generate random CIM seed
    cim_seed = gen_rand_bits(set_parameters.REG_FILE_WIDTH)

    # Generate random IM seeds
    im_seed_list = []
    for i in range(set_parameters.NUM_IM_SETS):
        im_seed_list.append(gen_rand_bits(set_parameters.REG_FILE_WIDTH))

    # Write seeds to the CiM and IM

    # This writes to CiM seed
    await write_csr(dut, set_parameters.CIM_SEED_REG_ADDR, cim_seed)

    # This writes to IM seeds
    for i in range(set_parameters.NUM_IM_SETS):
        await write_csr(dut, set_parameters.IM_BASE_SEED_REG_ADDR + i, im_seed_list[i])

    # Verify if the seeds are written correctly
    # First check the CIM seed
    read_cim_seed = await read_csr(dut, set_parameters.CIM_SEED_REG_ADDR)
    check_result(cim_seed, read_cim_seed)

    # Next check the IM seeds
    for i in range(set_parameters.NUM_IM_SETS):
        read_im_seed = await read_csr(dut, set_parameters.IM_BASE_SEED_REG_ADDR + i)
        check_result(im_seed_list[i], read_im_seed)

    cocotb.log.info(" ------------------------------------------ ")
    cocotb.log.info("       Writing to Instruction Memory        ")
    cocotb.log.info(" ------------------------------------------ ")

    inst_list = []
    for i in range(set_parameters.INST_MEM_DEPTH):
        inst_list.append(gen_rand_bits(set_parameters.REG_FILE_WIDTH))

    # Enable first the write mode and debug mode
    inst_data_write = 0x0000_0003
    await write_csr(dut, set_parameters.INST_CTRL_REG_ADDR, inst_data_write)

    # Verify and check if the instruction mode is written correctly
    read_inst_ctrl = await read_csr(dut, set_parameters.INST_CTRL_REG_ADDR)
    check_result(inst_data_write, read_inst_ctrl)

    # Write to instruction memory
    # While writing we can check the current program counter
    for i in range(set_parameters.INST_MEM_DEPTH):
        read_inst_addr = await read_csr(dut, set_parameters.INST_PC_ADDR_REG_ADDR)
        check_result(i, read_inst_addr)
        await write_csr(dut, set_parameters.INST_WRITE_DATA_REG_ADDR, inst_list[i])

    # Using the debug address we can read the instructions
    for i in range(set_parameters.INST_MEM_DEPTH):
        await write_csr(dut, set_parameters.INST_RDDBG_ADDR_REG_ADDR, i)
        read_inst = await read_csr(dut, set_parameters.INST_INST_AT_ADDR_ADDR_REG_ADDR)
        check_result(inst_list[i], read_inst)

    # Check if some WO signals return 0
    read_inst_ctrl = await read_csr(dut, set_parameters.INST_WRITE_ADDR_REG_ADDR)
    check_result(0, read_inst_ctrl)

    read_inst_ctrl = await read_csr(dut, set_parameters.INST_WRITE_DATA_REG_ADDR)
    check_result(0, read_inst_ctrl)

    cocotb.log.info(" ------------------------------------------ ")
    cocotb.log.info("     Writing to Loop Control Registers      ")
    cocotb.log.info(" ------------------------------------------ ")

    # Write to inst loop mode
    golden_val = gen_rand_bits(set_parameters.REG_FILE_WIDTH)
    await write_csr(dut, set_parameters.INST_LOOP_CTRL_REG_ADDR, golden_val)

    # Read back the value
    read_val = await read_csr(dut, set_parameters.INST_LOOP_CTRL_REG_ADDR)
    # Mask only the lower 2 bits
    check_result((golden_val & 0x0000_0003), read_val)

    # General mask for the 3*INST_MEM_ADDR_WIDTH bits of loop registers
    mask = (
        (set_parameters.INST_MEM_DEPTH - 1)
        | ((set_parameters.INST_MEM_DEPTH - 1) << set_parameters.INST_MEM_ADDR_WIDTH)
        | (
            (set_parameters.INST_MEM_DEPTH - 1)
            << 2 * set_parameters.INST_MEM_ADDR_WIDTH
        )
    )

    # Write to inst loop jump
    golden_val = gen_rand_bits(set_parameters.REG_FILE_WIDTH)
    await write_csr(dut, set_parameters.INST_LOOP_JUMP_ADDR_REG_ADDR, golden_val)

    # Read back the value
    read_val = await read_csr(dut, set_parameters.INST_LOOP_JUMP_ADDR_REG_ADDR)
    # Mask only the lower 3*INST_MEM_ADDR_WIDTH bits
    check_result((golden_val & mask), read_val)

    # Write to inst loop end
    golden_val = gen_rand_bits(set_parameters.REG_FILE_WIDTH)
    await write_csr(dut, set_parameters.INST_LOOP_END_ADDR_REG_ADDR, golden_val)

    # Read back the value
    read_val = await read_csr(dut, set_parameters.INST_LOOP_END_ADDR_REG_ADDR)
    # Mask only the lower 3*INST_MEM_ADDR_WIDTH bits
    check_result((golden_val & mask), read_val)

    # Write to inst loop count
    golden_val = gen_rand_bits(set_parameters.REG_FILE_WIDTH)
    await write_csr(dut, set_parameters.INST_LOOP_COUNT_REG_ADDR, golden_val)

    # Read back the value
    read_val = await read_csr(dut, set_parameters.INST_LOOP_COUNT_REG_ADDR)
    # Mask only the lower 3*INST_MEM_ADDR_WIDTH bits
    check_result((golden_val & mask), read_val)

    # Some trailing cycles only
    for i in range(10):
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
def test_hypercorex_csr(simulator, parameters, waves):
    bender_path = bender_path = get_dir() + "/../."
    bender_filelist = get_bender_filelist(bender_path)
    print(bender_filelist)
    verilog_sources = bender_filelist

    toplevel = "tb_hypercorex"

    module = "test_hypercorex_csr"

    setup_and_run(
        verilog_sources=verilog_sources,
        toplevel=toplevel,
        module=module,
        simulator=simulator,
        parameters=parameters,
        waves=waves,
        bender_filelist=True,
    )
