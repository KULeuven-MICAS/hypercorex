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
import random
import numpy as np
from typing import Optional

# ---------------------------------------------------------------------------
# Fixed parameters
# ---------------------------------------------------------------------------
LFSR_MASK_32 = 0xFFFF_FFFF  # keep 32-bit arithmetic in Python ints
LFSR_TAP_MASK = 0xB4BC_D35C  # primitive polynomial — maximal-length 32-bit LFSR
LFSR_KNUTH_CONST = 0x9E37_79B9  # floor(2^32 / φ) — Knuth multiplicative hash
LFSR_WARMUP_STEPS = 32  # warm-up iterations inside lfsr_item_seed


# ---------------------------------------------------------------------------
# Auxiliary functions
# ---------------------------------------------------------------------------
# Random flipping of bits in a hypervector
def hv_rand_flip(
    hv: np.ndarray, start_flips: int, end_flips: int, hv_type: str = "binary"
) -> np.ndarray:
    """
    Randomly flip bits in a hypervector.

    Parameters:
        hv (np.ndarray): The hypervector to flip bits in.
        start_flips (int): The starting index for flipping.
        end_flips (int): The ending index for flipping.
        hv_type (str): The type of hypervector. Can be 'bipolar'

    Returns:
        np.ndarray: The hypervector with flipped bits.
    """
    if hv_type == "bipolar":
        hv[start_flips:end_flips] *= -1
    else:
        hv[start_flips:end_flips] ^= 1
    return hv


# Prediction from an existing class AM and an encoded hypervector
def hv_prediction_idx(
    class_am: np.ndarray, encoded_hv: np.ndarray, hv_type: str = "bipolar"
) -> int:
    """
    Predict the index of the class that is most similar to the encoded hypervector.

    Parameters:
        class_am (np.ndarray): The class associative memory containing class HVs.
        encoded_hv (np.ndarray): The encoded HV to be compared against the class AM.
        hv_type (str): The type of hypervector ("binary" or "bipolar").
    Returns:
        int: The index of the predicted class.
    """
    score_list = []
    for i in range(len(class_am)):
        score_list.append(hv_norm_dist(class_am[i], encoded_hv, hv_type=hv_type))

    predict_idx = np.argmax(score_list)

    return predict_idx


# ---------------------------------------------------------------------------
# Hypervector generation functions
# ---------------------------------------------------------------------------


# Generating empty hypervector (all zeros)
def hv_gen_empty(hv_dim: int) -> np.ndarray:
    """
    Generate an empty hypervector of the specified dimension.

    Parameters:
        hv_dim (int): The dimension of the hypervector.
    Returns:
        np.ndarray: An empty hypervector of zeros.
    """
    return np.zeros(hv_dim)


# Generate using random indexing style
def hv_gen_ri(hv_dim: int, p_dense: float, hv_type: str = "binary") -> np.ndarray:
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


# This one is used for LFSR-based generation
# First is the LFSR state generation
def lfsr_next(state: int) -> int:
    """
    One step of a 32-bit Galois LFSR.

    Parameters:
        state (int): The current state of the LFSR.
    Returns:
        int: The next state of the LFSR.
    """
    feedback = state & 1
    state = (state >> 1) & LFSR_MASK_32
    if feedback:
        state ^= LFSR_TAP_MASK
    return state


# For generating initial seed in LFSR
def lfsr_item_seed(base_seed: int, idx: int) -> int:
    """
    Derive a unique, well-dispersed starting state for item idx.

    1. Multiply idx by the Knuth constant → scatter across 32-bit space.
    2. XOR with base_seed  → user-controlled variation.
    3. 32 LFSR warm-up steps → thoroughly mix all seed bits.

    Parameters:
        base_seed (int): The base seed for generating the item seed.
        idx (int): The index of the item for which to generate the seed.
    Returns:
        int: A unique, well-dispersed starting state for the item.
    """
    state = (
        base_seed ^ (((idx & LFSR_MASK_32) * LFSR_KNUTH_CONST) & LFSR_MASK_32)
    ) & LFSR_MASK_32
    for _ in range(LFSR_WARMUP_STEPS):
        state = lfsr_next(state)
    return state


