"""
Copyright 2024 KU Leuven
Ryan Antonio <ryan.antonio@esat.kuleuven.be>

Description:
This tests the combined item memory
that contains both the CiM and CA90
"""

import random
import set_parameters
import cocotb
from cocotb.clock import Clock
import pytest
import sys

from util import (
    get_root,
    setup_and_run,
    check_result_array,
    numbin2list,
    hvlist2num,
    clock_and_time,
)

# Add hdc utility functions
hdc_util_path = get_root() + "/hdc_exp/"
sys.path.append(hdc_util_path)

# Import item memory generations
from hdc_util import gen_square_cim, gen_ca90_im_set  # noqa: E402


@cocotb.test()
async def item_memory_dut(dut):
    cocotb.log.info(" ------------------------------------------ ")
    cocotb.log.info("                Item Memory                 ")
    cocotb.log.info(" ------------------------------------------ ")

    cocotb.log.info(" ------------------------------------------ ")
    cocotb.log.info("     Generate Seeds and Golden Values       ")
    cocotb.log.info(" ------------------------------------------ ")

    # Generated golden CiM
    cim_seed_input, golden_cim = gen_square_cim(
        base_seed=set_parameters.BASE_SEED_CIM,
        gen_seed=False,
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
        base_seeds=set_parameters.ORTHO_IM_SEEDS,
        gen_seed=True,
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

    # Reset
    dut.rst_ni.value = 0

    # Input the CiM seed and the iM seeds
    dut.cim_seed_hv_i.value = cim_seed_input
    dut.im_seed_hv_i.value = im_seed_input

    # Initialize all other ports to 0
    dut.port_a_cim_i.value = 0
    dut.im_a_addr_i.value = 0
    dut.im_b_addr_i.value = 0

    # Set dimensional expansion to 0 first
    dut.enable_i.value = 0
    dut.extend_enable_i.value = 0
    dut.extend_increment_i.value = 0
    dut.extend_count_i.value = 0

    # Initialize clock always
    clock = Clock(dut.clk_i, 10, units="ns")
    cocotb.start_soon(clock.start(start_high=False))

    # Propagate time for logic
    await clock_and_time(dut.clk_i)

    dut.rst_ni.value = 1

    await clock_and_time(dut.clk_i)

    cocotb.log.info(" ------------------------------------------ ")
    cocotb.log.info("         Checking CA90 Item Memory          ")
    cocotb.log.info(" ------------------------------------------ ")

    # Since port_a_cim_i is 0, it selects the
    # CA90 item memory

    # Load request, propagate, check result
    for i in range(set_parameters.NUM_TOT_IM):
        dut.im_a_addr_i.value = i
        dut.im_b_addr_i.value = i
        await clock_and_time(dut.clk_i)

        actual_val_a = dut.im_a_o.value.integer
        actual_val_b = dut.im_b_o.value.integer

        # Convert actual values to binary list
        actual_val_a = numbin2list(actual_val_a, set_parameters.HV_DIM)
        actual_val_b = numbin2list(actual_val_b, set_parameters.HV_DIM)

        # Check arrays if they are equal
        # Unfortunately, this is needed because there are
        # bit-width limitations for integer conversions
        check_result_array(actual_val_a, golden_im[i])
        check_result_array(actual_val_b, golden_im[i])

    # Clear other inputs but put
    # port_a_cim_i to 1 to select the CiM
    dut.port_a_cim_i.value = 1
    dut.im_a_addr_i.value = 0
    dut.im_b_addr_i.value = 0

    # Propagate time for logic
    await clock_and_time(dut.clk_i)

    cocotb.log.info(" ------------------------------------------ ")
    cocotb.log.info("               Checking CiM                 ")
    cocotb.log.info(" ------------------------------------------ ")

    # Use select and check for values
    num_cim_levels = int(set_parameters.HV_DIM / 2)

    for i in range(num_cim_levels):
        # Input the selection
        dut.im_a_addr_i.value = i

        # Propagate time for logic
        await clock_and_time(dut.clk_i)

        # Obtain actual value
        actual_val_a = dut.im_a_o.value.integer
        actual_val_a = numbin2list(actual_val_a, set_parameters.HV_DIM)

        # Compare to golden
        check_result_array(actual_val_a, golden_cim[i])

    # Bring back to 0
    dut.port_a_cim_i.value = 0
    dut.im_a_addr_i.value = 0
    dut.im_b_addr_i.value = 0

    await clock_and_time(dut.clk_i)

    cocotb.log.info(" ------------------------------------------ ")
    cocotb.log.info("         Checking Extension Counter         ")
    cocotb.log.info(" ------------------------------------------ ")

    # Enable extension
    dut.enable_i.value = 1
    dut.extend_enable_i.value = 1

    random_count = random.randint(5, 16)
    dut.extend_count_i.value = random_count
    await clock_and_time(dut.clk_i)

    for i in range(random_count):
        # Extend increment
        dut.extend_increment_i.value = 1

        # Extract data
        actual_val_a = dut.im_a_o.value.integer
        actual_val_b = dut.im_b_o.value.integer

        # Convert actual values to binary list
        actual_val_a = numbin2list(actual_val_a, set_parameters.HV_DIM)
        actual_val_b = numbin2list(actual_val_b, set_parameters.HV_DIM)

        # Check arrays if they are equal
        # Unfortunately, this is needed because there are
        # bit-width limitations for integer conversions
        check_result_array(actual_val_a, golden_im[i])
        check_result_array(actual_val_b, golden_im[i])

        await clock_and_time(dut.clk_i)

    # This is for waveform checking later
    for i in range(10):
        # Propagate time for logic
        await clock_and_time(dut.clk_i)


# Actual test run
@pytest.mark.parametrize(
    "parameters",
    [
        {
            "HVDimension": str(set_parameters.HV_DIM),
            "NumTotIm": str(set_parameters.NUM_TOT_IM),
            "NumPerImBank": str(set_parameters.NUM_PER_IM_BANK),
            "ImAddrWidth": str(set_parameters.REG_FILE_WIDTH),
            "SeedWidth": str(set_parameters.REG_FILE_WIDTH),
        }
    ],
)
def test_item_memory(simulator, parameters, waves):
    verilog_sources = [
        "/rtl/common/mux.sv",
        "/rtl/item_memory/fixed_ca90_unit.sv",
        "/rtl/item_memory/ca90_hier_base.sv",
        "/rtl/item_memory/cim_bit_flip.sv",
        "/rtl/item_memory/cim.sv",
        "/rtl/item_memory/ca90_item_memory.sv",
        "/rtl/item_memory/item_memory.sv",
    ]

    toplevel = "item_memory"

    module = "test_item_memory"

    setup_and_run(
        verilog_sources=verilog_sources,
        toplevel=toplevel,
        module=module,
        simulator=simulator,
        parameters=parameters,
        waves=waves,
    )
