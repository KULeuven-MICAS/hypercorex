"""
  Copyright 2024 KU Leuven
  Ryan Antonio <ryan.antonio@esat.kuleuven.be>

  Description:
  This tests the basic functionality
of the FIFO common module
"""

from util import setup_and_run, gen_rand_bits, clock_and_time, check_result

import cocotb
from cocotb.clock import Clock
import pytest

# Some local parameters for testing
FALL_THROUGH = 0
DATA_WIDTH = 32
FIFO_DEPTH = 32


# Set inputs to 0
def clear_inputs_no_clock(dut):
    # Write ports
    dut.clr_i.value = 0
    # Push port
    dut.data_i.value = 0
    dut.push_i.value = 0
    # Pop port
    dut.pop_i.value = 0
    return


# Push to FIFO
async def push_fifo(dut, data):
    clear_inputs_no_clock(dut)
    dut.data_i.value = data
    dut.push_i.value = 1
    await clock_and_time(dut.clk_i)
    clear_inputs_no_clock(dut)
    return


# Read first then pop
async def pop_fifo(dut):
    clear_inputs_no_clock(dut)
    data = dut.data_o.value.integer
    dut.pop_i.value = 1
    await clock_and_time(dut.clk_i)
    clear_inputs_no_clock(dut)
    return data


# Clear FIFO
async def clr_fifo(dut):
    dut.clr_i.value = 1
    await clock_and_time(dut.clk_i)


# Generate random data first
def gen_rand_data_list(num_elem, datawidth):
    rand_data_list = []
    for i in range(num_elem):
        rand_data_list.append(gen_rand_bits(datawidth))
    return rand_data_list


@cocotb.test()
async def fifo_dut(dut):
    cocotb.log.info(" ------------------------------------------ ")
    cocotb.log.info("             Testing FIFO unit              ")
    cocotb.log.info(" ------------------------------------------ ")

    # Initialize input values
    clear_inputs_no_clock(dut)
    dut.rst_ni.value = 0

    # Initialize clock always
    clock = Clock(dut.clk_i, 10, units="ns")
    cocotb.start_soon(clock.start(start_high=False))

    # Wait one cycle for reset
    await clock_and_time(dut.clk_i)

    dut.rst_ni.value = 1

    cocotb.log.info(" ------------------------------------------ ")
    cocotb.log.info("           Pushing data to FIFO             ")
    cocotb.log.info(" ------------------------------------------ ")

    rand_data_list = gen_rand_data_list(FIFO_DEPTH, DATA_WIDTH)

    for i in range(FIFO_DEPTH):
        # Get current counter and see if it's at the correct state
        counter_val = dut.counter_state_o.value.integer
        check_result(counter_val, i)
        await push_fifo(dut, rand_data_list[i])

    # Since the FIFO is full check if the full state is high
    # and check if the empty state is low
    full_state = dut.full_o.value.integer
    empty_state = dut.empty_o.value.integer
    check_result(full_state, 1)
    check_result(empty_state, 0)

    cocotb.log.info(" ------------------------------------------ ")
    cocotb.log.info("          Read and POP from FIFO            ")
    cocotb.log.info(" ------------------------------------------ ")

    for i in range(FIFO_DEPTH):
        # First check if counter decrement is correct
        counter_val = dut.counter_state_o.value.integer
        check_result(counter_val, FIFO_DEPTH - i)

        # Then pop the value
        pop_fifo_val = await pop_fifo(dut)
        check_result(pop_fifo_val, rand_data_list[i])

    # Since the FIFO is empty check if the full state is low
    # and check if the empty state is high
    full_state = dut.full_o.value.integer
    empty_state = dut.empty_o.value.integer
    check_result(full_state, 0)
    check_result(empty_state, 1)

    cocotb.log.info(" ------------------------------------------ ")
    cocotb.log.info("            Fill and clear FIFO             ")
    cocotb.log.info(" ------------------------------------------ ")

    clear_inputs_no_clock(dut)

    # Fill FIFO again can do rechecking for sanity purposes
    for i in range(FIFO_DEPTH):
        # Get current counter and see if it's at the correct state
        counter_val = dut.counter_state_o.value.integer
        check_result(counter_val, i)
        await push_fifo(dut, rand_data_list[i])

    # Clear FIFO
    await clr_fifo(dut)

    # A clear makes sure the FIFO is immediately empty
    full_state = dut.full_o.value.integer
    empty_state = dut.empty_o.value.integer
    check_result(full_state, 0)
    check_result(empty_state, 1)

    # For waveform purposes only
    for i in range(10):
        await clock_and_time(dut.clk_i)


# Actual test run
@pytest.mark.parametrize(
    "parameters",
    [
        {
            "DataWidth": str(DATA_WIDTH),
            "FifoDepth": str(FIFO_DEPTH),
        }
    ],
)
def test_fifo(simulator, parameters, waves):
    verilog_sources = ["/rtl/common/fifo_buffer.sv"]

    toplevel = "fifo_buffer"

    module = "test_fifo"

    setup_and_run(
        verilog_sources=verilog_sources,
        toplevel=toplevel,
        module=module,
        simulator=simulator,
        parameters=parameters,
        waves=waves,
    )
