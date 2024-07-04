"""
  Copyright 2024 KU Leuven
  Ryan Antonio <ryan.antonio@esat.kuleuven.be>

  Description:
  This tests the vectorized bundler unit
"""

import set_parameters
from util import (
    get_root,
    setup_and_run,
    gen_rand_bits,
    clock_and_time,
    clear_encode_inputs_no_clock,
    load_reg_to_qhv,
    load_im_to_reg,
    perm_reg_to_qhv,
    bind_2im_to_reg,
    bind_2reg_to_reg,
    im_to_bundler,
    load_bundler_to_reg,
    load_bundler_to_qhv,
    hv_alu_out,
    numbip2list,
    hvlist2num,
)

import cocotb
from cocotb.clock import Clock
import numpy as np
import sys
import pytest
import random

# Add hdc utility functions
hdc_util_path = get_root() + "/hdc_exp/"
print(hdc_util_path)
sys.path.append(hdc_util_path)

from hdc_util import binarize_hv  # noqa: E402

# Some local parameters
IM_LEN = 10


# Convert a number in binary to a list
# Used to feed each bundler unit
def numbin2list(numbin, dim):
    # Convert binary inputs first
    bin_hv = np.array(list(map(int, format(numbin, f"0{dim}b"))))
    return bin_hv


# Check results
def check_result(actual_val, golden_val):
    assert (
        golden_val == actual_val
    ), f"Error! Golden Val: {golden_val}; Actual Val: {actual_val}"
    return


