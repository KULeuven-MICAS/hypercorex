"""
  Copyright 2024 KU Leuven
  Ryan Antonio <ryan.antonio@esat.kuleuven.be>

  Description:
  This tests the basic functionality
  of the continuous item memory (CiM)
"""

import set_parameters
import cocotb
from cocotb.triggers import Timer
import pytest
import sys

from util import get_root, setup_and_run, numbin2list, check_result_array

# Add hdc utility functions
hdc_util_path = get_root() + "/hdc_exp/"
sys.path.append(hdc_util_path)

# Grab the CiM generation from the utility
from hdc_util import gen_square_cim  # noqa: E402


@cocotb.test()
async def cim_dut(dut):
    cocotb.log.info(" ------------------------------------------ ")
    cocotb.log.info("                Testing CiM                 ")
    cocotb.log.info(" ------------------------------------------ ")

    # Use an initial seed
    seed_input = 3275349888

    # Convert to list for golden checking
    seed_input_list = numbin2list(seed_input, set_parameters.REG_FILE_WIDTH)

    # Generated golden CiM
    golden_cim = gen_square_cim(
        set_parameters.HV_DIM, seed_input_list, im_type="ca90_hier"
    )

    # Input the seed
    dut.seed_hv_i.value = seed_input

    # Propagate time for logic
    await Timer(1, units="ps")

    # Use select and check for values
    num_cim_levels = int(set_parameters.HV_DIM / 2)

    for i in range(num_cim_levels):
        # Input the selection
        dut.cim_sel_i.value = i

        # Propagate time for logic
        await Timer(1, units="ps")

        # Obtain actual value
        actual_val = dut.cim_o.value.integer
        actual_val = numbin2list(actual_val, set_parameters.HV_DIM)

        # Convert golden to number
        golden_val = golden_cim[i]

        # Compare to golden
        check_result_array(actual_val, golden_val)

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
        }
    ],
)
def test_cim(simulator, parameters):
    verilog_sources = [
        "/rtl/item_memory/ca90_unit.sv",
        "/rtl/item_memory/ca90_hier_base.sv",
        "/rtl/item_memory/cim_bit_flip.sv",
        "/rtl/item_memory/cim.sv",
    ]

    toplevel = "cim"

    module = "test_cim"

    setup_and_run(
        verilog_sources=verilog_sources,
        toplevel=toplevel,
        module=module,
        simulator=simulator,
        parameters=parameters,
        waves=True,
    )
