"""
Copyright 2024 KU Leuven
Ryan Antonio <ryan.antonio@esat.kuleuven.be>

Description:
This tests the bin_sim_search unit with the latch-memory request interface.
The memory is modelled as always-ready with 1-cycle read latency, matching
the assumption that no write traffic is active during inference.

Interface mapping to latch_memory:
    class_hv_req_valid_o  -> r_req_valid_i
    class_hv_req_ready_i  <- r_req_ready_o   (held high: always ready)
    class_hv_addr_o       -> r_addr_i
    class_hv_i            <- r_resp_data_o
    class_hv_valid_i      <- r_resp_valid_o
    class_hv_read_o       -> r_resp_ready_i
"""

import set_parameters
from util import (
    get_root,
    setup_and_run,
    gen_rand_bits,
    clock_and_time,
    hvlist2num,
    numbin2list,
    check_result,
)

import cocotb
from cocotb.clock import Clock
from cocotb.triggers import RisingEdge
import sys
import pytest
import random

# Add hdc utility functions
hdc_util_path = get_root() + "/hdc_exp/"
print(hdc_util_path)
sys.path.append(hdc_util_path)

from hdc_util import binarize_hv, prediction_idx  # noqa: E402


# ------------------------------------------------------------------
# Input helpers
# ------------------------------------------------------------------


def clear_inputs_no_clock(dut):
    """Drive all inputs to their idle/default state (no clock required)."""
    dut.query_hv_i.value = 0
    dut.am_start_i.value = 0
    dut.class_hv_i.value = 0
    dut.class_hv_valid_i.value = 0
    dut.class_hv_req_ready_i.value = 1  # memory is always ready
    dut.am_num_class_i.value = 0
    dut.am_predict_valid_clr_i.value = 0
    dut.predict_ready_i.value = 1


async def load_query_hv(dut, query_hv):
    """Present the query HV and pulse am_start_i for one cycle."""
    dut.query_hv_i.value = query_hv
    dut.am_start_i.value = 1
    await clock_and_time(dut.clk_i)
    # After this edge: busy_reg=1, req_counter=0, addr=0, req_valid=1
    dut.am_start_i.value = 0


# ------------------------------------------------------------------
# Data generator
# ------------------------------------------------------------------


def gen_am_and_qv(num_classes, hv_dim):
    """
    Generate a random associative memory and a noisy query that maps to
    one of the classes.  Returns (golden_idx, query_hv_int, sim_search_ints).
    """
    sim_search = [
        numbin2list(gen_rand_bits(hv_dim), hv_dim) for _ in range(num_classes)
    ]

    random_idx = random.randrange(num_classes)

    # Build a noisy query by bundling the target class with 2 random HVs
    temp_hv1 = numbin2list(gen_rand_bits(hv_dim), hv_dim)
    temp_hv2 = numbin2list(gen_rand_bits(hv_dim), hv_dim)
    query_hv = binarize_hv(temp_hv1 + temp_hv2 + sim_search[random_idx], 1.5)

    golden_idx = prediction_idx(sim_search, query_hv, "binary")

    # Convert to integers for DUT driving
    query_hv_int = hvlist2num(query_hv)
    sim_search_int = [hvlist2num(sim_search[i]) for i in range(num_classes)]

    return golden_idx, query_hv_int, sim_search_int


# ------------------------------------------------------------------
# Latch memory model
#
# Timing contract (matches latch_memory.sv when no writes are active):
#   - class_hv_req_ready_i is held permanently high
#   - A request accepted at rising edge N produces a response
#     (class_hv_i / class_hv_valid_i) at rising edge N+1
#
# Run this as a background cocotb task; call .kill() after each test run.
# ------------------------------------------------------------------


async def latch_memory_model(dut, sim_search):
    dut.class_hv_req_ready_i.value = 1
    pending_valid = 0
    pending_data = 0

    while True:
        await RisingEdge(dut.clk_i)

        # 1. Drive the response prepared in the previous cycle
        dut.class_hv_valid_i.value = pending_valid
        dut.class_hv_i.value = pending_data

        # 2. Sample the current outgoing request; prepare next response
        if dut.class_hv_req_valid_o.value.integer:
            addr = dut.class_hv_addr_o.value.integer
            pending_valid = 1
            pending_data = sim_search[addr]
        else:
            pending_valid = 0
            pending_data = 0


# ------------------------------------------------------------------
# Main test
# ------------------------------------------------------------------


