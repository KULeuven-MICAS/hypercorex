"""
  Copyright 2024 KU Leuven
  Ryan Antonio <ryan.antonio@esat.kuleuven.be>

  Description:
  This contains the parameters used across all tests.
"""

# Test Parameters
TEST_RUNS = 20
NUM_CLASSES = 10

# Working dimensions
HV_DIM = 256
REG_FILE_WIDTH = 32

# Encoder parameters
BUNDLER_COUNT_WIDTH = 8
BUNDLER_MUX_WIDTH = 2
ALU_MUX_WIDTH = 2
ALU_OPS_WIDTH = 2
ALU_MAX_SHIFT = HV_DIM/2
REG_MUX_WIDTH = 2
QHV_MUX_WIDTH = 2
REG_NUM = 4

# Shift amount needs to be in odd number form
# because the shifts is from 0 to some dimension
# here, we restrict shift amount to be half of the total dimension
MAX_SHIFT_AMT = HV_DIM / 2 - 1
