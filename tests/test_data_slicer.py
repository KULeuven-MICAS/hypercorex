"""
  Copyright 2024 KU Leuven
  Ryan Antonio <ryan.antonio@esat.kuleuven.be>

  Description:
  This tests the functionality of the data slicer
"""

from util import setup_and_run, gen_rand_bits, clock_and_time, check_result

import cocotb
from cocotb.clock import Clock
import pytest
import set_parameters
import random

# Somer internal parameters
MAX_NUM_ELEM = 100
MIN_NUM_ELEM = 10


# Generate random numbers
def random_int(min_val, max_val):
    return random.randint(min_val, max_val)


# Set inputs to 0
def clear_inputs_no_clock(dut):
    dut.clr_i.value = 0
    dut.enable_i.value = 0
    dut.clr_i.value = 0
    dut.sel_mode_i.value = 0
    dut.csr_elem_size_i.value = 0
    dut.lowdim_data_i.value = 0
    dut.lowdim_data_valid_i.value = 0
    dut.addr_ready_i.value = 0
    return


async def load_lowdim_data(dut, data):
    dut.lowdim_data_i.value = data
    dut.lowdim_data_valid_i.value = 1
    await clock_and_time(dut.clk_i)
    dut.lowdim_data_i.value = 0
    dut.lowdim_data_valid_i.value = 0
    return


def load_lowdim_data_no_clk(dut, data):
    dut.lowdim_data_i.value = data
    dut.lowdim_data_valid_i.value = 1
    return


def clear_low_dim_data(dut):
    dut.lowdim_data_i.value = 0
    dut.lowdim_data_valid_i.value = 0
    return


async def clear(dut):
    dut.clk_i.value = 1
    await clock_and_time(dut.clk_i)
    dut.clk_i.value = 0
    return


async def data_slice_test(dut, mode):
    # Set num of slices
    if mode == 1:
        num_slices = 64
        shift_factor = 1
        mask_val = 0x1
    elif mode == 2:
        num_slices = 16
        shift_factor = 4
        mask_val = 0xF
    elif mode == 3:
        num_slices = 8
        shift_factor = 8
        mask_val = 0xFF
    else:
        raise ValueError("Invalid mode entry!")

    # Load some starting configs
    num_elem_test = random_int(MIN_NUM_ELEM, MAX_NUM_ELEM)
    dut.csr_elem_size_i.value = num_elem_test
    dut.sel_mode_i.value = mode

    # Calculate how many rounds and the remainder
    num_rounds = num_elem_test // num_slices
    num_remainder = num_elem_test % num_slices

    # Cycle through all 64b rounds
    # Check MSB if correct
    for i in range(num_rounds):
        input_data = gen_rand_bits(set_parameters.NARROW_DATA_WIDTH)
        load_lowdim_data_no_clk(dut, input_data)

        # Cycle some time and check the value
        for i in range(num_slices):
            await clock_and_time(dut.clk_i)
            golden_val = (input_data >> (i * shift_factor)) & mask_val
            check_result(dut.addr_o.value.integer, golden_val)

    if num_remainder != 0:
        # Do the remainder of the data
        input_data = gen_rand_bits(set_parameters.NARROW_DATA_WIDTH)
        load_lowdim_data_no_clk(dut, input_data)
        for i in range(num_remainder):
            await clock_and_time(dut.clk_i)
            golden_val = (input_data >> (i * shift_factor)) & mask_val
            check_result(dut.addr_o.value.integer, golden_val)

    # Clear inputs
    clear_low_dim_data(dut)
    return


# Generate random data first
def gen_rand_data_list(num_elem, datawidth):
    rand_data_list = []
    for i in range(num_elem):
        rand_data_list.append(gen_rand_bits(datawidth))
    return rand_data_list


@cocotb.test()
async def data_slicer_dut(dut):
    cocotb.log.info(" ------------------------------------------ ")
    cocotb.log.info("          Testing Data Slicer unit          ")
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
    await clock_and_time(dut.clk_i)

    # Check first that the output valid is not asserted
    out_valid = dut.addr_valid_o.value
    check_result(out_valid, 0)

    cocotb.log.info(" ------------------------------------------ ")
    cocotb.log.info("              Testing 64b Case              ")
    cocotb.log.info(" ------------------------------------------ ")

    # Load some starting configs for the 64b case
    num_elem_test = random_int(MIN_NUM_ELEM, MAX_NUM_ELEM)
    dut.csr_elem_size_i.value = num_elem_test

    dut.sel_mode_i.value = 0
    dut.enable_i.value = 1
    dut.addr_ready_i.value = 1

    # Load random data then check immediatley
    for i in range(num_elem_test):
        golden_val = gen_rand_bits(set_parameters.IM_ADDR_WIDTH)
        await load_lowdim_data(dut, golden_val)
        output_val = dut.addr_o.value.integer
        check_result(output_val, golden_val)

    # Clear system
    await clear(dut)

    # For waveform purposes only
    for i in range(10):
        await clock_and_time(dut.clk_i)

    cocotb.log.info(" ------------------------------------------ ")
    cocotb.log.info("               1bit Slice Case              ")
    cocotb.log.info(" ------------------------------------------ ")

    await data_slice_test(dut, 1)

    cocotb.log.info(" ------------------------------------------ ")
    cocotb.log.info("               4bit Slice Case              ")
    cocotb.log.info(" ------------------------------------------ ")

    await data_slice_test(dut, 2)

    cocotb.log.info(" ------------------------------------------ ")
    cocotb.log.info("               8bit Slice Case              ")
    cocotb.log.info(" ------------------------------------------ ")

    await data_slice_test(dut, 3)

    # For waveform purposes only
    for i in range(10):
        await clock_and_time(dut.clk_i)


# Actual test run
@pytest.mark.parametrize(
    "parameters",
    [
        {
            "LowDimWidth": str(set_parameters.NARROW_DATA_WIDTH),
            "NumTotIm": str(set_parameters.NUM_TOT_IM),
            "SlicerFifoDepth": str(set_parameters.SLICER_FIFO_DEPTH),
            "CsrRegWidth": str(set_parameters.REG_FILE_WIDTH),
        }
    ],
)
def test_data_slicer(simulator, parameters, waves):
    verilog_sources = ["/rtl/common/fifo_buffer.sv", "/rtl/common/data_slicer.sv"]

    toplevel = "data_slicer"

    module = "test_data_slicer"

    setup_and_run(
        verilog_sources=verilog_sources,
        toplevel=toplevel,
        module=module,
        simulator=simulator,
        parameters=parameters,
        waves=waves,
    )
