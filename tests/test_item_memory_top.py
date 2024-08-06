"""
  Copyright 2024 KU Leuven
  Ryan Antonio <ryan.antonio@esat.kuleuven.be>

  Description:
  This tests the memory holding FIFO
"""

import set_parameters
import cocotb
from cocotb.clock import Clock
from cocotb.triggers import Timer
import pytest
import sys

from util import (
    get_root,
    setup_and_run,
    check_result,
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


# Working functions
def clear_inputs_no_clock(dut):
    # Initialize all other ports to 0
    # Exclude CSR related ports
    dut.clr_i.value = 0

    dut.lowdim_a_data_i.value = 0
    dut.highdim_a_data_i.value = 0
    dut.im_a_data_valid_i.value = 0

    dut.lowdim_b_data_i.value = 0
    dut.highdim_b_data_i.value = 0
    dut.im_b_data_valid_i.value = 0

    dut.im_a_pop_i.value = 0
    dut.im_b_pop_i.value = 0

    return


async def load_im_addr(dut, data, port="a", high_dim=False, seq_exe=True):
    if port == "a":
        if high_dim:
            dut.highdim_a_data_i.value = data
        else:
            dut.lowdim_a_data_i.value = data
        dut.im_a_data_valid_i.value = 1
    else:
        if high_dim:
            dut.highdim_b_data_i.value = data
        else:
            dut.lowdim_b_data_i.value = data
        dut.im_b_data_valid_i.value = 1
    if seq_exe:
        await clock_and_time(dut.clk_i)
        clear_inputs_no_clock(dut)
    return


async def read_and_pop(dut, port="a", seq_exe=True):
    if port == "a":
        im_val = dut.im_a_o.value.integer
        dut.im_a_pop_i.value = 1
    else:
        im_val = dut.im_b_o.value.integer
        dut.im_b_pop_i.value = 1
    im_val = numbin2list(im_val, set_parameters.HV_DIM)
    if seq_exe:
        await clock_and_time(dut.clk_i)
        clear_inputs_no_clock(dut)
    return im_val


@cocotb.test()
async def item_memory_top_dut(dut):
    cocotb.log.info(" ------------------------------------------ ")
    cocotb.log.info("              Item Memory Top               ")
    cocotb.log.info(" ------------------------------------------ ")

    cocotb.log.info(" ------------------------------------------ ")
    cocotb.log.info("               Initial reset                ")
    cocotb.log.info(" ------------------------------------------ ")

    clear_inputs_no_clock(dut)
    dut.rst_ni.value = 0
    dut.cim_seed_hv_i.value = 0
    dut.im_seed_hv_i.value = 0
    dut.port_a_cim_i.value = 0
    dut.port_b_cim_i.value = 0
    dut.enable_i.value = 0

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

    # Enable system too
    dut.enable_i.value = 1

    # Propagate time for logic
    await clock_and_time(dut.clk_i)

    cocotb.log.info(" ------------------------------------------ ")
    cocotb.log.info("         Testing FIFO Capabilities          ")
    cocotb.log.info(" ------------------------------------------ ")

    # First fill the entire buffer
    for i in range(set_parameters.HOLD_FIFO_DEPTH):
        await load_im_addr(dut, i, port="a")
        await load_im_addr(dut, i, port="b")

    # Since we filled the entire buffer
    # we check if it's full and it should set
    # the ready ports of the streamer side to 0
    fifo_a_full = dut.im_a_data_ready_o.value.integer
    check_result(fifo_a_full, 0)

    fifo_b_full = dut.im_b_data_ready_o.value.integer
    check_result(fifo_b_full, 0)

    # For wave-form viewing purposes
    clear_inputs_no_clock(dut)
    await clock_and_time(dut.clk_i)

    # Read and pop the outputs
    for i in range(set_parameters.HOLD_FIFO_DEPTH):
        # Read and check value firsts
        im_a_val = await read_and_pop(dut, port="a")
        check_result_array(im_a_val, golden_im[i])

        im_b_val = await read_and_pop(dut, port="b")
        check_result_array(im_b_val, golden_im[i])

    # The FIFOs need to be empty at this point
    # check if the ready signal is asserted
    fifo_a_full = dut.im_a_data_ready_o.value.integer
    check_result(fifo_a_full, 1)

    fifo_b_full = dut.im_b_data_ready_o.value.integer
    check_result(fifo_b_full, 1)

    cocotb.log.info(" ------------------------------------------ ")
    cocotb.log.info("           In-and-Out LowDim FIFO           ")
    cocotb.log.info(" ------------------------------------------ ")

    for i in range(set_parameters.TEST_RUNS):
        # Disable clock to allow parallel load
        await load_im_addr(dut, i, port="a", seq_exe=False)
        await load_im_addr(dut, i, port="b")

        # Read and check value firsts
        im_a_val = await read_and_pop(dut, port="a", seq_exe=False)
        check_result_array(im_a_val, golden_im[i])

        im_b_val = await read_and_pop(dut, port="b")
        check_result_array(im_b_val, golden_im[i])

    # For the next test
    clear_inputs_no_clock(dut)
    await clock_and_time(dut.clk_i)

    cocotb.log.info(" ------------------------------------------ ")
    cocotb.log.info("          In-and-Out HighDim FIFO           ")
    cocotb.log.info(" ------------------------------------------ ")

    # Set control signals to activate high-dimensional ports only
    dut.port_a_cim_i.value = 2
    dut.port_b_cim_i.value = 1

    for i in range(set_parameters.TEST_RUNS):
        # Disable clock to allow parallel load
        highdim_data = hvlist2num(golden_im[i])
        await load_im_addr(dut, highdim_data, port="a", high_dim=True, seq_exe=False)
        await load_im_addr(dut, highdim_data, port="b", high_dim=True)

        # Read and check value firsts
        im_a_val = await read_and_pop(dut, port="a", seq_exe=False)
        check_result_array(im_a_val, golden_im[i])

        im_b_val = await read_and_pop(dut, port="b")
        check_result_array(im_b_val, golden_im[i])

    # For the next test
    clear_inputs_no_clock(dut)
    await clock_and_time(dut.clk_i)

    cocotb.log.info(" ------------------------------------------ ")
    cocotb.log.info("          Testing Stall Signals             ")
    cocotb.log.info(" ------------------------------------------ ")

    # Note that at this point the FIFOs are empty
    # because the previous test empties the FIFOs

    # Assert the pop signal and see if stall asserts
    dut.im_a_pop_i.value = 1

    # Propagate time for logic
    await clock_and_time(dut.clk_i)

    # Check if the stall signal is asserted
    stall_val = dut.stall_o.value.integer
    check_result(stall_val, 1)

    # Set back to 0
    dut.im_a_pop_i.value = 0

    # Propagate time for logic
    await clock_and_time(dut.clk_i)

    # Check if the stall signal is de-asserted
    stall_val = dut.stall_o.value.integer
    check_result(stall_val, 0)

    # Do the same for other port
    dut.im_b_pop_i.value = 1

    # Propagate time for logic
    await clock_and_time(dut.clk_i)

    # Check if the stall signal is asserted
    stall_val = dut.stall_o.value.integer
    check_result(stall_val, 1)

    # Set back to 0
    dut.im_b_pop_i.value = 0

    # Propagate time for logic
    await clock_and_time(dut.clk_i)

    # Check if the stall signal is de-asserted
    stall_val = dut.stall_o.value.integer
    check_result(stall_val, 0)

    # This time, we first load the FIFOs
    # a single element only
    highdim_data = hvlist2num(golden_im[0])
    await load_im_addr(dut, highdim_data, port="a", high_dim=True, seq_exe=False)
    await load_im_addr(dut, highdim_data, port="b", high_dim=True)

    # Assert the pop signal and see if stall asserts
    dut.im_a_pop_i.value = 1
    dut.im_b_pop_i.value = 1

    # Propagate time but not clock
    await Timer(1, units="ps")

    # Check and see that the stall signal should not be asserted
    stall_val = dut.stall_o.value.integer
    check_result(stall_val, 0)

    # Propagate time for logic
    await clock_and_time(dut.clk_i)

    # Bring pops to 0
    dut.im_a_pop_i.value = 0
    dut.im_b_pop_i.value = 0

    # This is for waveform checking later
    for i in range(set_parameters.TEST_RUNS):
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
            "HoldFifoDepth": str(set_parameters.HOLD_FIFO_DEPTH),
        }
    ],
)
def test_item_memory_top(simulator, parameters, waves):
    verilog_sources = [
        # Level 0
        "/rtl/common/fifo_buffer.sv",
        "/rtl/common/mux.sv",
        "/rtl/item_memory/ca90_unit.sv",
        "/rtl/item_memory/cim_bit_flip.sv",
        # Level 1
        "/rtl/item_memory/ca90_hier_base.sv",
        # Level 2
        "/rtl/item_memory/cim.sv",
        "/rtl/item_memory/ca90_item_memory.sv",
        # Level 3
        "/rtl/item_memory/item_memory.sv",
        # Level 4
        "/rtl/item_memory/item_memory_top.sv",
    ]

    toplevel = "item_memory_top"

    module = "test_item_memory_top"

    setup_and_run(
        verilog_sources=verilog_sources,
        toplevel=toplevel,
        module=module,
        simulator=simulator,
        parameters=parameters,
        waves=waves,
    )