# Fopr generating the hypervector using LFSR
def hv_gen_lfsr(
    base_seed: int, idx: int, hv_dim: int, hv_type: str = "binary"
) -> np.ndarray:
    """
    Generate one hypervector as a numpy array.

    Clocks the LFSR hv_dim times, collecting the LSB each step into
    a pre-allocated uint8 array.

    Parameters:
        base_seed (int): The base seed for generating the hypervector.
        idx (int): The index of the item for which to generate the hypervector.
        hv_dim (int): The dimension of the hypervector to be generated.
    Returns:
        np.ndarray: A hypervector generated using LFSR.
    """
    state = lfsr_item_seed(base_seed, idx)
    bits = np.empty(hv_dim, dtype=np.int32)
    for i in range(hv_dim):
        # collect LSB
        bits[i] = state & 1
        state = lfsr_next(state)
    bits = np.flip(bits)
    if hv_type == "bipolar":
        bits = np.where(bits == 0, -1, 1)
    return bits


# ---------------------------------------------------------------------------
# Hypervector item memory generation functions
# ---------------------------------------------------------------------------


# Generating empty memories
def hv_gen_empty_mem(num_hv: int, hv_dim: int) -> np.ndarray:
    """
    Generate an empty hypervector memory.

    Parameters:
        num_hv (int): The number of hypervectors.
        hv_dim (int): The dimension of each hypervector.
    Returns:
        np.ndarray: An empty hypervector memory.
    """
    return np.zeros((num_hv, hv_dim))


# Generating orthogonal item memory
def hv_gen_orthogonal_im(
    num_items: int = 128,
    hv_size: int = 1024,
    hv_type: str = "bipolar",
    gen_type="ri",
    gen_ri_p_dense: float = 0.5,
    gen_lfsr_base_seed: int = 42,
):
    """
    Generate an item memory with orthogonal hypervectors.

    Parameters:
        num_items (int): The number of items in the item memory.
        hv_size (int): The size of each hypervector.
        hv_type (str): The type of hypervector.
        Can be 'bipolar', 'binary', 'real', or 'complex'.

    Returns:
        np.ndarray: The generated item memory.
    """
    if gen_type == "lfsr":
        im = np.array(
            [
                hv_gen_lfsr(gen_lfsr_base_seed, idx, hv_size, hv_type)
                for idx in range(num_items)
            ]
        )
    else:
        im = np.array(
            [hv_gen_ri(hv_size, gen_ri_p_dense, hv_type) for _ in range(num_items)]
        )
    return im


