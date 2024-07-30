"""
  Copyright 2024 KU Leuven
  Ryan Antonio <ryan.antonio@esat.kuleuven.be>

  Description:
  This contains the parameters used across all tests.
"""

import math

# Test Parameters
TEST_RUNS = 20
NUM_CLASSES = 10

# Working dimensions
HV_DIM = 256
SEED_DIM = 64
REG_FILE_WIDTH = 32

# Item memory parameters
NUM_TOT_IM = 256
NUM_PER_IM_BANK = int(HV_DIM // 4)
CA90_MODE = "ca90_hier"

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
