"""
    Copyright 2024 KU Leuven
    Ryan Antonio <ryan.antonio@esat.kuleuven.be>

    Description:
    This contains useful functions for managing
    the tests, script,s and generations
"""

# Importing useful tools
import random
import os
import cocotb
import hjson
from mako.template import Template
from mako.lookup import TemplateLookup
import JsonRef
from cocotb_test.simulator import run
from cocotb.triggers import Timer, RisingEdge
import numpy as np

"""
    Set of functions for test setups
"""


# For getting the root of the repository
def get_root():
    return os.getcwd()


# Setup and run functions
# Extracts necessary definitions and filelists
# Then invokes the run simulator
def setup_and_run(
    verilog_sources=None,
    defines=None,
    includes=None,
    toplevel="",
    module="",
    simulator="verilator",
    waves=False,
    parameters=None,
):
    # Extract global main root
    git_repo_root = get_root()

    # Set tests path, we use this by default
    tests_path = git_repo_root + "/tests"

    # Set the simulation build within test directory
    sim_build = tests_path + "/sim_build/{}/".format(toplevel)

    # Append git repo root for all items
    for i in range(len(verilog_sources)):
        verilog_sources[i] = git_repo_root + verilog_sources[i]

    # Setting of compilation arguments
    # and timescale depending on simulator
    if simulator == "verilator":
        compile_args = ["-Wno-WIDTH", "--no-timing", "--trace-structs"]
        timescale = None
    else:
        compile_args = None
        timescale = "1ns/1ps"

    run(
        verilog_sources=verilog_sources,
        includes=includes,
        toplevel=toplevel,
        defines=defines,
        module=module,
        simulator=simulator,
        sim_build=sim_build,
        compile_args=compile_args,
        timescale=timescale,
        waves=waves,
        parameters=parameters,
    )


# Extract json file
def get_config(cfg_path: str):
    with open(cfg_path, "r") as jsonf:
        srcfull = jsonf.read()

    # Format hjson file
    cfg = hjson.loads(srcfull, use_decimal=True)
    cfg = JsonRef.replace_refs(cfg)
    return cfg


# Read template
def get_template(tpl_path: str) -> Template:
    dir_name = os.path.dirname(tpl_path)
    file_name = os.path.basename(tpl_path)
    tpl_list = TemplateLookup(directories=[dir_name], output_encoding="utf-8")
    tpl = tpl_list.get_template(file_name)
    return tpl


# Generate file
def gen_file(cfg, tpl, out_file) -> None:
    # Writing file
    with open(out_file, "w") as f:
        f.write(str(tpl.render_unicode(cfg=cfg)))
    return


# For template generation
def gen_ca90_hier_base(cfg, tpl_path, out_file):
    tpl = get_template(tpl_path)
    gen_file(cfg, tpl, out_file)

    return


"""
    Functions for simulations
"""


async def clock_and_time(clock):
    await RisingEdge(clock)
    await Timer(1, "ps")


# Check results
def check_result(actual_val, golden_val, debug_on=False):
    if debug_on:
        cocotb.log.info(f"Golden val: {golden_val}; Actual val: {actual_val}")
    assert (
        golden_val == actual_val
    ), f"Error! Golden Val: {golden_val}; Actual Val: {actual_val}"
    return


def check_result_array(actual_val_array, golden_val_array, debug_on=False):
    if debug_on:
        for i in range(len(golden_val_array)):
            cocotb.log.info(
                f"Golden val: {golden_val_array[i]}; Actual val: {actual_val_array[i]}"
            )
    assert (
        golden_val_array == actual_val_array
    ).any(), f"Error! Golden Val: {golden_val_array}; Actual Val: {actual_val_array}"
    return


"""
    Set of functions for data generation
"""


# For generating random bits
def gen_rand_bits(dimension):
    return random.getrandbits(dimension)


# For generating random integer
def gen_randint(max_val):
    return random.randint(0, int(max_val))


# For the ALU output
def hv_alu_out(A, B, shift_amt, hv_dim, op):
    mask_val = 2**hv_dim - 1

    if op == 1:
        result = A & B
    elif op == 2:
        result = A | B
    elif op == 3:
        result = (A >> shift_amt) | (A << (hv_dim - shift_amt)) & mask_val
    else:
        result = A ^ B
    return result


