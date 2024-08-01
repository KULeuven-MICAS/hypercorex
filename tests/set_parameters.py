"""
  Copyright 2024 KU Leuven
  Ryan Antonio <ryan.antonio@esat.kuleuven.be>

  Description:
  This contains the parameters used across all tests.
"""

import math

# Test Parameters
TEST_RUNS = 50
NUM_CLASSES = 10

# Working dimensions
HV_DIM = 256
REG_FILE_WIDTH = 32
SEED_DIM = REG_FILE_WIDTH

# Item memory parameters
NUM_TOT_IM = 256
NUM_PER_IM_BANK = int(HV_DIM // 4)
NUM_IM_SETS = int(NUM_TOT_IM // NUM_PER_IM_BANK)
CA90_MODE = "ca90_hier"
IM_FIFO_DEPTH = 2

# Instruction memory parameters
INST_MEM_WIDTH = REG_FILE_WIDTH
INST_MEM_DEPTH = 128
INST_MEM_ADDR_WIDTH = int(math.log2(INST_MEM_DEPTH))
HOLD_FIFO_DEPTH = 4

# Encoder parameters
BUNDLER_COUNT_WIDTH = 8
BUNDLER_MUX_WIDTH = 2
ALU_MUX_WIDTH = 2
ALU_MAX_SHIFT = 4
REG_MUX_WIDTH = 2
QHV_MUX_WIDTH = 2
REG_NUM = 4

# Shift amount needs to be in odd number form
# because the shifts is from 0 to some dimension
# here, we restrict shift amount to be half of the total dimension
MAX_SHIFT_AMT = 4

# ---------------------------
# Register addressing
# ---------------------------

# CORE Settings
CORE_SET_REG_ADDR = 0

# AM Settings
AM_NUM_PREDICT_REG_ADDR = 1
AM_PREDICT_REG_ADDR = 2

# Instruction controls
INST_CTRL_REG_ADDR = 3
INST_WRITE_ADDR_REG_ADDR = 4
INST_WRITE_DATA_REG_ADDR = 5
INST_RDDBG_ADDR_REG_ADDR = 6
INST_PC_ADDR_REG_ADDR = 7
INST_INST_AT_ADDR_ADDR_REG_ADDR = 8

# Instruction loop control
INST_LOOP_CTRL_REG_ADDR = 9
INST_LOOP_JUMP_ADDR_REG_ADDR = 10
INST_LOOP_END_ADDR_REG_ADDR = 11
INST_LOOP_COUNT_REG_ADDR = 12

# IM seeds
CIM_SEED_REG_ADDR = 13
IM_BASE_SEED_REG_ADDR = 14


# ---------------------------
# Complete filelist
# ---------------------------
HYPERCOREX_FILELIST = [
    # ----------------------------
    # Common
    # ----------------------------
    # Level 0
    "/rtl/common/mux.sv",
    "/rtl/common/fifo.sv",
    "/rtl/common/reg_file_1w1r.sv",
    "/rtl/common/reg_file_1w2r.sv",
    # ----------------------------
    # Encoder
    # ----------------------------
    # Level 0
    "/rtl/encoder/hv_alu_pe.sv",
    "/rtl/encoder/bundler_unit.sv",
    "/rtl/encoder/qhv.sv",
    # Level 1
    "/rtl/encoder/bundler_set.sv",
    # Level 2
    "/rtl/encoder/hv_encoder.sv",
    # ----------------------------
    # Associative memory
    # ----------------------------
    # Level 0
    "/rtl/assoc_memory/ham_dist.sv",
    # Level 1
    "/rtl/assoc_memory/assoc_mem.sv",
    # ----------------------------
    # CSR
    # ----------------------------
    # Level 0
    "/rtl/csr/csr_addr_pkg.sv",
    # Level 1
    "/rtl/csr/csr.sv",
    # ----------------------------
    # Instruction memory
    # ----------------------------
    # Level 0
    "/rtl/inst_memory/hypercorex_inst_pkg.sv",
    "/rtl/inst_memory/inst_loop_control.sv",
    # Level 1
    "/rtl/inst_memory/inst_decode.sv",
    "/rtl/inst_memory/inst_control.sv",
    # ----------------------------
    # Item memory
    # ----------------------------
    # Level 0
    "/rtl/item_memory/ca90_unit.sv",
    "/rtl/item_memory/cim_bit_flip.sv",
    # Level 1
    "/rtl/item_memory/ca90_hier_base.sv",
    "/rtl/item_memory/cim.sv",
    # Level 2
    "/rtl/item_memory/ca90_item_memory.sv",
    # Level 3
    "/rtl/item_memory/item_memory.sv",
    # Level 4
    "/rtl/item_memory/item_memory_top.sv",
    # ----------------------------
    # Hypercorex top
    # ----------------------------
    "/rtl/hypercorex_top.sv",
]

TB_HYPERCOREX_FILELIST = [
    # ----------------------------
    # Testbench
    # ----------------------------
    # Level 0
    "/rtl/tb/tb_rd_memory.sv",
    "/rtl/tb/tb_wr_memory.sv",
    # Level 1
    "/rtl/tb/tb_hypercorex.sv",
]
