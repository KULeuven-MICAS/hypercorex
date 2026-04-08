"""
================================
VSAX Item Memory Generator
================================

This library consists of the functions to help in hypervector
and item memory generation. There are various ways to generate 
hypervectors ranging from random indexing, CA90, and LFSR.
It also includes analysis tools to evaluate the quality of 
the generated item memory.

"""

# ---------------------------------------------------------------------------
# Importing packages
# ---------------------------------------------------------------------------
import numpy as np


# ---------------------------------------------------------------------------
# Hypervector generation functions
# ---------------------------------------------------------------------------


# Generating empty hypervector (all zeros)
def gen_empty_hv(hv_dim: int) -> np.ndarray:
    return np.zeros(hv_dim, dtype=float)


# Generate using random indexing style
def gen_ri_hv(hv_dim: int, p_dense: float, hv_type: str = "binary") -> np.ndarray:
    # Generate a list of random integers
    random_list = np.arange(hv_dim)

    # Permute list
    np.random.shuffle(random_list)

    # Determine threshold
    threshold = np.floor(hv_dim * p_dense)

    # Binarize depending on hv_type
    if hv_type == "bipolar":
        random_list = np.where(random_list >= threshold, 1, -1)
    else:
        random_list = np.where(random_list >= threshold, 1, 0)

    return random_list


if __name__ == "__main__":
    # Example usage
    HV_DIM = 1024
    P_DENSE = 0.1
    HV_TYPE = "binary"

    hv = gen_ri_hv(HV_DIM, P_DENSE, HV_TYPE)
    print(f"Generated random-index HV: {hv}")