# Actual test routines
@cocotb.test()
async def hv_encoder_dut(dut):
    cocotb.log.info(" ------------------------------------------ ")
    cocotb.log.info("             Testing HV Encoder             ")
    cocotb.log.info(" ------------------------------------------ ")

    # Initialize input values
    clear_encode_inputs_no_clock(dut)
    dut.rst_ni.value = 0

    # Initialize clock always
    clock = Clock(dut.clk_i, 10, units="ns")
    cocotb.start_soon(clock.start(start_high=False))

    # Wait one cycle for reset
    await clock_and_time(dut.clk_i)

    dut.rst_ni.value = 1

    # Randomly generate a set of IM data
    # Just set 10 for now
    im_a_list = []
    im_b_list = []

    for i in range(IM_LEN):
        im_a_list.append(gen_rand_bits(set_parameters.HV_DIM))
        im_b_list.append(gen_rand_bits(set_parameters.HV_DIM))

    cocotb.log.info(" ------------------------------------------ ")
    cocotb.log.info("              IM > Regs > QHV               ")
    cocotb.log.info(" ------------------------------------------ ")

    # Loading item memory HVs to registers
    for i in range(set_parameters.REG_NUM):
        await load_im_to_reg(dut, im_a_list[i], i)

    # Move from regs to QHV
    for i in range(set_parameters.REG_NUM):
        # Load from register to QHV
        await load_reg_to_qhv(dut, i)

        # Extract answers
        qhv_val = dut.qhv_o.value.integer
        golden_val = im_a_list[i]

        # Check if QHV is correct
        check_result(qhv_val, golden_val)

    cocotb.log.info(" ------------------------------------------ ")
    cocotb.log.info("            Regs > Shift > QHV              ")
    cocotb.log.info(" ------------------------------------------ ")

    for i in range(set_parameters.REG_NUM):
        # Get random shift amout
        random_shift = random.randrange(int(set_parameters.MAX_SHIFT_AMT))

        # Get golden answer first
        golden_val = hv_alu_out(im_a_list[i], 0, random_shift, set_parameters.HV_DIM, 3)

        # Plug in control signals into encoder
        await perm_reg_to_qhv(dut, i, random_shift)

        # Extract answer
        qhv_val = dut.qhv_o.value.integer

        # Check if QHV is correct
        check_result(qhv_val, golden_val)

    cocotb.log.info(" ------------------------------------------ ")
    cocotb.log.info("       IM A and B > ALU > Regs > QHV        ")
    cocotb.log.info(" ------------------------------------------ ")

    for i in range(set_parameters.REG_NUM):
        # Get golden answer first
        golden_val = hv_alu_out(im_a_list[i], im_b_list[i], 0, set_parameters.HV_DIM, 0)

        # Bind from 2 im and save to register
        await bind_2im_to_reg(dut, im_a_list[i], im_b_list[i], i)

        # Move register to qhv
        await load_reg_to_qhv(dut, i)

        # Extract answer
        qhv_val = dut.qhv_o.value.integer

        # Check if QHV is correct
        check_result(qhv_val, golden_val)

    cocotb.log.info(" ------------------------------------------ ")
    cocotb.log.info("      Reg A and B > ALU > Regs > QHV        ")
    cocotb.log.info(" ------------------------------------------ ")

    # For this part we will do a specific routine
    # 1. Load data from IM to register
    for i in range(set_parameters.REG_NUM):
        await load_im_to_reg(dut, im_a_list[i], i)

    # 2. Grab HA A and HV B from register
    # and store back to 1st and 2nd respectively
    await bind_2reg_to_reg(dut, 0, 1, 0)
    await bind_2reg_to_reg(dut, 2, 3, 1)

    # Get golden answers from here
    test_hv_0 = im_a_list[0] ^ im_a_list[1]
    test_hv_1 = im_a_list[2] ^ im_a_list[3]

    # 3. Load to the QHV output and check results
    await load_reg_to_qhv(dut, 0)
    qhv_val = dut.qhv_o.value.integer

    check_result(test_hv_0, qhv_val)

    await load_reg_to_qhv(dut, 1)
    qhv_val = dut.qhv_o.value.integer

    check_result(test_hv_1, qhv_val)

    cocotb.log.info(" ------------------------------------------------ ")
    cocotb.log.info("   IM > Bundler > Reg > QHV > or Bundler > QHV    ")
    cocotb.log.info(" ------------------------------------------------ ")

    for bundler_addr in range(2):
        # Do this for the item length count
        golden_hv_bundle = np.zeros(set_parameters.HV_DIM)
        for i in range(IM_LEN):
            # Bindle from IM to bundler
            await im_to_bundler(dut, im_a_list[i], bundler_addr)

            # Get ideal bundle score
            golden_hv_bundle += numbip2list(im_a_list[i], set_parameters.HV_DIM)

        # Binarize golden value
        # Combine into bit-wise info
        golden_hv_bundle = binarize_hv(golden_hv_bundle, 0)
        golden_hv_bundle = hvlist2num(golden_hv_bundle)

        # Load from binarized bundler to register 0
        # Then from register 0 to QHV
        await load_bundler_to_reg(dut, bundler_addr, 0)
        await load_reg_to_qhv(dut, 0)

        # Extract the qhv output
        actual_hv_bundle = dut.qhv_o.value.integer

        # Compare results
        check_result(actual_hv_bundle, golden_hv_bundle)

        # Move the bundler to QHV
        await load_bundler_to_qhv(dut, bundler_addr)

        # Extract the qhv output
        actual_hv_bundle = dut.qhv_o.value.integer

        # Compare results
        check_result(actual_hv_bundle, golden_hv_bundle)

    # Some trailing cycles only
    for i in range(10):
        await clock_and_time(dut.clk_i)


# Config and run
@pytest.mark.parametrize(
    "parameters",
    [
        {
            "HVDimension": str(set_parameters.HV_DIM),
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
def test_hv_encoder(simulator, parameters, waves):
    verilog_sources = [
        "/rtl/common/reg_file_1w2r.sv",
        "/rtl/hv_alu_pe.sv",
        "/rtl/bundler_unit.sv",
        "/rtl/bundler_set.sv",
        "/rtl/hv_encoder.sv",
    ]

    toplevel = "hv_encoder"

    module = "test_hv_encoder"

    setup_and_run(
        verilog_sources=verilog_sources,
        toplevel=toplevel,
        module=module,
        simulator=simulator,
        parameters=parameters,
        waves=waves,
    )
