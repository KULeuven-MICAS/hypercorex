#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
  Copyright 2024 KU Leuven
  Ryan Antonio <ryan.antonio@esat.kuleuven.be>

  Description:
  This is the main compiler for the hypercorex
  it takes in assembly fromat like texts
  then converts them into binary files
"""

import os

"""
Some parameters
"""
TYPE_LEN = 3
FUNC_LEN = 21


"""
    Functions
"""


# Simple read function and returns the text
# into a list that can be used for decoding
# each line is stripped and split
def read_asm(filepath):
    asm_lines = []
    with open(filepath, "r") as file:
        for line in file:
            asm_lines.append(line.strip().split())

    return asm_lines


# Convert a number in binary to a list
# Used to feed each bundler unit
def num2list(numbin, dim):
    # Convert binary inputs first if it is string
    # also take only the last number
    if isinstance(numbin, str):
        number = int(numbin[-1])
    else:
        number = numbin
    bin_hv = list(map(int, format(number, f"0{dim}b")))
    return bin_hv


# Combining list of integers into a string
def list2str(input_list):
    combine_list = "".join([str(i) for i in input_list])
    return combine_list


# Main instruction decode function it returns
# both the control code for sanity checking
# and the equiavalent instruction code
# Both are in lists for clarity
def decode_inst(asm_line, sanity_check=False, convert_str=False, print_ctrl=False):
    # asm_line always expects that
    # the first argument is the instruction
    # the succeeding are other arguments
    asm_inst = asm_line[0]

    # Initial default values
    # This is for the final output
    inst_code = 0
    control_code = 0

    # Type and function
    inst_type = num2list(0, TYPE_LEN)
    func_type = num2list(0, FUNC_LEN)

    # Contorl ports for IM
    im_a_pop = [0]
    im_b_pop = [0]

    # Control ports for ALU
    alu_mux_a = [0, 0]
    alu_mux_b = [0, 0]
    alu_ops = [0, 0, 0]
    alu_shift_amt = [0, 0]

    # Control ports for bundlers
    bund_mux_a = [0, 0]
    bund_mux_b = [0, 0]
    bund_valid_a = [0]
    bund_valid_b = [0]
    bund_clr_a = [0]
    bund_clr_b = [0]

    # Control ports for register ops
    reg_mux = [0, 0]
    reg_rd_addr_a = [0, 0]
    reg_rd_addr_b = [0, 0]
    reg_wr_addr = [0, 0]
    reg_wr_en = [0]

    # Control ports for query HV
    qhv_clr = [0]
    qhv_wen = [0]
    qhv_mux = [0, 0]

    # AM module search
    am_search = [0]
    am_load = [0]

    # -----------------------------------
    # Main decoder of setting values
    # -----------------------------------

    # IM
    if asm_inst == "ima_reg":
        inst_type = num2list(0, TYPE_LEN)
        func_type = num2list(1, FUNC_LEN)
        im_a_pop = [1]
        alu_mux_a = [0, 0]
        reg_mux = [0, 0]
        reg_wr_en = [1]
        alu_ops = [0, 0, 1]
        reg_wr_addr = num2list(asm_line[1], 2)
    elif asm_inst == "imb_reg":
        inst_type = num2list(0, TYPE_LEN)
        func_type = num2list(2, FUNC_LEN)
        im_b_pop = [1]
        alu_mux_b = [0, 0]
        reg_mux = [0, 0]
        reg_wr_en = [1]
        alu_ops = [0, 1, 0]
        reg_wr_addr = num2list(asm_line[1], 2)
    elif asm_inst == "imab_bind_reg":
        inst_type = num2list(0, TYPE_LEN)
        func_type = num2list(3, FUNC_LEN)
        im_a_pop = [1]
        im_b_pop = [1]
        alu_mux_a = [0, 0]
        alu_mux_b = [0, 0]
        reg_mux = [0, 0]
        reg_wr_en = [1]
        alu_ops = [0, 0, 0]
        reg_wr_addr = num2list(asm_line[1], 2)
    elif asm_inst == "ima_perm_r_reg":
        inst_type = num2list(0, TYPE_LEN)
        func_type = num2list(4, FUNC_LEN)
        im_a_pop = [1]
        alu_mux_a = [0, 0]
        reg_mux = [0, 0]
        reg_wr_en = [1]
        alu_ops = [0, 1, 1]
        reg_wr_addr = num2list(asm_line[1], 2)
        alu_shift_amt = num2list(asm_line[2], 2)
    elif asm_inst == "ima_perm_l_reg":
        inst_type = num2list(0, TYPE_LEN)
        func_type = num2list(5, FUNC_LEN)
        im_a_pop = [1]
        alu_mux_a = [0, 0]
        reg_mux = [0, 0]
        reg_wr_en = [1]
        alu_ops = [1, 0, 0]
        reg_wr_addr = num2list(asm_line[1], 2)
        alu_shift_amt = num2list(asm_line[2], 2)
    # IM-REG
    elif asm_inst == "ima_regb_bind_reg":
        inst_type = num2list(1, TYPE_LEN)
        func_type = num2list(1, FUNC_LEN)
        im_a_pop = [1]
        alu_mux_a = [0, 0]
        alu_mux_b = [0, 1]
        reg_mux = [0, 0]
        reg_wr_en = [1]
        alu_ops = [0, 0, 0]
        reg_wr_addr = num2list(asm_line[1], 2)
        reg_rd_addr_b = num2list(asm_line[2], 2)
    elif asm_inst == "imb_rega_bind_reg":
        inst_type = num2list(1, TYPE_LEN)
        func_type = num2list(2, FUNC_LEN)
        im_b_pop = [1]
        alu_mux_a = [0, 1]
        alu_mux_b = [0, 0]
        reg_mux = [0, 0]
        reg_wr_en = [1]
        alu_ops = [0, 0, 0]
        reg_wr_addr = num2list(asm_line[1], 2)
        reg_rd_addr_a = num2list(asm_line[2], 2)
    # IM-BUND
    elif asm_inst == "ima_bunda":
        inst_type = num2list(2, TYPE_LEN)
        func_type = num2list(1, FUNC_LEN)
        im_a_pop = [1]
        bund_mux_a = [1, 0]
        bund_valid_a = [1]
    elif asm_inst == "ima_bundb":
        inst_type = num2list(2, TYPE_LEN)
        func_type = num2list(2, FUNC_LEN)
        im_a_pop = [1]
        bund_mux_b = [1, 0]
        bund_valid_b = [1]
    elif asm_inst == "imab_bind_bunda":
        inst_type = num2list(2, TYPE_LEN)
        func_type = num2list(3, FUNC_LEN)
        im_a_pop = [1]
        im_b_pop = [1]
        alu_mux_a = [0, 0]
        alu_mux_b = [0, 0]
        bund_mux_a = [0, 0]
        bund_valid_a = [1]
        alu_ops = [0, 0, 0]
    elif asm_inst == "imab_bind_bundb":
        inst_type = num2list(2, TYPE_LEN)
        func_type = num2list(4, FUNC_LEN)
        im_a_pop = [1]
        im_b_pop = [1]
        alu_mux_a = [0, 0]
        alu_mux_b = [0, 0]
        bund_mux_b = [0, 0]
        bund_valid_b = [1]
        alu_ops = [0, 0, 0]
    elif asm_inst == "ima_perm_r_bunda":
        inst_type = num2list(2, TYPE_LEN)
        func_type = num2list(5, FUNC_LEN)
        im_a_pop = [1]
        alu_mux_a = [0, 0]
        bund_mux_a = [0, 0]
        bund_valid_a = [1]
        alu_ops = [0, 1, 1]
        alu_shift_amt = num2list(asm_line[1], 2)
    elif asm_inst == "ima_perm_r_bundb":
        inst_type = num2list(2, TYPE_LEN)
        func_type = num2list(6, FUNC_LEN)
        im_a_pop = [1]
        alu_mux_a = [0, 0]
        bund_mux_b = [0, 0]
        bund_valid_b = [1]
        alu_ops = [0, 1, 1]
        alu_shift_amt = num2list(asm_line[1], 2)
    elif asm_inst == "ima_perm_l_bunda":
        inst_type = num2list(2, TYPE_LEN)
        func_type = num2list(7, FUNC_LEN)
        im_a_pop = [1]
        alu_mux_a = [0, 0]
        bund_mux_a = [0, 0]
        bund_valid_a = [1]
        alu_ops = [1, 0, 0]
        alu_shift_amt = num2list(asm_line[1], 2)
    elif asm_inst == "ima_perm_l_bundb":
        inst_type = num2list(2, TYPE_LEN)
        func_type = num2list(8, FUNC_LEN)
        im_a_pop = [1]
        alu_mux_a = [0, 0]
        bund_mux_b = [0, 0]
        bund_valid_b = [1]
        alu_ops = [1, 0, 0]
        alu_shift_amt = num2list(asm_line[1], 2)
    # REG
    elif asm_inst == "regab_bind_reg":
        inst_type = num2list(3, TYPE_LEN)
        func_type = num2list(1, FUNC_LEN)
        alu_mux_a = [0, 1]
        alu_mux_b = [0, 1]
        reg_mux = [0, 0]
        reg_wr_en = [1]
        alu_ops = [0, 0, 0]
        reg_wr_addr = num2list(asm_line[1], 2)
        reg_rd_addr_a = num2list(asm_line[2], 2)
        reg_rd_addr_b = num2list(asm_line[3], 2)
    elif asm_inst == "rega_perm_r_reg":
        inst_type = num2list(3, TYPE_LEN)
        func_type = num2list(2, FUNC_LEN)
        alu_mux_a = [0, 1]
        reg_mux = [0, 0]
        reg_wr_en = [1]
        alu_ops = [0, 1, 1]
        reg_wr_addr = num2list(asm_line[1], 2)
        reg_rd_addr_a = num2list(asm_line[2], 2)
        alu_shift_amt = num2list(asm_line[3], 2)
    elif asm_inst == "rega_perm_l_reg":
        inst_type = num2list(3, TYPE_LEN)
        func_type = num2list(3, FUNC_LEN)
        alu_mux_a = [0, 1]
        reg_mux = [0, 0]
        reg_wr_en = [1]
        alu_ops = [1, 0, 0]
        reg_wr_addr = num2list(asm_line[1], 2)
        reg_rd_addr_a = num2list(asm_line[2], 2)
        alu_shift_amt = num2list(asm_line[3], 2)
    elif asm_inst == "mv_reg":
        inst_type = num2list(3, TYPE_LEN)
        func_type = num2list(4, FUNC_LEN)
        alu_mux_a = [0, 1]
        reg_mux = [0, 0]
        reg_wr_en = [1]
        alu_ops = [0, 0, 1]
        reg_wr_addr = num2list(asm_line[1], 2)
        reg_rd_addr_a = num2list(asm_line[2], 2)
    # REG-BUND
    elif asm_inst == "regab_bind_bunda":
        inst_type = num2list(4, TYPE_LEN)
        func_type = num2list(1, FUNC_LEN)
        alu_mux_a = [0, 1]
        alu_mux_b = [0, 1]
        bund_mux_a = [0, 0]
        bund_valid_a = [1]
        alu_ops = [0, 0, 0]
        reg_rd_addr_a = num2list(asm_line[1], 2)
        reg_rd_addr_b = num2list(asm_line[2], 2)
    elif asm_inst == "regab_bind_bundb":
        inst_type = num2list(4, TYPE_LEN)
        func_type = num2list(2, FUNC_LEN)
        alu_mux_a = [0, 1]
        alu_mux_b = [0, 1]
        bund_mux_b = [0, 0]
        bund_valid_b = [1]
        alu_ops = [0, 0, 0]
        reg_rd_addr_a = num2list(asm_line[1], 2)
        reg_rd_addr_b = num2list(asm_line[2], 2)
    elif asm_inst == "rega_perm_r_bunda":
        inst_type = num2list(4, TYPE_LEN)
        func_type = num2list(3, FUNC_LEN)
        alu_mux_a = [0, 1]
        bund_mux_a = [0, 0]
        bund_valid_a = [1]
        alu_ops = [0, 1, 1]
        reg_rd_addr_a = num2list(asm_line[1], 2)
        alu_shift_amt = num2list(asm_line[2], 2)
    elif asm_inst == "rega_perm_r_bundb":
        inst_type = num2list(4, TYPE_LEN)
        func_type = num2list(4, FUNC_LEN)
        alu_mux_a = [0, 1]
        bund_mux_b = [0, 0]
        bund_valid_b = [1]
        alu_ops = [0, 1, 1]
        reg_rd_addr_a = num2list(asm_line[1], 2)
        alu_shift_amt = num2list(asm_line[2], 2)
    elif asm_inst == "rega_perm_l_bunda":
        inst_type = num2list(4, TYPE_LEN)
        func_type = num2list(5, FUNC_LEN)
        alu_mux_a = [0, 1]
        bund_mux_a = [0, 0]
        bund_valid_a = [1]
        alu_ops = [1, 0, 0]
        reg_rd_addr_a = num2list(asm_line[1], 2)
        alu_shift_amt = num2list(asm_line[2], 2)
    elif asm_inst == "rega_perm_l_bundb":
        inst_type = num2list(4, TYPE_LEN)
        func_type = num2list(6, FUNC_LEN)
        alu_mux_a = [0, 1]
        bund_mux_b = [0, 0]
        bund_valid_b = [1]
        alu_ops = [1, 0, 0]
        reg_rd_addr_a = num2list(asm_line[1], 2)
        alu_shift_amt = num2list(asm_line[2], 2)
    elif asm_inst == "rega_bunda_bind_reg":
        inst_type = num2list(4, TYPE_LEN)
        func_type = num2list(7, FUNC_LEN)
        alu_mux_a = [0, 1]
        alu_mux_b = [1, 0]
        reg_mux = [0, 0]
        reg_wr_en = [1]
        alu_ops = [0, 0, 0]
        reg_wr_addr = num2list(asm_line[1], 2)
        reg_rd_addr_a = num2list(asm_line[2], 2)
    elif asm_inst == "rega_bundb_bind_reg":
        inst_type = num2list(4, TYPE_LEN)
        func_type = num2list(8, FUNC_LEN)
        alu_mux_a = [0, 1]
        alu_mux_b = [1, 1]
        reg_mux = [0, 0]
        reg_wr_en = [1]
        alu_ops = [0, 0, 0]
        reg_wr_addr = num2list(asm_line[1], 2)
        reg_rd_addr_a = num2list(asm_line[2], 2)
    elif asm_inst == "bunda_perm_r_reg":
        inst_type = num2list(4, TYPE_LEN)
        func_type = num2list(9, FUNC_LEN)
        alu_mux_a = [1, 0]
        reg_mux = [0, 0]
        reg_wr_en = [1]
        alu_ops = [0, 1, 1]
        reg_wr_addr = num2list(asm_line[1], 2)
        alu_shift_amt = num2list(asm_line[2], 2)
    elif asm_inst == "bundb_perm_r_reg":
        inst_type = num2list(4, TYPE_LEN)
        func_type = num2list(10, FUNC_LEN)
        alu_mux_a = [1, 1]
        reg_mux = [0, 0]
        reg_wr_en = [1]
        alu_ops = [0, 1, 1]
        reg_wr_addr = num2list(asm_line[1], 2)
        alu_shift_amt = num2list(asm_line[2], 2)
    elif asm_inst == "bunda_perm_l_reg":
        inst_type = num2list(4, TYPE_LEN)
        func_type = num2list(11, FUNC_LEN)
        alu_mux_a = [1, 0]
        reg_mux = [0, 0]
        reg_wr_en = [1]
        alu_ops = [1, 0, 0]
        reg_wr_addr = num2list(asm_line[1], 2)
        alu_shift_amt = num2list(asm_line[2], 2)
    elif asm_inst == "bundb_perm_l_reg":
        inst_type = num2list(4, TYPE_LEN)
        func_type = num2list(12, FUNC_LEN)
        alu_mux_a = [1, 1]
        reg_mux = [0, 0]
        reg_wr_en = [1]
        alu_ops = [1, 0, 0]
        reg_wr_addr = num2list(asm_line[1], 2)
        alu_shift_amt = num2list(asm_line[2], 2)
    elif asm_inst == "mv_bunda_reg":
        inst_type = num2list(4, TYPE_LEN)
        func_type = num2list(13, FUNC_LEN)
        reg_mux = [1, 0]
        reg_wr_en = [1]
        reg_wr_addr = num2list(asm_line[1], 2)
    elif asm_inst == "mv_bundb_reg":
        inst_type = num2list(4, TYPE_LEN)
        func_type = num2list(14, FUNC_LEN)
        reg_mux = [1, 1]
        reg_wr_en = [1]
        reg_wr_addr = num2list(asm_line[1], 2)
    elif asm_inst == "mv_reg_bunda":
        inst_type = num2list(4, TYPE_LEN)
        func_type = num2list(15, FUNC_LEN)
        bund_mux_a = [1, 1]
        bund_valid_a = [1]
        reg_rd_addr_a = num2list(asm_line[1], 2)
    elif asm_inst == "mv_reg_bundb":
        inst_type = num2list(4, TYPE_LEN)
        func_type = num2list(16, FUNC_LEN)
        bund_mux_b = [1, 1]
        bund_valid_b = [1]
        reg_rd_addr_a = num2list(asm_line[1], 2)
    # BUND
    elif asm_inst == "mv_bunda_bundb":
        inst_type = num2list(5, TYPE_LEN)
        func_type = num2list(1, FUNC_LEN)
        bund_mux_b = [0, 1]
        bund_valid_b = [1]
    elif asm_inst == "mv_bundb_bunda":
        inst_type = num2list(5, TYPE_LEN)
        func_type = num2list(2, FUNC_LEN)
        bund_mux_a = [0, 1]
        bund_valid_a = [1]
    elif asm_inst == "clr_bunda":
        inst_type = num2list(5, TYPE_LEN)
        func_type = num2list(3, FUNC_LEN)
        bund_clr_a = [1]
    elif asm_inst == "clr_bundb":
        inst_type = num2list(5, TYPE_LEN)
        func_type = num2list(4, FUNC_LEN)
        bund_clr_b = [1]
    # QHV
    elif asm_inst == "mv_reg_qhv":
        inst_type = num2list(6, TYPE_LEN)
        func_type = num2list(1, FUNC_LEN)
        qhv_mux = [0, 1]
        qhv_wen = [1]
    elif asm_inst == "mv_bunda_qhv":
        inst_type = num2list(6, TYPE_LEN)
        func_type = num2list(2, FUNC_LEN)
        qhv_mux = [1, 0]
        qhv_wen = [1]
    elif asm_inst == "mv_bundb_qhv":
        inst_type = num2list(6, TYPE_LEN)
        func_type = num2list(3, FUNC_LEN)
        qhv_mux = [1, 1]
        qhv_wen = [1]
    elif asm_inst == "clr_qhv":
        inst_type = num2list(6, TYPE_LEN)
        func_type = num2list(4, FUNC_LEN)
        qhv_clr = [1]
    elif asm_inst == "am_search":
        inst_type = num2list(7, TYPE_LEN)
        func_type = num2list(1, FUNC_LEN)
        am_search = [1]
    elif asm_inst == "am_load":
        inst_type = num2list(7, TYPE_LEN)
        func_type = num2list(2, FUNC_LEN)
        am_load = [1]
    else:
        raise ValueError(f"Instruction incorrect {asm_line}")

    # Instruction code
    inst_code = (
        func_type
        + inst_type
        + alu_shift_amt
        + reg_wr_addr
        + reg_rd_addr_a
        + reg_rd_addr_b
    )

    # For debug purposes
    if print_ctrl:
        print(" ------------------ Golden Values ------------------ ")
        print(f"im_a_pop: {im_a_pop}")
        print(f"im_b_pop: {im_b_pop}")
        print(f"alu_mux_a: {alu_mux_a}")
        print(f"alu_mux_b: {alu_mux_b}")
        print(f"alu_ops: {alu_ops}")
        print(f"alu_shift_amt: {alu_shift_amt}")
        print(f"bund_mux_a: {bund_mux_a}")
        print(f"bund_mux_b: {bund_mux_b}")
        print(f"bund_valid_a: {bund_valid_a}")
        print(f"bund_valid_b: {bund_valid_b}")
        print(f"bund_clr_a: {bund_clr_a}")
        print(f"bund_clr_b: {bund_clr_b}")
        print(f"reg_mux: {reg_mux}")
        print(f"reg_rd_addr_a: {reg_rd_addr_a}")
        print(f"reg_rd_addr_b: {reg_rd_addr_b}")
        print(f"reg_wr_addr: {reg_wr_addr}")
        print(f"reg_wr_en: {reg_wr_en}")
        print(f"qhv_clr: {qhv_clr}")
        print(f"qhv_wen: {qhv_wen}")
        print(f"qhv_mux: {qhv_mux}")
        print(f"am_search: {am_search}")
        print(f"am_load: {am_load}")

    # Control code
    control_code = (
        im_a_pop
        + im_b_pop
        + alu_mux_a
        + alu_mux_b
        + alu_ops
        + alu_shift_amt
        + bund_mux_a
        + bund_mux_b
        + bund_valid_a
        + bund_valid_b
        + bund_clr_a
        + bund_clr_b
        + reg_mux
        + reg_rd_addr_a
        + reg_rd_addr_b
        + reg_wr_addr
        + reg_wr_en
        + qhv_clr
        + qhv_wen
        + qhv_mux
        + am_search
        + am_load
    )

    # Static sanity checking
    if sanity_check:
        if len(inst_code) != 32:
            raise ValueError("Instruction code is not 32 bits long. Double check.")
        if len(control_code) != 33:
            raise ValueError("Instruction code is not 33 bits long. Double check.")

    if convert_str:
        inst_code = list2str(inst_code)
        control_code = list2str(control_code)

    # Packing of the values into binary code
    return inst_code, control_code


# Compile assembly
def compile_hypercorex_asm(filepath):
    asm_lines = read_asm(filepath)

    inst_code_list = []
    control_code_list = []

    for i in range(len(asm_lines)):
        inst_code, control_code = decode_inst(asm_lines[i])
        inst_code_list.append(inst_code)
        control_code_list.append(control_code)

    return inst_code_list, control_code_list


if __name__ == "__main__":
    current_directory = os.path.dirname(os.path.abspath(__file__))
    filepath = current_directory + "/asm/train_char_recog.asm"

    inst_code_list, control_code_list = compile_hypercorex_asm(filepath)

    print("Done compiling ASM files!")
