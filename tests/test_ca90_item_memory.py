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

from util import get_root, setup_and_run, check_result_array, numbin2list, hvlist2num

# Add hdc utility functions
hdc_util_path = get_root() + "/hdc_exp/"
sys.path.append(hdc_util_path)

from hdc_util import gen_orthogonal_im, gen_ri_hv  # noqa: E402


@cocotb.test()
async def ca90_item_memory_dut(dut):
    cocotb.log.info(" ------------------------------------------ ")
    cocotb.log.info("         Testing CA90 Item Memory           ")
    cocotb.log.info(" ------------------------------------------ ")

    # Get nice seed with 50% 1s and 0s
    seed_hv_list = gen_ri_hv(set_parameters.HV_DIM, 0.5)
    seed_hv = hvlist2num(seed_hv_list)

    cocotb.log.info(f"Working with seed: {seed_hv}")

    # Generate golden item memory
    golden_im = gen_orthogonal_im(
        set_parameters.NUM_ORTHO_ITEMS,
        set_parameters.HV_DIM,
        0.5,
        seed_hv_list,
        hv_type="binary",
        im_type="ca90_iter",
    )

    # Dummy seed value
    dut.seed_hv_i.value = seed_hv

    # Propagate time for logic
    await Timer(1, units="ps")

    # Load request, propagate, check result
    for i in range(set_parameters.NUM_ORTHO_ITEMS):
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
            "NumImElements": str(set_parameters.NUM_ORTHO_ITEMS),
        }
    ],
)
def test_ca90_item_memory(simulator, parameters):
    verilog_sources = [
        "/rtl/item_memory/ca90_unit.sv",
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
        waves=True,
    )
