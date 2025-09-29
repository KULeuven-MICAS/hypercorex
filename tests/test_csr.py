"""
  Copyright 2024 KU Leuven
  Ryan Antonio <ryan.antonio@esat.kuleuven.be>

  Description:
  This tests the csr registers if they are working.
  This is specific so tests are very specific.
  This test exhaustively goes through each register
  and checks if the output signals and functionality
  are correct
"""

import set_parameters
import cocotb
from cocotb.clock import Clock
from cocotb.triggers import Timer
import pytest

from util import setup_and_run, check_result, clock_and_time, gen_rand_bits


# Clear inputs first
def clear_inputs_no_clock(dut):
    dut.csr_req_data_i.value = 0
    dut.csr_req_addr_i.value = 0
    dut.csr_req_write_i.value = 0
    dut.csr_req_valid_i.value = 0
    return


# Writing to csr registers
async def write_csr(dut, data, addr):
    clear_inputs_no_clock(dut)
    dut.csr_req_data_i.value = data
    dut.csr_req_addr_i.value = addr
    dut.csr_req_write_i.value = 1
    dut.csr_req_valid_i.value = 1
    await clock_and_time(dut.clk_i)
    clear_inputs_no_clock(dut)
    return


# Reading from csr
# But simulate how to read combinationally
async def read_csr(dut, addr):
    clear_inputs_no_clock(dut)
    dut.csr_req_addr_i.value = addr
    dut.csr_req_write_i.value = 0
    dut.csr_req_valid_i.value = 1
    # Propagate time to get combinationally
    await Timer(1, units="ps")
    csr_val = dut.csr_rsp_data_o.value.integer
    # Propagate time to finish task
    await clock_and_time(dut.clk_i)
    clear_inputs_no_clock(dut)
    return csr_val


# Some parameters for use
MAX_REG_VAL = (2**set_parameters.REG_FILE_WIDTH) - 1
MAX_8B_VAL = (2**8) - 1


