"""
  Copyright 2024 KU Leuven
  Ryan Antonio <ryan.antonio@esat.kuleuven.be>

  Description:
  This tests the functionality of the adder tree.
  Note that the adder tree can take multiple inputs.
  In this test we just try out the 8-bit functionality.
"""

from util import setup_and_run, gen_randint, check_result

import cocotb
from cocotb.triggers import Timer
import pytest

# Some local parameters for testing
NUM_INPUTS = 8
IN_DATA_WIDTH = 8

NUM_TEST = 50
# MAX VAL 2's complement
MAX_VAL = 2 ** (IN_DATA_WIDTH - 1) - 1
MIN_VAL = -(2 ** (IN_DATA_WIDTH - 1))


# Set inputs to 0
def clear_inputs(dut):
    # Write ports
    for i in range(NUM_INPUTS):
        dut.data_i[i].value = 0
    return


def load_inputs(dut):
    data_list = []
    for i in range(NUM_INPUTS):
        data_list.append(gen_randint(MIN_VAL, MAX_VAL))
        dut.data_i[i].value = data_list[i]
    return data_list


@cocotb.test()
async def adder_tree_dut(dut):
    cocotb.log.info(" ------------------------------------------ ")
    cocotb.log.info("            Testing Adder Tree              ")
    cocotb.log.info(" ------------------------------------------ ")

    # Initialize input values
    clear_inputs(dut)
    await Timer(1, "ns")

    for i in range(NUM_TEST):
        # Load random inputs
        data_list = load_inputs(dut)

        # Wait for the output to stabilize
        await Timer(1, "ns")

        # Check the result
        expected_sum = sum(data_list)
        check_result(dut.adder_tree_data_o.value.signed_integer, expected_sum)

    # For waveform purposes only
    await Timer(10, "ns")


# Actual test run
@pytest.mark.parametrize(
    "parameters",
    [
        {
            "NumInputs": str(NUM_INPUTS),
            "InDataWidth": str(IN_DATA_WIDTH),
        }
    ],
)
def test_adder_tree(simulator, parameters, waves):
    verilog_sources = ["/rtl/common/adder_tree.sv"]

    toplevel = "adder_tree"

    module = "test_adder_tree"

    setup_and_run(
        verilog_sources=verilog_sources,
        toplevel=toplevel,
        module=module,
        simulator=simulator,
        parameters=parameters,
        waves=waves,
    )