# Generating continuous item memory
def hv_gen_continuous_im(
    num_items=21,
    hv_size=1024,
    cim_max_is_ortho=True,
    hv_type="bipolar",
):
    """
    Generate a continuous item memory (CIM).

    Parameters:
        num_items (int): The number of items in the CIM.
        hv_size (int): The size of each hypervector.
        cim_max_is_ortho (bool): If True, the maximum distance
                                 between hypervectors is orthogonal.
        hv_type (str): The type of hypervector. Can be 'bipolar' or 'binary'.

    Returns:
        np.ndarray: The generated continuous item memory.
    """
    # First initialize some seed HV
    # Calculate % number of flips
    if cim_max_is_ortho:
        num_flips = (hv_size // 2) // (num_items - 1)
    else:
        num_flips = hv_size // (num_items - 1)

    # Initialize empty matrix
    cim = hv_gen_empty_mem(num_items, hv_size)

    # Generate first seed HV
    cim[0] = hv_gen_ri(hv_size, p_dense=0.5, hv_type=hv_type)

    # Iteratively generate other HVs
    for i in range(num_items - 1):
        cim[i + 1] = hv_rand_flip(
            cim[i], i * num_flips, (i + 1) * num_flips, hv_type=hv_type
        )
    return cim


# ---------------------------------------------------------------------------
# Hypervector general functions
# ---------------------------------------------------------------------------


# Binding dense functions
def hv_bind(hv_a: np.ndarray, hv_b: np.ndarray, hv_type: str = "binary") -> np.ndarray:
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
def hv_circ_perm(hv_a: np.ndarray, permute_amt: int) -> np.ndarray:
    """
    Perform a circular permutation on the hypervector.

    Parameters:
        hv_a (np.ndarray): The input hypervector to be permuted.
        permute_amt (int): The amount by which to circularly permute the hypervector.
    Returns:
        np.ndarray: The circularly permuted hypervector.
    """
    return np.roll(hv_a, permute_amt)


# Binarize hypervector
def hv_binarize(
    hv_a: np.ndarray, threshold: float, hv_type: str = "binary"
) -> np.ndarray:
    """
    Binarize a hypervector based on a threshold.

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
def hv_norm_dist(
    hv_a: np.ndarray,
    hv_b: np.ndarray,
    hv_type: str = "bipolar",
    quant_type: Optional[str] = None,
) -> float:
    """
    Calculate the normalized distance between two hypervectors.

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


# ---------------------------------------------------------------------------
# Hypervector profiling functions
# ---------------------------------------------------------------------------
def profile_im_density(im: np.ndarray) -> float:
    """
    Calculate the density of a hypervector.

    Parameters:
        im (np.ndarray): The input hypervector.
    Returns:
        float: The density of the hypervector.
    """
    return np.mean(im)


def profile_im_pairwise_dist(im: np.ndarray, hv_type: str = "binary") -> np.ndarray:
    """
    Calculate the pairwise distances between hypervectors in an item memory.

    Parameters:
        im (np.ndarray): The input item memory containing multiple hypervectors.
        hv_type (str): The type of the hypervectors ("binary" or "bipolar").
    Returns:
        np.ndarray: A matrix of pairwise distances between the hypervectors.
    """
    num_items = im.shape[0]
    distances = np.zeros((num_items, num_items))
    for i in range(num_items):
        for j in range(num_items):
            distances[i, j] = hv_norm_dist(im[i], im[j], hv_type)
    return distances


# ---------------------------------------------------------------------------
# Hypervector sanity checkers
# ---------------------------------------------------------------------------
def checker_im_density(im: np.ndarray, hv_type: str, threshold: float) -> bool:
    """
    Check if the density of a hypervector is within a
    specified threshold of an expected value.

    Parameters:
        im (np.ndarray): The input hypervector to be checked.
        hv_type (str): The type of the hypervector ("binary" or "bipolar").
        threshold (float): The acceptable deviation from the expected density.
    Returns:
        bool: True if the density is within the threshold, False otherwise.
    """
    if hv_type == "binary":
        expected_density = 0.5
    elif hv_type == "bipolar":
        expected_density = 0
    else:
        raise ValueError(f"Unsupported hypervector type: {hv_type}")

    actual_density = profile_im_density(im)

    if np.allclose(actual_density, expected_density, atol=threshold):
        print(f"Pass! Density {actual_density}")
    else:
        raise AssertionError(
            f"Error! Density {actual_density} \
                             not within {expected_density} +/- {threshold}"
        )
    return True


def checker_im_pairwise_dist(im: np.ndarray, hv_type: str, threshold: float) -> bool:
    """
    Check if the pairwise distances between hypervectors in an item memory
    are within a specified threshold of expected values.

    Parameters:
        im (np.ndarray): The input item memory containing multiple hypervectors.
        hv_type (str): The type of the hypervectors ("binary" or "bipolar").
        threshold (float): The acceptable deviation from the expected distance.
    Returns:
        bool: True if all pairwise distances are within the threshold, False otherwise.
    """
    distances = profile_im_pairwise_dist(im, hv_type)
    num_items = im.shape[0]
    mask = ~np.eye(num_items, dtype=bool)
    off_diag_distances = distances[mask]

    if hv_type == "binary":
        expected_distance = 0.5
    elif hv_type == "bipolar":
        expected_distance = 0
    else:
        raise ValueError(f"Unsupported hypervector type: {hv_type}")

    if np.all(
        (off_diag_distances >= expected_distance - threshold)
        & (off_diag_distances <= expected_distance + threshold)
    ):
        print("Pass! Pairwise distance check")
    else:
        raise AssertionError(
            f"Error! Pairwise distances not within \
                             {expected_distance} +/- {threshold}"
        )
    return True


if __name__ == "__main__":
    # Example usage
    HV_DIM = 2048
    P_DENSE = 0.5
    THRESHOLD = 0.1
    NUM_ITEMS = 10

    # Printing the parameters
    print("======== Parameters ========")
    print(f"HV_DIM: {HV_DIM}")
    print(f"P_DENSE: {P_DENSE}")
    print(f"THRESHOLD: {THRESHOLD}")
    print(f"NUM_ITEMS: {NUM_ITEMS}")

    # ---------------------------
    # Binary HV check
    # ---------------------------
    print("======== Tests ========")
    print("======== Binary RI HV Tests ========")
    HV_TYPE = "binary"
    # Generate a set of random hypervectors
    random_index_set = hv_gen_orthogonal_im(
        num_items=NUM_ITEMS,
        hv_size=HV_DIM,
        hv_type=HV_TYPE,
        gen_type="ri",
        gen_ri_p_dense=P_DENSE,
    )

    # Get density of each hypervector
    checker_im_density(random_index_set, hv_type=HV_TYPE, threshold=THRESHOLD)

    # Get pair-wise distances between the hypervectors
    distances = profile_im_pairwise_dist(random_index_set, hv_type=HV_TYPE)

    # Check non-diagonal distances
    checker_im_pairwise_dist(random_index_set, hv_type=HV_TYPE, threshold=THRESHOLD)

    # ---------------------------
    # Bipolar HV check
    # ---------------------------
    print("======== Bipolar RI HV Tests ========")
    HV_TYPE = "bipolar"

    # Generate a set of random hypervectors
    random_index_set = hv_gen_orthogonal_im(
        num_items=NUM_ITEMS,
        hv_size=HV_DIM,
        hv_type=HV_TYPE,
        gen_type="ri",
        gen_ri_p_dense=P_DENSE,
    )

    # Get density of each hypervector
    checker_im_density(random_index_set, hv_type=HV_TYPE, threshold=THRESHOLD)

    # Get pair-wise distances between the hypervectors
    checker_im_pairwise_dist(random_index_set, hv_type=HV_TYPE, threshold=THRESHOLD)

    # ---------------------------
    # Binary LFSR HV check
    # ---------------------------
    print("======== Binary LFSR HV Tests ========")

    HV_TYPE = "binary"
    BASE_SEED = random.getrandbits(32)

    # Generate a set of random hypervectors
    lfsr_set = hv_gen_orthogonal_im(
        num_items=NUM_ITEMS,
        hv_size=HV_DIM,
        hv_type=HV_TYPE,
        gen_type="lfsr",
        gen_lfsr_base_seed=BASE_SEED,
    )

    # Get density of each hypervector
    checker_im_density(lfsr_set, hv_type=HV_TYPE, threshold=THRESHOLD)

    # Get pair-wise distances between the hypervectors
    checker_im_pairwise_dist(lfsr_set, hv_type=HV_TYPE, threshold=THRESHOLD)

    # ---------------------------
    # Bipolar LFSR HV check
    # ---------------------------
    print("======== Bipolar LFSR HV Tests ========")

    HV_TYPE = "bipolar"
    BASE_SEED = random.getrandbits(32)

    # Generate a set of random hypervectors
    lfsr_set = hv_gen_orthogonal_im(
        num_items=NUM_ITEMS,
        hv_size=HV_DIM,
        hv_type=HV_TYPE,
        gen_type="lfsr",
        gen_lfsr_base_seed=BASE_SEED,
    )

    # Get density of each hypervector
    checker_im_density(lfsr_set, hv_type=HV_TYPE, threshold=THRESHOLD)

    # Get pair-wise distances between the hypervectors
    checker_im_pairwise_dist(lfsr_set, hv_type=HV_TYPE, threshold=THRESHOLD)

    # ---------------------------
    # Generating CiM
    # ---------------------------
    print("======== CiM Tests ========")
    HV_TYPE = "bipolar"
    NUM_ITEMS = 21
    # Generate a continuous item memory
    cim_set = hv_gen_continuous_im(
        num_items=NUM_ITEMS,
        hv_size=HV_DIM,
        cim_max_is_ortho=False,
        hv_type=HV_TYPE,
    )

    # Get pair-wise distances between the hypervectors
    cim_distances = profile_im_pairwise_dist(cim_set, hv_type=HV_TYPE)
    # Just manual inspection to see if it is working
    print("Pairwise distances of 1st CiM HV:")
    print(cim_distances[0])