@cocotb.test()
async def bin_sim_search_dut(dut):
    cocotb.log.info(" ------------------------------------------ ")
    cocotb.log.info("         Testing Associative Memory         ")
    cocotb.log.info(" ------------------------------------------ ")

    # ---- Initialise ----
    clear_inputs_no_clock(dut)
    dut.rst_ni.value = 0

    clock = Clock(dut.clk_i, 10, units="ns")
    cocotb.start_soon(clock.start(start_high=False))

    await clock_and_time(dut.clk_i)
    dut.rst_ni.value = 1

    cocotb.log.info(" ------------------------------------------ ")
    cocotb.log.info("      AM Check for Single Predictions       ")
    cocotb.log.info(" ------------------------------------------ ")

    for run in range(set_parameters.TEST_RUNS):
        NUM_CLASSES = random.randint(10, 32)
        cocotb.log.info(f"Run {run}: comparing {NUM_CLASSES} classes")

        clear_inputs_no_clock(dut)

        golden_idx, query_hv, sim_search = gen_am_and_qv(
            NUM_CLASSES, set_parameters.HV_DIM
        )

        dut.am_num_class_i.value = NUM_CLASSES
        dut.predict_ready_i.value = 1

        # ---- Pre-start: unit must be idle ----
        check_result(dut.am_busy_o.value.integer, 0)
        check_result(dut.class_hv_req_valid_o.value.integer, 0)
        check_result(dut.predict_valid_o.value.integer, 0)
        check_result(dut.am_predict_valid_o.value.integer, 0)

        # ---- Start background memory model ----
        mem_task = cocotb.start_soon(latch_memory_model(dut, sim_search))

        # ---- Trigger the search ----
        await load_query_hv(dut, query_hv)

        # ---- Post-start: verify request channel is live ----
        # After load_query_hv: busy=1, req_counter=0 (just reset), req_valid=1
        check_result(dut.am_busy_o.value.integer, 1)
        check_result(dut.class_hv_req_valid_o.value.integer, 1)
        check_result(dut.class_hv_addr_o.value.integer, 0)  # first address is 0
        check_result(
            dut.class_hv_read_o.value.integer, 1
        )  # ready for responses (= busy)
        check_result(dut.predict_valid_o.value.integer, 0)
        check_result(dut.am_predict_valid_o.value.integer, 0)

        # ---- Stall check: assert am_start_i mid-search ----
        # Wait up to NUM_CLASSES//2 cycles so we are well inside the search
        # window (search finishes at approximately NUM_CLASSES+2 cycles).
        stall_wait = random.randint(1, max(1, NUM_CLASSES // 2))
        for _ in range(stall_wait):
            await clock_and_time(dut.clk_i)

        # am_start_i while busy must assert am_stall_o
        dut.am_start_i.value = 1
        await clock_and_time(dut.clk_i)
        check_result(dut.am_stall_o.value.integer, 1)

        # Deasserting am_start_i must clear the stall
        dut.am_start_i.value = 0
        await clock_and_time(dut.clk_i)
        check_result(dut.am_stall_o.value.integer, 0)

        # ---- Wait for the search to finish ----
        # busy goes low when the last response handshake fires
        while dut.am_busy_o.value.integer == 1:
            await clock_and_time(dut.clk_i)

        # One extra cycle for last_compare_reg_save to pulse and
        # latch min_arg_idx / assert predict_valid
        await clock_and_time(dut.clk_i)

        # ---- Post-search checks ----
        check_result(dut.predict_o.value.integer, golden_idx)
        check_result(dut.predict_valid_o.value.integer, 1)
        check_result(dut.am_predict_valid_o.value.integer, 1)
        # All NUM_CLASSES requests were issued; req_valid must now be deasserted
        check_result(dut.class_hv_req_valid_o.value.integer, 0)
        # Not busy anymore, so response-ready is also low
        check_result(dut.class_hv_read_o.value.integer, 0)

        # ---- Clear valid and verify both valid outputs drop ----
        dut.am_predict_valid_clr_i.value = 1
        await clock_and_time(dut.clk_i)

        check_result(dut.predict_valid_o.value.integer, 0)
        check_result(dut.am_predict_valid_o.value.integer, 0)

        # Stop the memory model before the next iteration
        mem_task.kill()

    # Trailing idle cycles
    for _ in range(10):
        await clock_and_time(dut.clk_i)


# ------------------------------------------------------------------
# Config and run
# ------------------------------------------------------------------


@pytest.mark.parametrize(
    "parameters",
    [
        {
            "HVDimension": str(set_parameters.HV_DIM),
            "DataWidth": str(set_parameters.REG_FILE_WIDTH),
        }
    ],
)
def test_bin_sim_search(simulator, parameters, waves):
    verilog_sources = [
        "/rtl/assoc_memory/ham_dist.sv",
        "/rtl/assoc_memory/binary_compare.sv",
        "/rtl/assoc_memory/bin_sim_search.sv",
    ]

    toplevel = "bin_sim_search"
    module = "test_bin_sim_search"

    setup_and_run(
        verilog_sources=verilog_sources,
        toplevel=toplevel,
        module=module,
        simulator=simulator,
        parameters=parameters,
        waves=waves,
    )
