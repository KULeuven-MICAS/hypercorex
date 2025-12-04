"""
Copyright 2024 KU Leuven
Ryan Antonio <ryan.antonio@esat.kuleuven.be>

Description:
This tests the basic functionality
of the CA90 generation unit
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


@cocotb.test()
async def ca90_item_memory_dut(dut):
    cocotb.log.info(" ------------------------------------------ ")
    cocotb.log.info("         Testing CA90 Item Memory           ")
    cocotb.log.info(" ------------------------------------------ ")

    # Generate seed list and golden IM
    seed_list, golden_im, conf_mat = gen_ca90_im_set(
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
    seed_input = 0
    for i in range(num_im_banks):
        seed_input = (seed_input << set_parameters.REG_FILE_WIDTH) + seed_list[
            num_im_banks - i - 1
        ]

    dut.seed_hv_i.value = seed_input

    # Propagate time for logic
    await Timer(1, units="ps")

    # Load request, propagate, check result
    for i in range(set_parameters.NUM_TOT_IM):
        dut.im_sel_a_i.value = i
        dut.im_sel_b_i.value = i
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
        }
    ],
)
def test_ca90_item_memory(simulator, parameters, waves):
    verilog_sources = [
        "/rtl/item_memory/fixed_ca90_unit.sv",
        "/rtl/item_memory/ca90_hier_base.sv",
        "/rtl/item_memory/ca90_item_memory.sv",
    ]

    toplevel = "ca90_item_memory"

    module = "test_ca90_item_memory"

    setup_and_run(
        verilog_sources=verilog_sources,
        toplevel=toplevel,
        module=module,
        simulator=simulator,
        parameters=parameters,
        waves=waves,
    )