@cocotb.test()
async def csr_dut(dut):
    cocotb.log.info(" ------------------------------------------ ")
    cocotb.log.info("                  CSR Set                   ")
    cocotb.log.info(" ------------------------------------------ ")

    # Initialize input values
    clear_inputs_no_clock(dut)
    dut.rst_ni.value = 0

    # Initialize other signals
    # Put these to 1 for value checking
    dut.csr_busy_i.value = 1
    dut.csr_am_pred_i.value = MAX_8B_VAL
    dut.csr_am_pred_valid_i.value = 1
    dut.csr_inst_pc_i.value = set_parameters.INST_MEM_DEPTH - 1
    dut.csr_inst_at_addr_i.value = MAX_REG_VAL

    # Assume that host side is always ready
    dut.csr_rsp_ready_i.value = 1

    # Initialize clock always
    clock = Clock(dut.clk_i, 10, units="ns")
    cocotb.start_soon(clock.start(start_high=False))

    # Wait one cycle for reset
    await clock_and_time(dut.clk_i)

    dut.rst_ni.value = 1

    cocotb.log.info(" ------------------------------------------ ")
    cocotb.log.info("            Check Core Setting              ")
    cocotb.log.info(" ------------------------------------------ ")

    await write_csr(dut, MAX_REG_VAL, set_parameters.CORE_SET_REG_ADDR)

    # Check some signals at this instant
    test_val = dut.csr_start_o.value.integer
    check_result(test_val, 1)

    test_val = dut.csr_seq_test_mode_o.value.integer
    check_result(test_val, 1)

    test_val = dut.csr_port_a_cim_o.value.integer
    check_result(test_val, 3)

    test_val = dut.csr_port_b_cim_o.value.integer
    check_result(test_val, 1)

    test_val = dut.csr_clr_o.value.integer
    check_result(test_val, 1)

    test_val = dut.csr_fifo_clr_o.value.integer
    check_result(test_val, 1)

    test_val = dut.csr_regs_clr_o.value.integer
    check_result(test_val, 1)

    test_val = dut.csr_dslc_clr_o.value.integer
    check_result(test_val, 1)

    # Propagate time for some signals to return to 0
    await clock_and_time(dut.clk_i)

    # Check start and clear must return 0
    test_val = dut.csr_start_o.value.integer
    check_result(test_val, 0)

    test_val = dut.csr_seq_test_mode_o.value.integer
    check_result(test_val, 1)

    test_val = dut.csr_port_a_cim_o.value.integer
    check_result(test_val, 3)

    test_val = dut.csr_port_b_cim_o.value.integer
    check_result(test_val, 1)

    test_val = dut.csr_clr_o.value.integer
    check_result(test_val, 0)

    # Request read and check if values are correct for return value
    csr_read_val = await read_csr(dut, set_parameters.CORE_SET_REG_ADDR)
    golden_val = int(0x0000_003E)

    check_result(csr_read_val, golden_val)

    cocotb.log.info(" ------------------------------------------ ")
    cocotb.log.info("           Check Num Predictions            ")
    cocotb.log.info(" ------------------------------------------ ")

    # Generate random bits to write
    golden_val = gen_rand_bits(set_parameters.REG_FILE_WIDTH)

    await write_csr(dut, golden_val, set_parameters.AM_NUM_PREDICT_REG_ADDR)

    # Check if value is correct
    test_val = dut.csr_am_num_pred_o.value.integer
    check_result(test_val, golden_val)

    # Do a read and check if value is correct
    csr_read_val = await read_csr(dut, set_parameters.AM_NUM_PREDICT_REG_ADDR)
    check_result(csr_read_val, golden_val)

    cocotb.log.info(" ------------------------------------------ ")
    cocotb.log.info("         Check Prediction Register          ")
    cocotb.log.info(" ------------------------------------------ ")

    csr_read_val = await read_csr(dut, set_parameters.AM_PREDICT_REG_ADDR)
    check_result(csr_read_val, (MAX_REG_VAL & 0x0000_01FF))

    cocotb.log.info(" ------------------------------------------ ")
    cocotb.log.info("        Instruction Control Register        ")
    cocotb.log.info(" ------------------------------------------ ")

    await write_csr(dut, MAX_REG_VAL, set_parameters.INST_CTRL_REG_ADDR)

    test_val = dut.csr_inst_ctrl_write_mode_o.value.integer
    check_result(test_val, 1)

    test_val = dut.csr_inst_ctrl_dbg_o.value.integer
    check_result(test_val, 1)

    test_val = dut.csr_inst_ctrl_clr_o.value.integer
    check_result(test_val, 1)

    # Propagate time then check if some signals return to 0
    await clock_and_time(dut.clk_i)

    test_val = dut.csr_inst_ctrl_write_mode_o.value.integer
    check_result(test_val, 1)

    test_val = dut.csr_inst_ctrl_dbg_o.value.integer
    check_result(test_val, 1)

    test_val = dut.csr_inst_ctrl_clr_o.value.integer
    check_result(test_val, 0)

    # Do a read and check if value is correct
    csr_read_val = await read_csr(dut, set_parameters.INST_CTRL_REG_ADDR)
    check_result(csr_read_val, 0x0000_0003)

    cocotb.log.info(" ------------------------------------------ ")
    cocotb.log.info("          Instruction Write Control         ")
    cocotb.log.info(" ------------------------------------------ ")

    # Generate random bits to write
    golden_val = gen_rand_bits(set_parameters.INST_MEM_ADDR_WIDTH)

    await write_csr(dut, golden_val, set_parameters.INST_WRITE_ADDR_REG_ADDR)

    # Check if value is correct
    test_val = dut.csr_inst_wr_addr_o.value.integer
    check_result(test_val, golden_val)

    test_val = dut.csr_inst_wr_addr_en_o.value.integer
    check_result(test_val, 1)

    # Propagate time then check if some signals return to 0
    await clock_and_time(dut.clk_i)

    test_val = dut.csr_inst_wr_addr_en_o.value.integer
    check_result(test_val, 0)

    # Do a read and check if value is correct
    csr_read_val = await read_csr(dut, set_parameters.INST_WRITE_ADDR_REG_ADDR)
    check_result(csr_read_val, 0)

    cocotb.log.info(" ------------------------------------------ ")
    cocotb.log.info("         Instruction Write Address          ")
    cocotb.log.info(" ------------------------------------------ ")

    # Generate random bits to write
    golden_val = gen_rand_bits(set_parameters.REG_FILE_WIDTH)

    await write_csr(dut, golden_val, set_parameters.INST_WRITE_DATA_REG_ADDR)

    # Check if value is correct
    test_val = dut.csr_inst_wr_data_o.value.integer
    check_result(test_val, golden_val)

    test_val = dut.csr_inst_wr_data_en_o.value.integer
    check_result(test_val, 1)

    # Propagate time then check if some signals return to 0
    await clock_and_time(dut.clk_i)

    test_val = dut.csr_inst_wr_data_en_o.value.integer
    check_result(test_val, 0)

    # Do a read and check if value is correct
    csr_read_val = await read_csr(dut, set_parameters.INST_WRITE_DATA_REG_ADDR)
    check_result(csr_read_val, 0)

    cocotb.log.info(" ------------------------------------------ ")
    cocotb.log.info("         Instruction Debug Address          ")
    cocotb.log.info(" ------------------------------------------ ")

    # Generate random bits to write
    golden_val = gen_rand_bits(set_parameters.INST_MEM_ADDR_WIDTH)

    await write_csr(dut, golden_val, set_parameters.INST_RDDBG_ADDR_REG_ADDR)

    # Check if value is correct
    test_val = dut.csr_inst_rddbg_addr_o.value.integer
    check_result(test_val, golden_val)

    # Do a read and check if value is correct
    csr_read_val = await read_csr(dut, set_parameters.INST_RDDBG_ADDR_REG_ADDR)
    check_result(csr_read_val, golden_val)

    cocotb.log.info(" ------------------------------------------ ")
    cocotb.log.info("          Instruction PC Address            ")
    cocotb.log.info(" ------------------------------------------ ")

    overwrite_val = gen_rand_bits(set_parameters.INST_MEM_ADDR_WIDTH)
    await write_csr(dut, overwrite_val, set_parameters.INST_PC_ADDR_REG_ADDR)

    # Do a read and check if value is correct
    # In this scenario it must not equate to the overwrite value
    # But the one originally set at the beginning
    csr_read_val = await read_csr(dut, set_parameters.INST_PC_ADDR_REG_ADDR)
    check_result(csr_read_val, set_parameters.INST_MEM_DEPTH - 1)

    cocotb.log.info(" ------------------------------------------ ")
    cocotb.log.info("          Instruction At Address            ")
    cocotb.log.info(" ------------------------------------------ ")

    overwrite_val = gen_rand_bits(set_parameters.INST_MEM_ADDR_WIDTH)
    await write_csr(dut, overwrite_val, set_parameters.INST_INST_AT_ADDR_ADDR_REG_ADDR)

    # Do a read and check if value is correct
    # In this scenario it must not equate to the overwrite value
    # But the one originally set at the beginning
    csr_read_val = await read_csr(dut, set_parameters.INST_INST_AT_ADDR_ADDR_REG_ADDR)
    check_result(csr_read_val, MAX_REG_VAL)

    cocotb.log.info(" ------------------------------------------ ")
    cocotb.log.info("         Instruction Loop Control           ")
    cocotb.log.info(" ------------------------------------------ ")

    # Generate random bits to write
    golden_val = gen_rand_bits(set_parameters.REG_FILE_WIDTH)

    await write_csr(dut, golden_val, set_parameters.INST_LOOP_CTRL_REG_ADDR)

    # Check if values are correct
    test_val = dut.csr_inst_loop_mode_o.value.integer
    check_result(test_val, (golden_val & 0x0000_0007))

    test_val = dut.csr_inst_loop_hvdim_sel_o.value.integer
    check_result(test_val, (golden_val & 0x0000_0018) >> 3)

    test_val = dut.csr_inst_loop_hvdim_extend_count_o.value.integer
    check_result(test_val, (golden_val & 0x0000_03E0) >> 5)

    csr_read_val = await read_csr(dut, set_parameters.INST_LOOP_CTRL_REG_ADDR)
    check_result(csr_read_val, (golden_val & 0x0000_03FF))

    cocotb.log.info(" ------------------------------------------ ")
    cocotb.log.info("         Instruction Jump Address           ")
    cocotb.log.info(" ------------------------------------------ ")

    # This has some shifting needed to slice the data
    # Generate random bits to write
    golden_val = gen_rand_bits(set_parameters.REG_FILE_WIDTH)

    await write_csr(dut, golden_val, set_parameters.INST_LOOP_JUMP_ADDR_REG_ADDR)

    # Check if value is correct
    # Make sure to shift the values accordingly
    test_val = dut.csr_loop_jump_addr1_o.value.integer
    check_result(test_val, (golden_val & (set_parameters.INST_MEM_DEPTH - 1)))

    test_val = dut.csr_loop_jump_addr2_o.value.integer
    check_result(
        test_val,
        (
            (golden_val >> set_parameters.INST_MEM_ADDR_WIDTH)
            & (set_parameters.INST_MEM_DEPTH - 1)
        ),
    )

    test_val = dut.csr_loop_jump_addr3_o.value.integer
    check_result(
        test_val,
        (
            (golden_val >> (2 * set_parameters.INST_MEM_ADDR_WIDTH))
            & (set_parameters.INST_MEM_DEPTH - 1)
        ),
    )

    test_val = dut.csr_loop_jump_addr4_o.value.integer
    check_result(
        test_val,
        (
            (golden_val >> (3 * set_parameters.INST_MEM_ADDR_WIDTH))
            & (set_parameters.INST_MEM_DEPTH - 1)
        ),
    )

    csr_read_val = await read_csr(dut, set_parameters.INST_LOOP_JUMP_ADDR_REG_ADDR)
    check_result(csr_read_val, golden_val)

    cocotb.log.info(" ------------------------------------------ ")
    cocotb.log.info("         Instruction End Address            ")
    cocotb.log.info(" ------------------------------------------ ")

    # Generate random bits to write
    golden_val = gen_rand_bits(set_parameters.REG_FILE_WIDTH)

    await write_csr(dut, golden_val, set_parameters.INST_LOOP_END_ADDR_REG_ADDR)

    # Check if value is correct
    # Make sure to shift the values accordingly
    test_val = dut.csr_loop_end_addr1_o.value.integer
    check_result(test_val, (golden_val & (set_parameters.INST_MEM_DEPTH - 1)))

    test_val = dut.csr_loop_end_addr2_o.value.integer
    check_result(
        test_val,
        (
            (golden_val >> set_parameters.INST_MEM_ADDR_WIDTH)
            & (set_parameters.INST_MEM_DEPTH - 1)
        ),
    )

    test_val = dut.csr_loop_end_addr3_o.value.integer
    check_result(
        test_val,
        (
            (golden_val >> (2 * set_parameters.INST_MEM_ADDR_WIDTH))
            & (set_parameters.INST_MEM_DEPTH - 1)
        ),
    )

    test_val = dut.csr_loop_end_addr4_o.value.integer
    check_result(
        test_val,
        (
            (golden_val >> (3 * set_parameters.INST_MEM_ADDR_WIDTH))
            & (set_parameters.INST_MEM_DEPTH - 1)
        ),
    )

    csr_read_val = await read_csr(dut, set_parameters.INST_LOOP_END_ADDR_REG_ADDR)
    check_result(csr_read_val, golden_val)

    cocotb.log.info(" ------------------------------------------ ")
    cocotb.log.info("         Instruction Loop Counts            ")
    cocotb.log.info(" ------------------------------------------ ")

    # Generate random bits to write
    golden_val = gen_rand_bits(set_parameters.REG_FILE_WIDTH)
    mask_val = (2**set_parameters.INST_LOOP_COUNT_WIDTH) - 1

    await write_csr(dut, golden_val, set_parameters.INST_LOOP_COUNT1_REG_ADDR)

    # Check if value is correct
    # Make sure to shift the values accordingly
    test_val = dut.csr_loop_count_addr1_o.value.integer
    check_result(test_val, (golden_val & (mask_val)))

    test_val = dut.csr_loop_count_addr2_o.value.integer
    check_result(
        test_val,
        ((golden_val >> set_parameters.INST_LOOP_COUNT_WIDTH) & (mask_val)),
    )

    csr_read_val = await read_csr(dut, set_parameters.INST_LOOP_COUNT1_REG_ADDR)
    check_result(csr_read_val, golden_val)

    # Generate random bits to write
    golden_val = gen_rand_bits(set_parameters.REG_FILE_WIDTH)
    mask_val = (2**set_parameters.INST_LOOP_COUNT_WIDTH) - 1

    await write_csr(dut, golden_val, set_parameters.INST_LOOP_COUNT2_REG_ADDR)

    test_val = dut.csr_loop_count_addr3_o.value.integer
    check_result(test_val, (golden_val & (mask_val)))

    test_val = dut.csr_loop_count_addr4_o.value.integer
    check_result(
        test_val,
        ((golden_val >> set_parameters.INST_LOOP_COUNT_WIDTH) & (mask_val)),
    )

    csr_read_val = await read_csr(dut, set_parameters.INST_LOOP_COUNT2_REG_ADDR)
    check_result(csr_read_val, golden_val)

    cocotb.log.info(" ------------------------------------------ ")
    cocotb.log.info("         Data Slicer Configurations         ")
    cocotb.log.info(" ------------------------------------------ ")

    # Check the data slicer mode first
    # Generate random bits to write
    golden_val = gen_rand_bits(set_parameters.REG_FILE_WIDTH)
    await write_csr(dut, golden_val, set_parameters.DATA_SRC_CTRL_REG_ADDR)

    # Check value of data slice mode for port A
    golden_val_slide_mode = golden_val & 0x0000_0003
    test_val = dut.csr_data_slice_mode_a_o.value.integer
    check_result(test_val, golden_val_slide_mode)

    # Check value of data slice mode for port B
    golden_val_slide_mode = (golden_val >> 2) & 0x0000_0003
    test_val = dut.csr_data_slice_mode_b_o.value.integer
    check_result(test_val, golden_val_slide_mode)

    # Check the value of source select also 2 bits long
    golden_val_src_sel = (golden_val >> 4) & 0x0000_0003
    test_val = dut.csr_data_src_sel_o.value.integer
    check_result(test_val, golden_val_src_sel)

    # Read value manually
    golden_val = golden_val & 0x0000_003F
    csr_read_val = await read_csr(dut, set_parameters.DATA_SRC_CTRL_REG_ADDR)
    check_result(csr_read_val, golden_val)

    # Check the data slicer number of elements ----------------------------------
    # Generate random bits to write
    golden_val = gen_rand_bits(set_parameters.REG_FILE_WIDTH)
    await write_csr(dut, golden_val, set_parameters.DATA_SLICE_NUM_ELEM_A_REG_ADDR)

    # Check value of data slice mode
    test_val = dut.csr_data_slice_num_elem_a_o.value.integer
    check_result(test_val, golden_val)

    # Read value manually
    csr_read_val = await read_csr(dut, set_parameters.DATA_SLICE_NUM_ELEM_A_REG_ADDR)
    check_result(csr_read_val, golden_val)

    # Generate random bits to write
    golden_val = gen_rand_bits(set_parameters.REG_FILE_WIDTH)
    await write_csr(dut, golden_val, set_parameters.DATA_SLICE_NUM_ELEM_B_REG_ADDR)

    # Check value of data slice mode
    test_val = dut.csr_data_slice_num_elem_b_o.value.integer
    check_result(test_val, golden_val)

    # Read value manually
    csr_read_val = await read_csr(dut, set_parameters.DATA_SLICE_NUM_ELEM_B_REG_ADDR)
    check_result(csr_read_val, golden_val)

    # Check the data auto start value ----------------------------------
    # Generate random bits to write
    golden_val = gen_rand_bits(set_parameters.REG_FILE_WIDTH)
    await write_csr(dut, golden_val, set_parameters.DATA_SRC_AUTO_START_A_REG_ADDR)

    # Check value of data slice mode
    test_val = dut.csr_src_auto_start_num_a_o.value.integer
    check_result(test_val, golden_val)

    # Read value manually
    csr_read_val = await read_csr(dut, set_parameters.DATA_SRC_AUTO_START_A_REG_ADDR)
    check_result(csr_read_val, golden_val)

    # Generate random bits to write
    golden_val = gen_rand_bits(set_parameters.REG_FILE_WIDTH)
    await write_csr(dut, golden_val, set_parameters.DATA_SRC_AUTO_START_B_REG_ADDR)

    # Check value of data slice mode
    test_val = dut.csr_src_auto_start_num_b_o.value.integer
    check_result(test_val, golden_val)

    # Read value manually
    csr_read_val = await read_csr(dut, set_parameters.DATA_SRC_AUTO_START_B_REG_ADDR)
    check_result(csr_read_val, golden_val)

    # Check the data auto num value ----------------------------------
    # Generate random bits to write
    golden_val = gen_rand_bits(set_parameters.REG_FILE_WIDTH)
    await write_csr(dut, golden_val, set_parameters.DATA_SRC_AUTO_NUM_A_REG_ADDR)

    # Check value of data slice mode
    test_val = dut.csr_src_auto_num_a_o.value.integer
    check_result(test_val, golden_val)

    # Read value manually
    csr_read_val = await read_csr(dut, set_parameters.DATA_SRC_AUTO_NUM_A_REG_ADDR)
    check_result(csr_read_val, golden_val)

    # Generate random bits to write
    golden_val = gen_rand_bits(set_parameters.REG_FILE_WIDTH)
    await write_csr(dut, golden_val, set_parameters.DATA_SRC_AUTO_NUM_B_REG_ADDR)

    # Check value of data slice mode
    test_val = dut.csr_src_auto_num_b_o.value.integer
    check_result(test_val, golden_val)

    # Read value manually
    csr_read_val = await read_csr(dut, set_parameters.DATA_SRC_AUTO_NUM_B_REG_ADDR)
    check_result(csr_read_val, golden_val)

    # This is for waveform checking later
    for i in range(set_parameters.TEST_RUNS):
        # Propagate time for logic
        await clock_and_time(dut.clk_i)


# Actual test run
@pytest.mark.parametrize(
    "parameters",
    [
        {
            "NumTotIm": str(set_parameters.NUM_TOT_IM),
            "NumPerImBank": str(set_parameters.NUM_PER_IM_BANK),
            "CsrDataWidth": str(set_parameters.REG_FILE_WIDTH),
            "CsrAddrWidth": str(set_parameters.REG_FILE_WIDTH),
            "InstMemDepth": str(set_parameters.INST_MEM_DEPTH),
        }
    ],
)
def test_csr(simulator, parameters, waves):
    verilog_sources = [
        # Level 0
        "/rtl/csr/csr_addr_pkg.sv",
        # Level 1
        "/rtl/csr/csr.sv",
    ]

    toplevel = "csr"

    module = "test_csr"

    setup_and_run(
        verilog_sources=verilog_sources,
        toplevel=toplevel,
        module=module,
        simulator=simulator,
        parameters=parameters,
        waves=waves,
    )
