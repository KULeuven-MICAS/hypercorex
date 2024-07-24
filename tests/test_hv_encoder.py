"""
  Copyright 2024 KU Leuven
  Ryan Antonio <ryan.antonio@esat.kuleuven.be>

  Description:
  This tests the vectorized bundler unit
"""

from hdc_exp.hdc_util import numbin2list
import set_parameters
from util import (
    get_root,
    setup_and_run,
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
    hvlist2num,
    check_result_array,
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

# Import item memory generations
from hdc_util import gen_square_cim, gen_ca90_im_set, binarize_hv  # noqa: E402

# Local parameters
BUNDLE_COUNT = 10


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

    cocotb.log.info(" ------------------------------------------ ")
    cocotb.log.info("     Generate Seeds and Golden Values       ")
    cocotb.log.info(" ------------------------------------------ ")

    # Generated golden CiM
    cim_seed_input, golden_cim = gen_square_cim(
        hv_dim=set_parameters.HV_DIM,
        seed_size=set_parameters.REG_FILE_WIDTH,
        im_type=set_parameters.CA90_MODE,
    )

    # Convert seed list to number
    cim_seed_input = hvlist2num(cim_seed_input)

    # Generate seed list and golden IM
    im_seed_input_list, golden_im, conf_mat = gen_ca90_im_set(
        seed_size=set_parameters.REG_FILE_WIDTH,
        hv_dim=set_parameters.HV_DIM,
        num_total_im=set_parameters.NUM_TOT_IM,
        num_per_im_bank=set_parameters.NUM_PER_IM_BANK,
        ca90_mode=set_parameters.CA90_MODE,
    )

    # For combining into a single
    # wire bus for simulation purposes
    num_im_banks = int(set_parameters.NUM_TOT_IM / set_parameters.NUM_PER_IM_BANK)
    im_seed_input = 0
    for i in range(num_im_banks):
        im_seed_input = (
            im_seed_input << set_parameters.REG_FILE_WIDTH
        ) + im_seed_input_list[num_im_banks - i - 1]

    # Input the CiM seed and the iM seeds
    dut.cim_seed_hv_i.value = cim_seed_input
    dut.im_seed_hv_i.value = im_seed_input

    # Initially let's use the CA90 first

    cocotb.log.info(" ------------------------------------------ ")
    cocotb.log.info("              IM > Regs > QHV               ")
    cocotb.log.info(" ------------------------------------------ ")

    # Loading item memory HVs to registers
    for i in range(set_parameters.REG_NUM):
        await load_im_to_reg(dut, i, i)

    # Move from regs to QHV
    for i in range(set_parameters.REG_NUM):
        # Load from register to QHV
        await load_reg_to_qhv(dut, i)

        # Extract answers
        qhv_val = numbin2list(dut.qhv_o.value.integer, set_parameters.HV_DIM)
        golden_val = golden_im[i]

        # Check if QHV is correct
        check_result_array(qhv_val, golden_val)

    cocotb.log.info(" ------------------------------------------ ")
    cocotb.log.info("            Regs > Shift > QHV              ")
    cocotb.log.info(" ------------------------------------------ ")

    for i in range(set_parameters.REG_NUM):
        # Get random shift amout
        random_shift = random.randrange(int(set_parameters.MAX_SHIFT_AMT))

        # Get golden answer first
        golden_val = hv_alu_out(
            hv_a=golden_im[i],
            hv_b=0,
            shift_amt=random_shift,
            hv_dim=set_parameters.HV_DIM,
            op=3,
        )

        # Plug in control signals into encoder
        await perm_reg_to_qhv(dut, i, random_shift)

        # Extract answer
        qhv_val = numbin2list(dut.qhv_o.value.integer, set_parameters.HV_DIM)

        # Check if QHV is correct
        check_result_array(qhv_val, golden_val)

    cocotb.log.info(" ------------------------------------------ ")
    cocotb.log.info("     IM A and B > ALU bind > Regs > QHV     ")
    cocotb.log.info(" ------------------------------------------ ")

    for i in range(set_parameters.REG_NUM):
        # Get golden answer first
        golden_val = hv_alu_out(
            hv_a=golden_im[i],
            hv_b=golden_im[set_parameters.REG_NUM + i],
            shift_amt=0,
            hv_dim=set_parameters.HV_DIM,
            op=0,
        )

        # Bind from 2 im and save to register
        await bind_2im_to_reg(
            dut=dut, im_addr_a=i, im_addr_b=set_parameters.REG_NUM + i, reg_addr=i
        )

        # Move register to qhv
        await load_reg_to_qhv(dut, i)

        # Extract answer
        qhv_val = numbin2list(dut.qhv_o.value.integer, set_parameters.HV_DIM)

        # Check if QHV is correct
        check_result_array(qhv_val, golden_val)

    cocotb.log.info(" ------------------------------------------ ")
    cocotb.log.info("      Reg A and B > ALU > Regs > QHV        ")
    cocotb.log.info(" ------------------------------------------ ")

    # For this part we will do a specific routine
    # 1. Load data from IM to register
    for i in range(set_parameters.REG_NUM):
        await load_im_to_reg(dut, i, i)

    # 2. Grab HA A and HV B from register
    # and store back to 1st and 2nd respectively
    await bind_2reg_to_reg(dut, 0, 1, 0)
    await bind_2reg_to_reg(dut, 2, 3, 1)

    # Get golden answers from here
    test_hv_0 = golden_im[0] ^ golden_im[1]
    test_hv_1 = golden_im[2] ^ golden_im[3]

    # 3. Load to the QHV output and check results
    await load_reg_to_qhv(dut, 0)
    qhv_val = numbin2list(dut.qhv_o.value.integer, set_parameters.HV_DIM)

    check_result_array(test_hv_0, qhv_val)

    await load_reg_to_qhv(dut, 1)
    qhv_val = numbin2list(dut.qhv_o.value.integer, set_parameters.HV_DIM)

    check_result_array(test_hv_1, qhv_val)

    cocotb.log.info(" ------------------------------------------------ ")
    cocotb.log.info("   IM > Bundler > Reg > QHV > or Bundler > QHV    ")
    cocotb.log.info(" ------------------------------------------------ ")

    for bundler_addr in range(2):
        # Do this for the item length count
        golden_hv_bundle = np.zeros(set_parameters.HV_DIM)
        for i in range(BUNDLE_COUNT):
            # Bindle from IM to bundler
            await im_to_bundler(dut, i, bundler_addr)

            # Get ideal bundle score
            # golden_hv_bundle += numbip2list(golden_im[i], set_parameters.HV_DIM)
            golden_hv_bundle += golden_im[i]

        # Binarize golden value
        # Combine into bit-wise info
        golden_hv_bundle = binarize_hv(golden_hv_bundle, int(BUNDLE_COUNT / 2))

        # Load from binarized bundler to register 0
        # Then from register 0 to QHV
        await load_bundler_to_reg(dut, bundler_addr, 0)
        await load_reg_to_qhv(dut, 0)

        # Extract the QHV output
        actual_hv_bundle = numbin2list(dut.qhv_o.value.integer, set_parameters.HV_DIM)

        # Compare results
        check_result_array(actual_hv_bundle, golden_hv_bundle)

        # Move the bundler to QHV
        await load_bundler_to_qhv(dut, bundler_addr)

        # Extract the qhv output
        actual_hv_bundle = numbin2list(dut.qhv_o.value.integer, set_parameters.HV_DIM)

        # Compare results
        check_result_array(actual_hv_bundle, golden_hv_bundle)

    # Some trailing cycles only
    for i in range(10):
        await clock_and_time(dut.clk_i)


# Config and run
@pytest.mark.parametrize(
    "parameters",
    [
        {
            "HVDimension": str(set_parameters.HV_DIM),
            "NumTotIm": str(set_parameters.NUM_TOT_IM),
            "NumPerImBank": str(set_parameters.NUM_PER_IM_BANK),
            "ImAddrWidth": str(set_parameters.REG_FILE_WIDTH),
            "SeedWidth": str(set_parameters.REG_FILE_WIDTH),
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
        # Level 0
        "/rtl/common/mux.sv",
        "/rtl/common/reg_file_1w2r.sv",
        "/rtl/item_memory/ca90_unit.sv",
        "/rtl/item_memory/cim_bit_flip.sv",
        "/rtl/hv_alu_pe.sv",
        "/rtl/bundler_unit.sv",
        # Level 1
        "/rtl/item_memory/ca90_hier_base.sv",
        "/rtl/item_memory/cim.sv",
        "/rtl/item_memory/ca90_item_memory.sv",
        "/rtl/bundler_set.sv",
        # Level 2
        "/rtl/item_memory/item_memory.sv",
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
