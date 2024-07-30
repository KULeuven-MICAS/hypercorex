"""
  Copyright 2024 KU Leuven
  Ryan Antonio <ryan.antonio@esat.kuleuven.be>

  Description:
  This tests the fully combinational
  instruction decode unit.

  This one is more specific so it's not fully
  automated since it's limited by the control signals
"""

import set_parameters
import cocotb
from cocotb.triggers import Timer
import pytest
import sys
import numpy as np
from tests.util import check_result
import random

from util import get_root, setup_and_run, hvlist2num

# Add hdc utility functions
hdc_exp_path = get_root() + "/hdc_exp/"
sys.path.append(hdc_exp_path)

sw_path = get_root() + "/sw/"
sys.path.append(sw_path)

# From compiler
from hypercorex_compiler import decode_inst, list2str  # noqa: E402

# Some parameter
DEBUG = False


# For extracting control signals
async def input_and_extract(dut, inst_code, print_ctrl=DEBUG):
    # Clear first
    dut.inst_code_i.value = inst_code

    # Propagate time for logic
    await Timer(1, units="ps")

    # Control ports for IM
    im_a_pop = dut.im_a_pop_o.value.binstr
    im_b_pop = dut.im_b_pop_o.value.binstr
    # Control ports for ALU
    alu_mux_a = dut.alu_mux_a_o.value.binstr
    alu_mux_b = dut.alu_mux_b_o.value.binstr
    alu_ops = dut.alu_ops_o.value.binstr
    alu_shift_amt = dut.alu_shift_amt_o.value.binstr
    # Control ports for bundlers
    bund_mux_a = dut.bund_mux_a_o.value.binstr
    bund_mux_b = dut.bund_mux_b_o.value.binstr
    bund_valid_a = dut.bund_valid_a_o.value.binstr
    bund_valid_b = dut.bund_valid_b_o.value.binstr
    bund_clr_a = dut.bund_clr_a_o.value.binstr
    bund_clr_b = dut.bund_clr_b_o.value.binstr
    # Control ports for register ops
    reg_mux = dut.reg_mux_o.value.binstr
    reg_rd_addr_a = dut.reg_rd_addr_a_o.value.binstr
    reg_rd_addr_b = dut.reg_rd_addr_b_o.value.binstr
    reg_wr_addr = dut.reg_wr_addr_o.value.binstr
    reg_wr_en = dut.reg_wr_en_o.value.binstr
    # Control ports for query HV
    qhv_clr = dut.qhv_clr_o.value.binstr
    qhv_wen = dut.qhv_wen_o.value.binstr
    qhv_mux = dut.qhv_mux_o.value.binstr
    # Control port for the AM
    am_search = dut.am_search_o.value.binstr
    am_load = dut.am_load_o.value.binstr

    # Make sure to clear after propagating logic
    dut.inst_code_i.value = 0

    if print_ctrl:
        print(f"im_a_pop: {im_a_pop}")
        print(f"im_b_pop: {im_b_pop}")
        print(f"alu_mux_a: {alu_mux_a}")
        print(f"alu_mux_b: {alu_mux_b}")
        print(f"alu_ops: {alu_ops}")
        print(f"alu_shift_amt: {alu_shift_amt}")
        print(f"bund_mux_a: {bund_mux_a}")
        print(f"bund_mux_b: {bund_mux_b}")
        print(f"bund_valid_a: {bund_valid_a}")
        print(f"bund_valid_b: {bund_valid_b}")
        print(f"bund_clr_a: {bund_clr_a}")
        print(f"bund_clr_b: {bund_clr_b}")
        print(f"reg_mux: {reg_mux}")
        print(f"reg_rd_addr_a: {reg_rd_addr_a}")
        print(f"reg_rd_addr_b: {reg_rd_addr_b}")
        print(f"reg_wr_addr: {reg_wr_addr}")
        print(f"reg_wr_en: {reg_wr_en}")
        print(f"qhv_clr: {qhv_clr}")
        print(f"qhv_wen: {qhv_wen}")
        print(f"qhv_mux: {qhv_mux}")
        print(f"am_search: {am_search}")
        print(f"am_load: {am_load}")

    control_signal_list = (
        im_a_pop
        + im_b_pop
        + alu_mux_a
        + alu_mux_b
        + alu_ops
        + alu_shift_amt
        + bund_mux_a
        + bund_mux_b
        + bund_valid_a
        + bund_valid_b
        + bund_clr_a
        + bund_clr_b
        + reg_mux
        + reg_rd_addr_a
        + reg_rd_addr_b
        + reg_wr_addr
        + reg_wr_en
        + qhv_clr
        + qhv_wen
        + qhv_mux
        + am_search
        + am_load
    )

    return control_signal_list


