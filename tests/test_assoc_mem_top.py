"""
Copyright 2024 KU Leuven
Ryan Antonio <ryan.antonio@esat.kuleuven.be>

Description:
Test for the assoc_mem_top wrapper.
The test runs in three phases:

  Phase 1 - Memory write:
    Switch external_read_sel_i=1 and write all class HVs into
    the latch memory one word at a time, waiting for w_ready_o
    between writes.

  Phase 2 - Memory read-back verify:
    Still with external_read_sel_i=1, read every address back
    through the external read port and check the data matches.

  Phase 3 - Similarity search:
    Switch external_read_sel_i=0 and run the similarity search.
    Includes a mid-search stall assertion check and a final
    prediction correctness check.
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
import sys
import pytest
import random

# Add hdc utility functions
hdc_util_path = get_root() + "/hdc_exp/"
print(hdc_util_path)
sys.path.append(hdc_util_path)

from hdc_util import binarize_hv, prediction_idx  # noqa: E402

# Fixed dimension for this test suite
HV_DIM = 128
# Max classes that can be stored (matches NumClass parameter on DUT)
MAX_CLASS = 32


# ------------------------------------------------------------------
# Input helpers
# ------------------------------------------------------------------


def clear_inputs_no_clock(dut):
    """Drive all inputs to their idle/safe state (no clock tick needed)."""
    # Write side
    dut.w_valid_i.value = 0
    dut.w_en_i.value = 0
    dut.w_addr_i.value = 0
    dut.w_data_i.value = 0
    # External read port (sel=1: external owns the channel)
    dut.external_read_sel_i.value = 1
    dut.ext_r_req_valid_i.value = 0
    dut.ext_r_addr_i.value = 0
    dut.ext_r_resp_ready_i.value = 1  # always ready to accept responses
    # Search side
    dut.query_hv_i.value = 0
    dut.am_start_i.value = 0
    dut.am_num_class_i.value = 0
    dut.am_predict_valid_clr_i.value = 0
    dut.predict_ready_i.value = 1


# ------------------------------------------------------------------
# Phase 1: write helpers
# ------------------------------------------------------------------


async def write_class_hv(dut, addr, data):
    """
    Write one class HV into the latch memory.
    Waits for w_ready_o before asserting valid (the memory may still
    be in WRITE/CLEAR cycles from the previous word).
    After the write, waits until w_ready_o returns high (IDLE) before
    returning so back-to-back calls are always safe.
    """
    # Wait for memory to be ready
    while not dut.w_ready_o.value.integer:
        await clock_and_time(dut.clk_i)

    dut.w_valid_i.value = 1
    dut.w_en_i.value = 1
    dut.w_addr_i.value = addr
    dut.w_data_i.value = data
    await clock_and_time(dut.clk_i)  # captured; w_ready_o goes low
    dut.w_valid_i.value = 0
    dut.w_en_i.value = 0

    # Wait for the 3-cycle write sequence to
    # complete (WRITE→CLEAR_WEN→CLEAR_CAPTURES→IDLE)
    while not dut.w_ready_o.value.integer:
        await clock_and_time(dut.clk_i)


# ------------------------------------------------------------------
# Phase 2: read-back verify helpers
# ------------------------------------------------------------------


async def read_verify_class_hv(dut, addr, expected):
    """
    Issue one read request on the external read port and verify the
    returned data matches expected.

    Timing (latch_memory read path, 1-cycle latency):
      T0: assert ext_r_req_valid_i=1, addr; clock edge captures the request
          and registers r_resp_valid_o=1, r_resp_data_o=memory[addr].
      T1: response is stable; sample and check.
          With ext_r_resp_ready_i permanently high the memory clears
          r_resp_valid_o on this same edge.
    """
    # ext_r_req_ready_o should be 1 here (we are not in a write cycle)
    dut.ext_r_req_valid_i.value = 1
    dut.ext_r_addr_i.value = addr
    await clock_and_time(dut.clk_i)  # T0 edge: response registered
    dut.ext_r_req_valid_i.value = 0

    # Response is now valid; sample before the next edge clears it
    check_result(dut.ext_r_resp_valid_o.value.integer, 1)
    actual = dut.ext_r_resp_data_o.value.integer
    check_result(actual, expected)

    await clock_and_time(dut.clk_i)  # T1 edge: resp_valid cleared by ready


# ------------------------------------------------------------------
# Phase 3: similarity search helper
# ------------------------------------------------------------------


async def load_query_and_start(dut, query_hv):
    """Present the query HV and pulse am_start_i for one cycle."""
    dut.query_hv_i.value = query_hv
    dut.am_start_i.value = 1
    await clock_and_time(dut.clk_i)
    dut.am_start_i.value = 0


# ------------------------------------------------------------------
# Data generator
# ------------------------------------------------------------------


def gen_am_and_qv(num_classes, hv_dim):
    """
    Returns (golden_idx, query_hv_int, sim_search_ints).
    The query is constructed so that prediction_idx returns a
    deterministic golden answer.
    """
    sim_search = [
        numbin2list(gen_rand_bits(hv_dim), hv_dim) for _ in range(num_classes)
    ]

    random_idx = random.randrange(num_classes)

    temp_hv1 = numbin2list(gen_rand_bits(hv_dim), hv_dim)
    temp_hv2 = numbin2list(gen_rand_bits(hv_dim), hv_dim)
    query_hv = binarize_hv(temp_hv1 + temp_hv2 + sim_search[random_idx], 1.5)

    golden_idx = prediction_idx(sim_search, query_hv, "binary")

    query_hv_int = hvlist2num(query_hv)
    sim_search_int = [hvlist2num(sim_search[i]) for i in range(num_classes)]

    return golden_idx, query_hv_int, sim_search_int


# ------------------------------------------------------------------
# Main test
# ------------------------------------------------------------------


@cocotb.test()
async def assoc_mem_top_dut(dut):
    cocotb.log.info(" ------------------------------------------ ")
    cocotb.log.info("       Testing Associative Memory Top       ")
    cocotb.log.info(" ------------------------------------------ ")

    # ---- Initialise ----
    clear_inputs_no_clock(dut)
    dut.rst_ni.value = 0

    clock = Clock(dut.clk_i, 10, units="ns")
    cocotb.start_soon(clock.start(start_high=False))

    await clock_and_time(dut.clk_i)
    dut.rst_ni.value = 1
    await clock_and_time(dut.clk_i)

    # ==================================================================
    for run in range(set_parameters.TEST_RUNS):
        NUM_CLASSES = random.randint(10, MAX_CLASS)
        cocotb.log.info(f"Run {run}: {NUM_CLASSES} classes, HV dim {HV_DIM}")

        clear_inputs_no_clock(dut)

        golden_idx, query_hv, sim_search = gen_am_and_qv(NUM_CLASSES, HV_DIM)

        # --------------------------------------------------------------
        # Phase 1 — Write class HVs into latch memory
        # external_read_sel_i=1 keeps the search engine off the bus;
        # the write port is independent of the MUX, so writes work
        # regardless of sel, but keeping sel=1 is cleaner.
        # --------------------------------------------------------------
        cocotb.log.info("Phase 1: writing class HVs to memory")

        dut.external_read_sel_i.value = 1

        for addr, hv_data in enumerate(sim_search):
            await write_class_hv(dut, addr, hv_data)

        cocotb.log.info("Phase 1: all writes complete")

        # --------------------------------------------------------------
        # Phase 2 — Read back and verify every written address
        # --------------------------------------------------------------
        cocotb.log.info("Phase 2: verifying memory contents via external read port")

        for addr, expected in enumerate(sim_search):
            await read_verify_class_hv(dut, addr, expected)

        cocotb.log.info("Phase 2: all read-back checks passed")

        # --------------------------------------------------------------
        # Phase 3 — Similarity search
        # Switch sel=0 so bin_sim_search drives the latch memory read.
        # --------------------------------------------------------------
        cocotb.log.info("Phase 3: running similarity search")

        dut.external_read_sel_i.value = 0
        dut.am_num_class_i.value = NUM_CLASSES
        dut.predict_ready_i.value = 1

        # Pre-start: unit must be idle
        check_result(dut.am_busy_o.value.integer, 0)
        check_result(
            dut.class_hv_req_valid_o.value.integer
            if hasattr(dut, "class_hv_req_valid_o")
            else 0,
            0,
        )
        check_result(dut.predict_valid_o.value.integer, 0)
        check_result(dut.am_predict_valid_o.value.integer, 0)

        # Trigger the search
        await load_query_and_start(dut, query_hv)

        # Post-start: search engine should be active
        check_result(dut.am_busy_o.value.integer, 1)
        check_result(dut.predict_valid_o.value.integer, 0)

        # Stall check: assert am_start_i mid-search
        stall_wait = random.randint(1, max(1, NUM_CLASSES // 2))
        for _ in range(stall_wait):
            await clock_and_time(dut.clk_i)

        dut.am_start_i.value = 1
        await clock_and_time(dut.clk_i)
        check_result(dut.am_stall_o.value.integer, 1)

        dut.am_start_i.value = 0
        await clock_and_time(dut.clk_i)
        check_result(dut.am_stall_o.value.integer, 0)

        # Wait for search to finish (am_busy_o goes low)
        while dut.am_busy_o.value.integer == 1:
            await clock_and_time(dut.clk_i)

        # One extra cycle for last_compare_reg_save to pulse
        await clock_and_time(dut.clk_i)

        # Verify prediction result
        check_result(dut.predict_o.value.integer, golden_idx)
        check_result(dut.predict_valid_o.value.integer, 1)
        check_result(dut.am_predict_valid_o.value.integer, 1)

        # Clear valid and confirm both outputs drop
        dut.am_predict_valid_clr_i.value = 1
        await clock_and_time(dut.clk_i)

        check_result(dut.predict_valid_o.value.integer, 0)
        check_result(dut.am_predict_valid_o.value.integer, 0)

        dut.am_predict_valid_clr_i.value = 0

        cocotb.log.info(f"Run {run}: PASSED (predicted class {golden_idx})")

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
            "HVDimension": str(HV_DIM),
            "NumClass": str(MAX_CLASS),
            "DataWidth": str(set_parameters.REG_FILE_WIDTH),
        }
    ],
)
def test_assoc_mem_top(simulator, parameters, waves):
    verilog_sources = [
        "/rtl/common/latch_memory.sv",
        "/rtl/assoc_memory/ham_dist.sv",
        "/rtl/assoc_memory/binary_compare.sv",
        "/rtl/assoc_memory/bin_sim_search.sv",
        "/rtl/assoc_memory/assoc_mem_top.sv",
    ]

    toplevel = "assoc_mem_top"
    module = "test_assoc_mem_top"

    setup_and_run(
        verilog_sources=verilog_sources,
        toplevel=toplevel,
        module=module,
        simulator=simulator,
        parameters=parameters,
        waves=waves,
    )
