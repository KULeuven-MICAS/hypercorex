"""
  Copyright 2024 KU Leuven
  Ryan Antonio <ryan.antonio@esat.kuleuven.be>

  Description:
  This tests the combined item memory
  that contains both the CiM and CA90
"""

import set_parameters
import cocotb
from cocotb.triggers import Timer
import pytest
import sys

from util import get_root, setup_and_run, check_result_array, numbin2list

# Add hdc utility functions
hdc_util_path = get_root() + "/hdc_exp/"
sys.path.append(hdc_util_path)

# Grab the CA90 generation from the
# cellular automata experiment set
from cellular_automata import gen_ca90_im_set  # noqa: E402

# Grab the CiM generation from the utility
from hdc_util import gen_square_cim  # noqa: E402


@cocotb.test()
async def item_memory_dut(dut):
    cocotb.log.info(" ------------------------------------------ ")
    cocotb.log.info("                Item Memory                 ")
    cocotb.log.info(" ------------------------------------------ ")

    # For parameter checking, we put a warning
    if set_parameters.NUM_PER_IM_BANK >= int(set_parameters.HV_DIM / 2):
        cocotb.log.info(" ------------------------------------------ ")
        cocotb.log.info("            !!!!!  WARNING  !!!!!           ")
        cocotb.log.info(f" The number of IM per bank {set_parameters.NUM_PER_IM_BANK}")
        cocotb.log.info(
            f" must be less than half of the HV dimension size {set_parameters.HV_DIM}"
        )
        cocotb.log.info(
            " It is recommended that it is 1/4th of the dimension size to avoid"
        )
        cocotb.log.info(" saturating at all 1s or all 0s due to CA90 limitations")
        cocotb.log.info(" ------------------------------------------ ")

    cocotb.log.info(" ------------------------------------------ ")
    cocotb.log.info("     Generate Seeds and Golden Values       ")
    cocotb.log.info(" ------------------------------------------ ")

    # This is for the seed input
    cim_seed_input = 3275349888

    # Convert to list for golden checking
    cim_seed_input_list = numbin2list(cim_seed_input, set_parameters.REG_FILE_WIDTH)

    # Generated golden CiM
    golden_cim = gen_square_cim(
        set_parameters.HV_DIM, cim_seed_input_list, im_type=set_parameters.CA90_MODE
    )

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
    dut.cim_seed_hv.value = cim_seed_input
    dut.im_seed_hv.value = im_seed_input

    # Initialize all other ports to 0
    dut.port_a_cim.value = 0
    dut.im_a_addr_i.value = 0
    dut.im_b_addr_i.value = 0

    # Propagate time for logic
    await Timer(1, units="ps")

    cocotb.log.info(" ------------------------------------------ ")
    cocotb.log.info("         Checking CA90 Item Memory          ")
    cocotb.log.info(" ------------------------------------------ ")

    # Since port_a_cim is 0, it selects the
    # CA90 item memory

    # Load request, propagate, check result
    for i in range(set_parameters.NUM_TOT_IM):
        dut.im_a_addr_i.value = i
        dut.im_b_addr_i.value = i
        await Timer(1, units="ps")

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
    # port_a_cim to 1 to select the CiM
    dut.port_a_cim.value = 1
    dut.im_a_addr_i.value = 0
    dut.im_b_addr_i.value = 0

    # Propagate time for logic
    await Timer(1, units="ps")

    cocotb.log.info(" ------------------------------------------ ")
    cocotb.log.info("               Checking CiM                 ")
    cocotb.log.info(" ------------------------------------------ ")

    # Use select and check for values
    num_cim_levels = int(set_parameters.HV_DIM / 2)

    for i in range(num_cim_levels):
        # Input the selection
        dut.im_a_addr_i.value = i

        # Propagate time for logic
        await Timer(1, units="ps")

        # Obtain actual value
        actual_val_a = dut.im_a_o.value.integer
        actual_val_a = numbin2list(actual_val_a, set_parameters.HV_DIM)

        # Compare to golden
        check_result_array(actual_val_a, golden_cim[i])

    # This is for waveform checking later
    for i in range(set_parameters.TEST_RUNS):
        # Propagate time for logic
        await Timer(1, units="ps")


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
def test_item_memory(simulator, parameters):
    verilog_sources = [
        "/rtl/common/mux.sv",
        "/rtl/item_memory/ca90_unit.sv",
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
        waves=True,
    )
