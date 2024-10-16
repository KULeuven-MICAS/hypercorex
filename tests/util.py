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
from mako.template import Template
from mako.lookup import TemplateLookup
from cocotb_test.simulator import run
from cocotb.triggers import Timer, RisingEdge
import numpy as np
import subprocess

"""
    Set of functions for test setups
"""


# For getting the root of the repository
def get_root():
    return os.getcwd()


# For getting directory of the file
def get_dir():
    # Get the absolute path of the current script
    script_path = os.path.abspath(__file__)
    # Get the directory of the script
    script_dir = os.path.dirname(script_path)
    return script_dir


# Extracting filelist from Bender
def get_bender_filelist(bender_path):
    # Run bender to get the filelist
    os.chdir(bender_path)
    terminal_out = subprocess.run(
        ["bender", "script", "flist", "-t", "hypercorex", "-t", "tb_hypercorex"],
        capture_output=True,
        text=True,
    )
    filelist = terminal_out.stdout
    return filelist.strip().split("\n")


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
    bender_filelist=False,
):
    # Extract global main root
    git_repo_root = get_root()

    # Set tests path, we use this by default
    tests_path = git_repo_root + "/tests"

    # Set the simulation build within test directory
    sim_build = tests_path + "/sim_build/{}/".format(toplevel)

    # Append git repo root for all items
    # If using bender filelist no need to append
    if not bender_filelist:
        for i in range(len(verilog_sources)):
            verilog_sources[i] = git_repo_root + verilog_sources[i]

    # Setting of compilation arguments
    # and timescale depending on simulator
    if simulator == "verilator":
        compile_args = [
            "-Wno-WIDTH",
            "-Wno-PINMISSING",
            "--no-timing",
            "--trace-structs",
            "--unroll-count",
            "1024",
        ]
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
    ).all(), f"Error! Golden Val: {golden_val_array}; Actual Val: {actual_val_array}"
    return


def check_result_list(actual_val_array, golden_val_array, debug_on=False):
    if debug_on:
        for i in range(len(golden_val_array)):
            cocotb.log.info(
                f"Golden val: {golden_val_array[i]}; Actual val: {actual_val_array[i]}"
            )
    assert (
        golden_val_array == actual_val_array
    ), f"Error! Golden Val: {golden_val_array}; Actual Val: {actual_val_array}"
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
def hv_alu_out(hv_a, hv_b, shift_amt, hv_dim, op):
    mask_val = 2**hv_dim - 1

    if op == 1:
        result = hv_a
    elif op == 2:
        result = hv_b
    elif op == 3:
        # Workaround because github CI fails
        # At shifting more than 64 bits
        if isinstance(hv_a, np.ndarray):
            result = np.roll(hv_a, shift_amt)
        else:
            result = (hv_a >> shift_amt) | (hv_a << (hv_dim - shift_amt)) & mask_val
    else:
        result = hv_a ^ hv_b
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

    # Global stall signal
    dut.global_stall_i.value = 0

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
    dut.qhv_am_load_i.value = 0
    dut.qhv_ready_i.value = 0

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


"""
    Functions for testbench memory control
"""


