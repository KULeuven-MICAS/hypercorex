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
HV_DIM = 16
BUNDLER_COUNT_WIDTH = 8
REG_FILE_WIDTH = 32


# Shift amount needs to be in odd number form
# because the shifts is from 0 to some dimension
# here, we restrict shift amount to be half of the total dimension
MAX_SHIFT_AMT = HV_DIM / 2 - 1
