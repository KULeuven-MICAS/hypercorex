"""
Copyright 2024 KU Leuven
Ryan Antonio <ryan.antonio@esat.kuleuven.be>

Description:
This tests the hypercorex's testbench memory
modules while compling with the hypercorex
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
    check_result_list,
    # Testbench functions
    clear_tb_inputs,
    load_im_list,
    read_im_list,
    load_am_list,
    read_am_list,
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

    # Initialize golden values
    golden_im_a_lowdim_data = []
    golden_im_a_highdim_data = []
    golden_im_b_lowdim_data = []
    golden_im_b_highdim_data = []
    golden_am_data = []

    for i in range(set_parameters.TEST_RUNS):
        golden_im_a_lowdim_data.append(gen_rand_bits(set_parameters.REG_FILE_WIDTH))
        golden_im_a_highdim_data.append(gen_rand_bits(set_parameters.HV_DIM))
        golden_im_b_lowdim_data.append(gen_rand_bits(set_parameters.REG_FILE_WIDTH))
        golden_im_b_highdim_data.append(gen_rand_bits(set_parameters.HV_DIM))
        golden_am_data.append(gen_rand_bits(set_parameters.REG_FILE_WIDTH))

    cocotb.log.info(" ------------------------------------------ ")
    cocotb.log.info("          Loading Data Unto IMs             ")
    cocotb.log.info(" ------------------------------------------ ")

    # Load data unto IMs
    await load_im_list(dut, golden_im_a_lowdim_data, 0, "A", "low")
    await load_im_list(dut, golden_im_a_highdim_data, 0, "A", "high")
    await load_im_list(dut, golden_im_b_lowdim_data, 0, "B", "low")
    await load_im_list(dut, golden_im_b_highdim_data, 0, "B", "high")
    await load_am_list(dut, golden_am_data, 0)

    # Sanity check to see if data is correctly loaded
    actual_lowdim_im_a_list = await read_im_list(
        dut, 0, set_parameters.TEST_RUNS, "A", "low"
    )
    actual_highdim_im_a_list = await read_im_list(
        dut, 0, set_parameters.TEST_RUNS, "A", "high"
    )
    actual_lowdim_im_b_list = await read_im_list(
        dut, 0, set_parameters.TEST_RUNS, "B", "low"
    )
    actual_highdim_im_b_list = await read_im_list(
        dut, 0, set_parameters.TEST_RUNS, "B", "high"
    )
    actual_am_list = await read_am_list(dut, 0, set_parameters.TEST_RUNS)

    # Check if data is correctly loaded
    check_result_list(golden_im_a_lowdim_data, actual_lowdim_im_a_list)
    check_result_list(golden_im_a_highdim_data, actual_highdim_im_a_list)
    check_result_list(golden_im_b_lowdim_data, actual_lowdim_im_b_list)
    check_result_list(golden_im_b_highdim_data, actual_highdim_im_b_list)
    check_result_list(golden_am_data, actual_am_list)

    # Some trailing cycles only
    for i in range(10):
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
def test_tb_hypercorex(simulator, parameters, waves):
    bender_path = bender_path = get_dir() + "/../."
    bender_filelist = get_bender_filelist(bender_path)
    print(bender_filelist)
    verilog_sources = bender_filelist

    toplevel = "tb_hypercorex"

    module = "test_tb_hypercorex"

    setup_and_run(
        verilog_sources=verilog_sources,
        toplevel=toplevel,
        module=module,
        simulator=simulator,
        parameters=parameters,
        waves=waves,
        bender_filelist=True,
    )