# Clearing the testbench inputs
def clear_tb_inputs(dut):
    # Exclude hard settings in here

    # ---------------------
    # CSR ports
    # ---------------------
    # Request
    dut.csr_req_data_i.value = 0
    dut.csr_req_addr_i.value = 0
    dut.csr_req_write_i.value = 0
    dut.csr_req_valid_i.value = 0

    # ---------------------
    # IM ports
    # ---------------------
    dut.im_a_lowdim_wr_addr_i.value = 0
    dut.im_a_lowdim_wr_data_i.value = 0
    dut.im_a_lowdim_wr_en_i.value = 0
    dut.im_a_lowdim_rd_addr_i.value = 0

    dut.im_a_highdim_wr_addr_i.value = 0
    dut.im_a_highdim_wr_data_i.value = 0
    dut.im_a_highdim_wr_en_i.value = 0
    dut.im_a_highdim_rd_addr_i.value = 0

    dut.im_b_lowdim_wr_addr_i.value = 0
    dut.im_b_lowdim_wr_data_i.value = 0
    dut.im_b_lowdim_wr_en_i.value = 0
    dut.im_b_lowdim_rd_addr_i.value = 0

    dut.im_b_highdim_wr_addr_i.value = 0
    dut.im_b_highdim_wr_data_i.value = 0
    dut.im_b_highdim_wr_en_i.value = 0
    dut.im_b_highdim_rd_addr_i.value = 0

    # ---------------------
    # AM ports
    # ---------------------
    dut.am_wr_addr_i.value = 0
    dut.am_wr_data_i.value = 0
    dut.am_wr_en_i.value = 0
    dut.am_rd_addr_i.value = 0

    # ---------------------
    # QHV ports
    # ---------------------
    dut.qhv_rd_addr_i.value = 0

    # ---------------------
    # AM predict ports
    # ---------------------
    dut.predict_rd_addr_i.value = 0

    return


# To load unto low dimensional block
# choosable between A and B
async def load_im_lowdim(dut, im_data, im_addr, im_sel="A"):
    if im_sel == "A":
        dut.im_a_lowdim_wr_addr_i.value = im_addr
        dut.im_a_lowdim_wr_data_i.value = im_data
        dut.im_a_lowdim_wr_en_i.value = 1
    else:
        dut.im_b_lowdim_wr_addr_i.value = im_addr
        dut.im_b_lowdim_wr_data_i.value = im_data
        dut.im_b_lowdim_wr_en_i.value = 1

    # Wait for one cycle
    await clock_and_time(dut.clk_i)

    clear_tb_inputs(dut)
    return


# Loading to high dimensional block
# choosable between A and B
async def load_im_highdim(dut, im_data, im_addr, im_sel="A"):
    if im_sel == "A":
        dut.im_a_highdim_wr_addr_i.value = im_addr
        dut.im_a_highdim_wr_data_i.value = im_data
        dut.im_a_highdim_wr_en_i.value = 1
    else:
        dut.im_b_highdim_wr_addr_i.value = im_addr
        dut.im_b_highdim_wr_data_i.value = im_data
        dut.im_b_highdim_wr_en_i.value = 1

    # Wait for one cycle
    await clock_and_time(dut.clk_i)

    clear_tb_inputs(dut)
    return


# Loading to the associative memory
async def load_am(dut, am_data, am_addr):
    dut.am_wr_addr_i.value = am_addr
    dut.am_wr_data_i.value = am_data
    dut.am_wr_en_i.value = 1

    # Wait for one cycle
    await clock_and_time(dut.clk_i)

    clear_tb_inputs(dut)
    return


# Reading data from lowdim ports
# choosable between A and B
async def read_im_lowdim(dut, im_addr, im_sel="A"):
    if im_sel == "A":
        dut.im_a_lowdim_rd_addr_i.value = im_addr
    else:
        dut.im_b_lowdim_rd_addr_i.value = im_addr

    # Wait for one cycle
    await clock_and_time(dut.clk_i)

    # Extract data
    if im_sel == "A":
        data_val = dut.im_a_lowdim_rd_data_o.value.integer
    else:
        data_val = dut.im_b_lowdim_rd_data_o.value.integer

    clear_tb_inputs(dut)
    return data_val


# Reading data from highdim ports
# choosable between A and B
async def read_im_highdim(dut, im_addr, im_sel="A"):
    if im_sel == "A":
        dut.im_a_highdim_rd_addr_i.value = im_addr
    else:
        dut.im_b_highdim_rd_addr_i.value = im_addr

    # Wait for one cycle
    await clock_and_time(dut.clk_i)

    # Extract data
    if im_sel == "A":
        data_val = dut.im_a_highdim_rd_data_o.value.integer
    else:
        data_val = dut.im_b_highdim_rd_data_o.value.integer

    clear_tb_inputs(dut)
    return data_val


