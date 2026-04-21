"""
Copyright 2024 KU Leuven
Ryan Antonio <ryan.antonio@esat.kuleuven.be>

Description:
This program tests the VSAX ID-level top module which can
be used for any application that can do ID-level encoding.
"""

import cocotb
from cocotb.clock import Clock
import pytest
import numpy as np
import os
import sys

from util import (
    # General imports
    setup_and_run,
    clock_and_time,
    check_result,
)

# Importing main lib library
curr_dir = os.path.dirname(os.path.abspath(__file__))
lib_path = curr_dir + "/../lib"

sys.path.append(lib_path)

# Importing VSAX libraries
import vsax  # noqa: E402
import vsax_models  # noqa: E402
import vsax_util  # noqa: E402


# Writing to integer function for binary hypervectors
def hv_to_bin(hv: np.ndarray) -> str:
    """Convert a binary hypervector (1D numpy array of 0s/1s) to a binary string."""
    return int("".join(hv.astype(int).astype(str)), 2)


# Writing to memory class HV
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


# Read and verify data
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


# Some parameters about the architecture
HV_DIMENSION = 512
SEED_IM = 42
PARALLEL_INPUTS_IM = 16
PARALLEL_INPUTS_ENC = PARALLEL_INPUTS_IM // 2
MAX_PARALLEL_INPUTS_ENC = 2**PARALLEL_INPUTS_ENC - 1
CSR_REG_WIDTH = 8
NUM_TOT_IM = 1024
COUNTER_WIDTH_ENC = 8
NUM_CLASS_AM = 32
DISABLE_TQDM = True
GEN_TYPE = "lfsr"

# Test parameters
NUM_FEATURES = 28 * 28
NUM_ENC_ITERATIONS = NUM_FEATURES // PARALLEL_INPUTS_IM * 2
CLASS_LIST = [0, 1, 2, 3, 4, 5, 6, 7, 8, 9]
CLASS_LEN = len(CLASS_LIST)

# Path directories
curr_dir = os.path.dirname(os.path.abspath(__file__))
lib_path = curr_dir + "/../lib"
data_path = curr_dir + "/../data"
dataset_path = data_path + "/mnist_bin"
model_path = curr_dir + "/../models"
model_name = "vsax_bin_idlvl_digit_recog"
model_file = model_name + f"_d{HV_DIMENSION}.npz"
model_dir = model_path + f"/{model_file}"


# Download existing model
vsax_util.download_file(
    url=f"{vsax_util.git_trained_models_url}/{model_file}",
    out_dir=model_path,
    filename=model_file,
)

# Downloading and extracting the MNIST dataset
vsax_util.download_and_extract(
    url=vsax_util.vsax_data_url_bin_mnist,
    out_dir=data_path,
    delete_archive=True,
)

# Read data
X_data = vsax_util.read_data(CLASS_LIST, dataset_path, disable_tqdm=DISABLE_TQDM)


# Make class for digit model
class digitVSA(vsax_models.vsaModel):
    def encode(self, item_data):
        # Feature length
        item_len = len(item_data)
        # Threshold for binarization
        threshold = item_len // 2
        # Encode hypervector
        encoded_vec = vsax.hv_gen_empty(self.hv_size)
        for i in range(item_len):
            bind_id_level = vsax.hv_bind(
                self.ortho_im[i + 2],  # level offset by 2
                self.ortho_im[item_data[i]],  # 1st 2 are reserved for level encoding
                self.hv_type,
            )
            encoded_vec += bind_id_level
        # Binarization
        if self.binarize_encode:
            encoded_vec = vsax.hv_binarize(encoded_vec, threshold, self.hv_type)
        return encoded_vec


# Make digit class
digit_model = digitVSA(
    model_name=model_name,
    hv_size=HV_DIMENSION,
    class_list=CLASS_LIST,
    gen_type=GEN_TYPE,
)

# Load an existing trained model
digit_model.load_model(model_dir)
class_am = digit_model.class_am_bin
bin_class_am = (class_am + 1) // 2


def clear_inputs_no_clock(dut):
    # Item memories
    for i in range(PARALLEL_INPUTS_IM):
        dut.im_rd_i[i].value = 0
    # Encoder
    dut.enc_valid_i.value = 0
    dut.enc_clr_i.value = 0
    # QHV
    dut.qhv_wen_i.value = 0
    dut.qhv_clr_i.value = 0
    dut.qhv_am_load_i.value = 0
    # AM external control
    dut.w_valid_i.value = 0
    dut.w_en_i.value = 0
    dut.w_addr_i.value = 0
    dut.w_data_i.value = 0
    dut.external_read_sel_i.value = 0
    dut.ext_r_req_valid_i.value = 0
    dut.ext_r_addr_i.value = 0
    # always ready
    dut.ext_r_resp_ready_i.value = 1
    # AM search control
    dut.am_start_i.value = 0
    dut.am_num_class_i.value = CLASS_LEN
    # always ready
    dut.predict_ready_i.value = 1