# Convert a number in binary to a list
# Used to feed each bundler unit
def numbin2list(numbin, dim):
    # Convert binary inputs first
    bin_hv = np.array(list(map(int, format(numbin, f"0{dim}b"))))
    return bin_hv


# Convert a number in binary to a list
# Used to feed each bundler unit
def numbip2list(numbin, dim):
    # Convert binary inputs first
    bin_hv = np.array(list(map(int, format(numbin, f"0{dim}b"))))
    # Get marks that have 0s
    mask = bin_hv == 0
    # Convert 0s to -1s
    bin_hv[mask] = -1
    return bin_hv


# Convert from list to binary value
def hvlist2num(hv_list):
    # Bring back into an integer itself!
    # Sad workaround is to convert to str
    # The convert to integer
    hv_num = "".join(hv_list.astype(str))
    hv_num = int(hv_num, 2)

    return hv_num


"""
    Set of functions for the encoding module
"""


# Clear encoder signal inputs to 0
def clear_encode_inputs_no_clock(dut):
    # Item memory inputs
    dut.im_rd_a_i.value = 0
    dut.im_rd_b_i.value = 0

    # Control ports for ALU
    dut.alu_mux_a_i.value = 0
    dut.alu_mux_b_i.value = 0
    dut.alu_ops_i.value = 0
    dut.alu_shift_amt_i.value = 0

    # Control ports for bundlers
    dut.bund_mux_a_i.value = 0
    dut.bund_mux_b_i.value = 0
    dut.bund_valid_a_i.value = 0
    dut.bund_valid_b_i.value = 0
    dut.bund_clr_a_i.value = 0
    dut.bund_clr_b_i.value = 0

    # Control ports for registers
    dut.reg_mux_i.value = 0
    dut.reg_rd_addr_a_i.value = 0
    dut.reg_rd_addr_b_i.value = 0
    dut.reg_wr_addr_i.value = 0
    dut.reg_wr_en_i.value = 0

    # Control ports for query HV
    dut.qhv_clr_i.value = 0
    dut.qhv_wen_i.value = 0
    dut.qhv_mux_i.value = 0

    return


# Loading from Im to register
async def load_im_to_reg(dut, hv_data, reg_addr):
    # Make sure to clear first
    clear_encode_inputs_no_clock(dut)

    # Item memory inputs
    dut.im_rd_a_i.value = hv_data

    # Control ports for registers
    dut.reg_mux_i.value = 1
    dut.reg_wr_addr_i.value = reg_addr
    dut.reg_wr_en_i.value = 1

    # Wait clock
    await clock_and_time(dut.clk_i)

    # Make sure to clear
    clear_encode_inputs_no_clock(dut)

    return


# Loading data unto register
async def load_reg_to_qhv(dut, reg_addr):
    # Make sure to clear first
    clear_encode_inputs_no_clock(dut)

    # Control ports for registers
    dut.reg_rd_addr_a_i.value = reg_addr

    # Control ports for query HV
    dut.qhv_wen_i.value = 1
    dut.qhv_mux_i.value = 1

    # Wait clock
    await clock_and_time(dut.clk_i)

    # Make sure to clear
    clear_encode_inputs_no_clock(dut)

    return


# Permute element and load to query HV
async def perm_reg_to_qhv(dut, reg_addr, shift_amt):
    # Make sure to clear first
    clear_encode_inputs_no_clock(dut)

    # Control ports for registers
    dut.reg_rd_addr_a_i.value = reg_addr

    # Control ports for ALU
    dut.alu_mux_a_i.value = 1
    dut.alu_ops_i.value = 3
    dut.alu_shift_amt_i.value = shift_amt

    # Control ports for query HV
    dut.qhv_wen_i.value = 1
    dut.qhv_mux_i.value = 0

    # Wait clock
    await clock_and_time(dut.clk_i)

    # Make sure to clear
    clear_encode_inputs_no_clock(dut)

    return