@cocotb.test()
async def inst_decode_dut(dut):
    cocotb.log.info(" ------------------------------------------ ")
    cocotb.log.info("          Instruction Decode Unit           ")
    cocotb.log.info(" ------------------------------------------ ")

    cocotb.log.info(" ------------------------------------------ ")
    cocotb.log.info("     Generate Seeds and Golden Values       ")
    cocotb.log.info(" ------------------------------------------ ")

    # Initialize all other ports to 0
    dut.inst_code_i.value = 0

    # Do this in multiple loops
    for i in range(set_parameters.TEST_RUNS):
        inst_test_list = [
            "ima_reg x" + str(random.randint(0, 3)),
            "imb_reg x" + str(random.randint(0, 3)),
            "imab_bind_reg x" + str(random.randint(0, 3)),
            "ima_perm_reg x"
            + str(random.randint(0, 3))
            + " "
            + str(random.randint(0, 3)),
            "ima_bunda",
            "ima_bundb",
            "imab_bind_bunda",
            "imab_bind_bundb",
            "ima_perm_bunda " + str(random.randint(0, 3)),
            "ima_perm_bundb " + str(random.randint(0, 3)),
            "regab_bind_reg x"
            + str(random.randint(0, 3))
            + " x"
            + str(random.randint(0, 3))
            + " x"
            + str(random.randint(0, 3)),
            "rega_perm_reg x"
            + str(random.randint(0, 3))
            + " x"
            + str(random.randint(0, 3))
            + " "
            + str(random.randint(0, 3)),
            "mv_reg x" + str(random.randint(0, 3)) + " x" + str(random.randint(0, 3)),
            "regab_bind_bunda x"
            + str(random.randint(0, 3))
            + " x"
            + str(random.randint(0, 3)),
            "regab_bind_bundb x"
            + str(random.randint(0, 3))
            + " x"
            + str(random.randint(0, 3)),
            "rega_bunda_bind_reg x"
            + str(random.randint(0, 3))
            + " x"
            + str(random.randint(0, 3)),
            "rega_bundb_bind_reg x"
            + str(random.randint(0, 3))
            + " x"
            + str(random.randint(0, 3)),
            "bunda_perm_reg x"
            + str(random.randint(0, 3))
            + " "
            + str(random.randint(0, 3)),
            "bundb_perm_reg x"
            + str(random.randint(0, 3))
            + " "
            + str(random.randint(0, 3)),
            "mv_bunda_reg x" + str(random.randint(0, 3)),
            "mv_bundb_reg x" + str(random.randint(0, 3)),
            "mv_reg_bunda x" + str(random.randint(0, 3)),
            "mv_reg_bundb x" + str(random.randint(0, 3)),
            "mv_bunda_bundb",
            "mv_bundb_bunda",
            "clr_bunda",
            "clr_bundb",
            "mv_reg_qhv x" + str(random.randint(0, 3)),
            "mv_bunda_qhv",
            "mv_bundb_qhv",
            "clr_qhv",
            "am_search",
            "am_load",
        ]

        cocotb.log.info(" ------------------------------------------ ")
        cocotb.log.info("           Instructions Test List           ")
        cocotb.log.info(" ------------------------------------------ ")

        # Iterate each through instruction
        for i in range(len(inst_test_list)):
            # For debug purposes
            cocotb.log.info(f" Checking instruction: {inst_test_list[i]}")

            # First use the built-in compiler from the /sw directory
            inst_code, inst_control = decode_inst(
                inst_test_list[i].strip().split(), print_ctrl=DEBUG
            )

            # Convert list to a number for input purposes
            inst_code = hvlist2num(np.array(inst_code))

            # Convert to string list for easy comparison
            inst_control = list2str(inst_control)

            # Input and extract the instruction test
            actual_control_signal = await input_and_extract(
                dut, inst_code, print_ctrl=DEBUG
            )

            check_result(actual_control_signal, inst_control)

    # This is for waveform checking later
    for i in range(set_parameters.TEST_RUNS):
        # Propagate time for logic
        await Timer(1, units="ps")


# Actual test run
@pytest.mark.parametrize(
    "parameters",
    [
        {
            "InstWidth": str(set_parameters.INST_MEM_WIDTH),
            "ALUMuxWidth": str(set_parameters.ALU_MUX_WIDTH),
            "ALUMaxShiftAmt": str(set_parameters.ALU_MAX_SHIFT),
            "BundMuxWidth": str(set_parameters.BUNDLER_MUX_WIDTH),
            "RegMuxWidth": str(set_parameters.REG_MUX_WIDTH),
            "QvMuxWidth": str(set_parameters.QHV_MUX_WIDTH),
            "RegNum": str(set_parameters.REG_NUM),
        }
    ],
)
def test_item_memory(simulator, parameters, waves):
    verilog_sources = [
        "/rtl/inst_memory/hypercorex_inst_pkg.sv",
        "/rtl/inst_memory/inst_decode.sv",
    ]

    toplevel = "inst_decode"

    module = "test_inst_decode"

    setup_and_run(
        verilog_sources=verilog_sources,
        toplevel=toplevel,
        module=module,
        simulator=simulator,
        parameters=parameters,
        waves=waves,
    )