# Actual test routines
@cocotb.test()
async def tb_vsax_id_level_top(dut):
    cocotb.log.info(" ------------------------------------------ ")
    cocotb.log.info("     Testing VSAX ID-level top module       ")
    cocotb.log.info(" ------------------------------------------ ")

    # ---- Initialise ----
    clear_inputs_no_clock(dut)
    dut.rst_ni.value = 0

    clock = Clock(dut.clk_i, 10, units="ns")
    cocotb.start_soon(clock.start(start_high=False))

    await clock_and_time(dut.clk_i)
    dut.rst_ni.value = 1
    await clock_and_time(dut.clk_i)

    cocotb.log.info(" ------------------------------------------ ")
    cocotb.log.info("    Writing to latch memory class HVs...    ")
    cocotb.log.info(" ------------------------------------------ ")
    for i in range(len(CLASS_LIST)):
        # Write class HVs into the AM latch memory
        await write_class_hv(dut, addr=i, data=hv_to_bin(bin_class_am[i]))

    cocotb.log.info(" ------------------------------------------ ")
    cocotb.log.info("     Reading and verifying class HVs...     ")
    cocotb.log.info(" ------------------------------------------ ")

    # Make sure to set selector to external first
    dut.external_read_sel_i.value = 1
    for i in range(len(CLASS_LIST)):
        await read_verify_class_hv(dut, addr=i, expected=hv_to_bin(bin_class_am[i]))

    # Bring back to internal selector for the rest of the test (AM search)
    dut.external_read_sel_i.value = 0

    cocotb.log.info("Predict 1 class each...")
    for iter in range(CLASS_LEN):
        cocotb.log.info(f" ITERATION - {iter} ")

        cocotb.log.info("Encoding image")
        for i in range(NUM_ENC_ITERATIONS):
            dut.enc_valid_i.value = MAX_PARALLEL_INPUTS_ENC
            for j in range(PARALLEL_INPUTS_IM // 2):
                # This plus 2 offsets the binary 1 or 0
                dut.im_rd_i[j].value = i * (PARALLEL_INPUTS_IM // 2) + j + 2
                # The selection below selects or feeds the binary inputs
                dut.im_rd_i[PARALLEL_INPUTS_IM // 2 + j].value = int(
                    X_data[iter][0][i * (PARALLEL_INPUTS_IM // 2) + j]
                )
            await clock_and_time(dut.clk_i)

        # Clear outputs again
        clear_inputs_no_clock(dut)

        cocotb.log.info("Saving bundled HV into QHV...")

        dut.qhv_wen_i.value = 1
        await clock_and_time(dut.clk_i)
        clear_inputs_no_clock(dut)

        cocotb.log.info("AM search for predicted class...")

        dut.am_start_i.value = 1
        await clock_and_time(dut.clk_i)
        dut.am_start_i.value = 0

        # Wait for predict_valid_o
        while not dut.predict_valid_o.value.integer:
            await clock_and_time(dut.clk_i)

        cocotb.log.info("System clear...")
        clear_inputs_no_clock(dut)
        await clock_and_time(dut.clk_i)
        dut.enc_clr_i.value = 1
        dut.qhv_clr_i.value = 1
        await clock_and_time(dut.clk_i)
        clear_inputs_no_clock(dut)
        await clock_and_time(dut.clk_i)

    # Some trailing cycles only
    for i in range(5):
        await clock_and_time(dut.clk_i)


# Config and run
@pytest.mark.parametrize(
    "parameters",
    [
        {
            # General parameters
            "HVDimension": str(HV_DIMENSION),
            "CsrRegWidth": str(CSR_REG_WIDTH),
            # Item memory specific
            "SeedIm": str(SEED_IM),
            "ParallelInputsIm": str(PARALLEL_INPUTS_IM),
            "NumTotIm": str(NUM_TOT_IM),
            # Encoder specific
            "CounterWidthEnc": str(COUNTER_WIDTH_ENC),
            # Assoc memory specific
            "NumClassAm": str(NUM_CLASS_AM),
        }
    ],
)
def test_vsax_id_level_top(simulator, parameters, waves):
    verilog_sources = [
        "/rtl/common/adder_tree.sv",
        "/rtl/common/latch_memory.sv",
        "/rtl/item_memory/rom_lfsr_item_memory.sv",
        "/rtl/encoder/multi_in_bundler_unit.sv",
        "/rtl/encoder/multi_in_bundler_set.sv",
        "/rtl/encoder/qhv.sv",
        "/rtl/encoder/id_level_encoder.sv",
        "/rtl/assoc_memory/ham_dist.sv",
        "/rtl/assoc_memory/binary_compare.sv",
        "/rtl/assoc_memory/bin_sim_search.sv",
        "/rtl/assoc_memory/assoc_mem_top.sv",
        "/rtl/system_top/vsax_id_level_top.sv",
    ]
    toplevel = "vsax_id_level_top"

    module = "test_vsax_id_level_top"

    setup_and_run(
        verilog_sources=verilog_sources,
        toplevel=toplevel,
        module=module,
        simulator=simulator,
        parameters=parameters,
        waves=waves,
    )