# Bind 2 IM inputs and save to reg
async def bind_2im_to_reg(dut, hv_a, hv_b, reg_addr):
    # Make sure to clear
    clear_encode_inputs_no_clock(dut)

    # Item memory inputs
    dut.im_rd_a_i.value = hv_a
    dut.im_rd_b_i.value = hv_b

    # Control ports for ALU
    dut.alu_mux_a_i.value = 0
    dut.alu_mux_b_i.value = 0
    dut.alu_ops_i.value = 0

    # Control ports for registers
    dut.reg_mux_i.value = 0
    dut.reg_wr_addr_i.value = reg_addr
    dut.reg_wr_en_i.value = 1

    # Wait clock
    await clock_and_time(dut.clk_i)

    # Make sure to clear
    clear_encode_inputs_no_clock(dut)

    return


# Bind 2 reg inputs and save to reg
async def bind_2reg_to_reg(dut, reg_addr_a, reg_addr_b, reg_wr_addr):
    # Make sure to clear
    clear_encode_inputs_no_clock(dut)

    # Control ports for ALU
    dut.alu_mux_a_i.value = 1
    dut.alu_mux_b_i.value = 1
    dut.alu_ops_i.value = 0

    # Control ports for registers
    dut.reg_mux_i.value = 0
    dut.reg_rd_addr_a_i.value = reg_addr_a
    dut.reg_rd_addr_b_i.value = reg_addr_b
    dut.reg_wr_addr_i.value = reg_wr_addr
    dut.reg_wr_en_i.value = 1

    # Wait clock
    await clock_and_time(dut.clk_i)

    # Make sure to clear
    clear_encode_inputs_no_clock(dut)

    return


# Load bundler from IM
async def im_to_bundler(dut, hv_data, bundler_addr):
    # Make sure to clear first
    clear_encode_inputs_no_clock(dut)

    # Item memory inputs
    dut.im_rd_a_i.value = hv_data

    # Control ports for bundlers
    if bundler_addr == 0:
        dut.bund_mux_a_i.value = 2
        dut.bund_valid_a_i.value = 1
    else:
        dut.bund_mux_b_i.value = 2
        dut.bund_valid_b_i.value = 1

    # Wait clock
    await clock_and_time(dut.clk_i)

    # Make sure to clear first
    clear_encode_inputs_no_clock(dut)
    return


# Load reg to bundler
async def load_reg_to_bundler(dut, bundler_addr, reg_addr):
    # Make sure to clear first
    clear_encode_inputs_no_clock(dut)

    # Control ports for registers
    dut.reg_rd_addr_a_i.value = reg_addr

    # Control ports for bundlers
    if bundler_addr == 0:
        dut.bund_mux_a_i.value = 3
        dut.bund_valid_a_i.value = 1
    else:
        dut.bund_mux_b_i.value = 3
        dut.bund_valid_b_i.value = 1

    # Wait clock
    await clock_and_time(dut.clk_i)

    # Make sure to clear first
    clear_encode_inputs_no_clock(dut)
    return


# Load bundler to reg
async def load_bundler_to_reg(dut, bundler_addr, reg_addr):
    # Make sure to clear first
    clear_encode_inputs_no_clock(dut)

    # Control ports for registers
    if bundler_addr == 0:
        dut.reg_mux_i.value = 2
    else:
        dut.reg_mux_i.value = 3

    dut.reg_wr_addr_i.value = reg_addr
    dut.reg_wr_en_i.value = 1

    # Wait clock
    await clock_and_time(dut.clk_i)

    # Make sure to clear first
    clear_encode_inputs_no_clock(dut)
    return


# Load bundler to query HV
async def load_bundler_to_qhv(dut, bundler_addr):
    # Make sure to clear first
    clear_encode_inputs_no_clock(dut)

    # Control ports for bundlers
    if bundler_addr == 0:
        dut.qhv_mux_i.value = 2
    else:
        dut.qhv_mux_i.value = 3

    dut.qhv_wen_i.value = 1

    # Wait clock
    await clock_and_time(dut.clk_i)

    # Make sure to clear first
    clear_encode_inputs_no_clock(dut)
    return
