"""
================================
VSAX General Functions
================================

This library consists of the functions for general VSA operations such as:
binding, bundling, permutations, and similarity measures.
We also include the item memory or hypervector generation in here.

"""

# ---------------------------------------------------------------------------
# Importing packages
# ---------------------------------------------------------------------------
import numpy as np
from typing import Optional

# ---------------------------------------------------------------------------
# Hypervector generation functions
# ---------------------------------------------------------------------------


# Generating empty hypervector (all zeros)
def gen_empty_hv(hv_dim: int) -> np.ndarray:
    """
    Generate an empty hypervector of the specified dimension.
    Parameters:
        hv_dim (int): The dimension of the hypervector.
    Returns:
        np.ndarray: An empty hypervector of zeros.
    """
    return np.zeros(hv_dim, dtype=float)


# Generate using random indexing style
def gen_ri_hv(hv_dim: int, p_dense: float, hv_type: str = "binary") -> np.ndarray:
    """
    Generate a hypervector using random indexing style.
    Parameters:
        hv_dim (int): The dimension of the hypervector.
        p_dense (float): The density of the hypervector.
        hv_type (str): The type of the hypervector ("binary" or "bipolar").
    Returns:
        np.ndarray: A hypervector generated using random indexing.
    """
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


# ---------------------------------------------------------------------------
# Hypervector item memory generation functions
# ---------------------------------------------------------------------------


# Generating empty memories
def gen_empty_mem_hv(num_hv: int, hv_dim: int) -> np.ndarray:
    """
    Generate an empty hypervector memory.
    Parameters:
        num_hv (int): The number of hypervectors.
        hv_dim (int): The dimension of each hypervector.
    Returns:
        np.ndarray: An empty hypervector memory.
    """
    return np.zeros((num_hv, hv_dim), dtype=int)


# ---------------------------------------------------------------------------
# Hypervector general functions
# ---------------------------------------------------------------------------


# Binding dense functions
def bind_hv(hv_a: np.ndarray, hv_b: np.ndarray, hv_type: str = "binary") -> np.ndarray:
    """
    Bind two hypervectors together.
    Parameters:
        hv_a (np.ndarray): The first hypervector.
        hv_b (np.ndarray): The second hypervector.
        hv_type (str): The type of the hypervector ("binary" or "bipolar").
    Returns:
        np.ndarray: The bound hypervector.
    """
    # If bipolar we do multiplication
    # otherwise we do bit-wise XOR
    if hv_type == "bipolar":
        return np.multiply(hv_a, hv_b)
    else:
        return np.bitwise_xor(hv_a, hv_b)


# Circular permutations
def circ_perm_hv(hv_a: np.ndarray, permute_amt: int) -> np.ndarray:
    """Perform a circular permutation on the hypervector.
    Parameters:
        hv_a (np.ndarray): The input hypervector to be permuted.
        permute_amt (int): The amount by which to circularly permute the hypervector.
    Returns:
        np.ndarray: The circularly permuted hypervector.
    """
    return np.roll(hv_a, permute_amt)


# Binarize hypervector
def binarize_hv(
    hv_a: np.ndarray, threshold: float, hv_type: str = "binary"
) -> np.ndarray:
    """Binarize a hypervector based on a threshold.
    Parameters:
        hv_a (np.ndarray): The input hypervector to be binarized.
        threshold (float): The threshold for binarization.
        hv_type (str): The type of the hypervector ("binary" or "bipolar").
    Returns:
        np.ndarray: The binarized hypervector.
    """
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
    """Calculate the normalized distance between two hypervectors.
    Parameters:
        hv_a (np.ndarray): The first hypervector.
        hv_b (np.ndarray): The second hypervector.
        hv_type (str): The type of the hypervector ("binary" or "bipolar").
        quant_type (Optional[str]): The type of quantization used, if any.
    Returns:
        float: The normalized distance between the
        two hypervectors, ranging from 0 to 1.
    """
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


if __name__ == "__main__":
    # Example usage
    HV_DIM = 2048
    P_DENSE = 0.5
    HV_TYPE = "binary"
    NUM_ITEMS = 10

    # Generate a set of random hypervectors
    random_index_set = np.array(
        [gen_ri_hv(HV_DIM, P_DENSE, HV_TYPE) for _ in range(NUM_ITEMS)]
    )

    # Get density of each hypervector
    ri_density = np.mean(random_index_set, axis=1)
    print("RI Density:", ri_density)

    # Get pair-wise distances between the hypervectors
    distances = np.zeros((NUM_ITEMS, NUM_ITEMS))
    for i in range(NUM_ITEMS):
        for j in range(NUM_ITEMS):
            distances[i, j] = norm_dist_hv(
                random_index_set[i], random_index_set[j], HV_TYPE
            )
    print("RI pair-distances:\n", distances)