# Reading data from the associative memory
async def read_am(dut, am_addr):
    dut.am_rd_addr_i.value = am_addr

    # Wait for one cycle
    await clock_and_time(dut.clk_i)

    # Extract data
    data_val = dut.am_rd_data_o.value.integer

    clear_tb_inputs(dut)
    return data_val


# Loading a list of data into the low or high dimensional block
# Selectable between the two modes and the two blocks
async def load_im_list(dut, im_data_list, im_start_addr, im_sel="A", im_dim="low"):
    for i, im_data in enumerate(im_data_list):
        if im_dim == "low":
            await load_im_lowdim(dut, im_data, im_start_addr + i, im_sel)
        else:
            await load_im_highdim(dut, im_data, im_start_addr + i, im_sel)
    return


# Loading a list of data into the associative memory
async def load_am_list(dut, am_data_list, am_start_addr):
    for i, am_data in enumerate(am_data_list):
        await load_am(dut, am_data, am_start_addr + i)
    return


# Reading a list of data from the low or high dimensional block
# Selectable between the two modes and the two blocks
# Given the size to be read
async def read_im_list(dut, im_start_addr, im_size, im_sel="A", im_dim="low"):
    im_data_list = []
    for i in range(im_size):
        if im_dim == "low":
            im_data_list.append(await read_im_lowdim(dut, im_start_addr + i, im_sel))
        else:
            im_data_list.append(await read_im_highdim(dut, im_start_addr + i, im_sel))
    return im_data_list


# Reading a list of data from the associative memory
# Given the size to be read
async def read_am_list(dut, am_start_addr, am_size):
    am_data_list = []
    for i in range(am_size):
        am_data_list.append(await read_am(dut, am_start_addr + i))
    return am_data_list


# Read from QHV memory
async def read_qhv(dut, qhv_addr):
    dut.qhv_rd_addr_i.value = qhv_addr

    # Wait for one cycle
    await clock_and_time(dut.clk_i)

    # Extract data
    qhv_data = dut.qhv_rd_data_o.value.integer

    clear_tb_inputs(dut)
    return qhv_data


# Read from predict memory
async def read_predict(dut, predict_addr):
    dut.predict_rd_addr_i.value = predict_addr

    # Wait for one cycle
    await clock_and_time(dut.clk_i)

    # Extract data
    predict_data = dut.predict_rd_data_o.value.integer

    clear_tb_inputs(dut)
    return predict_data


"""
    Functions for CSR control
"""


# Clear CSR signals
def clear_csr_req_no_clock(dut):
    dut.csr_req_addr_i.value = 0
    dut.csr_req_data_i.value = 0
    dut.csr_req_write_i.value = 0
    dut.csr_req_valid_i.value = 0
    return


# Writes to csr registers of the hypercorex
async def write_csr(dut, addr, data):
    dut.csr_req_addr_i.value = addr
    dut.csr_req_data_i.value = data
    dut.csr_req_write_i.value = 1
    dut.csr_req_valid_i.value = 1
    await clock_and_time(dut.clk_i)
    clear_csr_req_no_clock(dut)
    return


# Reads from csr registers of the hypercorex
async def read_csr(dut, addr):
    dut.csr_req_addr_i.value = addr
    dut.csr_req_data_i.value = 0
    dut.csr_req_write_i.value = 0
    dut.csr_req_valid_i.value = 1
    # Propagate time to get combinationally
    await Timer(1, units="ps")
    read_csr_data = dut.csr_rsp_data_o.value.integer
    # Propagate time to finish task
    await clock_and_time(dut.clk_i)
    clear_csr_req_no_clock(dut)
    # Set this to high just in case the next cylce
    # needs to clear or flush the fifo
    dut.csr_rsp_ready_i.value = 1
    return read_csr_data


"""
    Functions for Instruction Loop control
"""


# For writing the instruction loop parameters
async def config_inst_ctrl(dut, reg_addr, val1, val2, val3, data_width):
    data = val1 + (val2 << data_width) + (val3 << 2 * data_width)
    await write_csr(dut, reg_addr, data)

    return data
