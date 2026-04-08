"""
================================
VSAX General Functions
================================

This library consists of the functions for general VSA operations such as:
binding, bundling, permutations, and similarity measures.

"""

# ---------------------------------------------------------------------------
# Importing packages
# ---------------------------------------------------------------------------
import numpy as np
from typing import Optional


# ---------------------------------------------------------------------------
# Hypervector general functions
# ---------------------------------------------------------------------------


# Binding dense functions
def bind_hv(hv_a: np.ndarray, hv_b: np.ndarray, hv_type: str = "binary") -> np.ndarray:
    # If bipolar we do multiplication
    # otherwise we do bit-wise XOR
    if hv_type == "bipolar":
        return np.multiply(hv_a, hv_b)
    else:
        return np.bitwise_xor(hv_a, hv_b)


# Circular permutations
def circ_perm_hv(hv_a: np.ndarray, permute_amt: int) -> np.ndarray:
    return np.roll(hv_a, permute_amt)


# Binarize hypervector
def binarize_hv(
    hv_a: np.ndarray, threshold: float, hv_type: str = "binary"
) -> np.ndarray:
    # Binarize depending on hv_type
    # If it's binary use a threshold for this
    if hv_type == "bipolar":
        hv_a = np.where(hv_a >= 0, 1, -1)
    else:
        hv_a = np.where(hv_a >= threshold, 1, 0)

    return hv_a


# Normalized distance calculation
# the output range is from 0 to 1
# where 1 is the highest similarity
def norm_dist_hv(
    hv_a: np.ndarray,
    hv_b: np.ndarray,
    hv_type: str = "binary",
    quant_type: Optional[str] = None,
) -> float:
    # If binary we do hamming distance,
    # else we do cosine similarity
    if (hv_type == "bipolar") or (quant_type is not None):
        hv_dot = np.dot(hv_a, hv_b)
        norm_a = np.linalg.norm(hv_a)
        norm_b = np.linalg.norm(hv_b)
        if (norm_a == 0) or (norm_b == 0):
            norm_factor = 1
        else:
            norm_factor = norm_a * norm_b
        dist = hv_dot / (norm_factor)
    else:
        ham_dist = np.sum(np.bitwise_xor(hv_a, hv_b))
        dist = 1 - (ham_dist / hv_a.size)

    return dist
