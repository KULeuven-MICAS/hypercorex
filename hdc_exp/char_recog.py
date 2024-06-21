#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
  Copyright 2024 KU Leuven
  Ryan Antonio <ryan.antonio@esat.kuleuven.be>

  Description:
  These program demonstrates how to use the
  character recognition example for HDC
"""

from hdc_util import (
    gen_empty_hv,
    gen_orthogonal_im,
    circ_perm_hv,
    binarize_hv,
    extract_dataset,
    measure_acc,
    prediction_set,
)
from tqdm import tqdm
import numpy as np


"""
    Some base parameters:
        NUM_CLASSES - 26 classes from A to Z
        IMG_ROW_NUM - number of pixel rows, default is 7
        IMG_COL_NUM - number of pixel cols, default is 5
        HV_DIM - hypervector dimensions
        THRESHOLD - threshold for bunlding
"""

# Characteristics of data set
NUM_CLASSSES = 26
IMG_ROW_NUM = 7
IMG_COL_NUM = 5
IMG_PIXEL_NUM = IMG_ROW_NUM * IMG_COL_NUM

# Characteristics of HV
HV_TYPE = "binary"
HV_DIM = 128
P_DENSE = 0.5
THRESHOLD = np.floor(IMG_ROW_NUM * IMG_COL_NUM / 2)

# Test parameters
TEST_RUNS = 50


"""
    Other useful useful functions for this test only
"""


# This test randomly distorts some pixels
# of the original data set for resilience measurement
def distort_inputs(orig_dataset, num_distort, img_len):
    distorted_dataset = []

    # Get random indices to flip
    for i in range(len(orig_dataset)):
        rand_idx = np.arange(img_len)
        np.random.shuffle(rand_idx)

        # Copy the original data set first
        temp_set = orig_dataset[i].copy()

        # Iterate through different
        # character indices
        for j in range(len(rand_idx)):
            # Only flip parts that need flipping
            if rand_idx[j] < num_distort:
                if temp_set[j] == 1:
                    temp_set[j] = 0
                else:
                    temp_set[j] = 1

        # Add to the list for the distorted data set
        distorted_dataset.append(temp_set)

    return distorted_dataset


"""
    Character recognition flow:
        1. First generate static item memory
        2. For each character do:
            - get 1 pixel <-> HV association
            - if white permute once, else do nothing
            - bundle all pixel-loc-value HVs
        3. Test by computing similarity searches
        
    This work will do this by encoding, testing, and training tasks
"""


# Encoding every character first
# The output is a binarized encoded hypervector
def encode_character(hv_dim, ortho_im, character_input, threshold, hv_type="binary"):
    # Initialize empty character hypervector
    char_hv = gen_empty_hv(hv_dim)

    # Cycle through every pixel
    for i in range(len(character_input)):
        if character_input[i] == 1:
            char_hv += circ_perm_hv(ortho_im[i], 1)
        else:
            char_hv += ortho_im[i]

    # Binarize the bundled HV
    char_hv = binarize_hv(char_hv, threshold, hv_type)

    return char_hv


# Main function to run the character recognition program
if __name__ == "__main__":
    # Get original data set
    file_path = "./data_set/char_recog/characters.txt"
    dataset = extract_dataset(file_path)

    # Minor data clean to make the data a list
    # of binary numbers instead of characters
    for i in range(len(dataset)):
        dataset[i] = np.array(list(map(int, list(dataset[i]))))

    # Correct answer set (this is fixed for char recog)
    correct_set = list(range(NUM_CLASSSES))

    # Generate base hypervectors
    ortho_im = gen_orthogonal_im(
        num_hv=IMG_PIXEL_NUM, hv_dim=HV_DIM, p_dense=P_DENSE, hv_type=HV_TYPE
    )

    # Encode the characters into AM
    # This is the training part
    assoc_mem = []
    for i in range(len(dataset)):
        assoc_mem.append(
            encode_character(HV_DIM, ortho_im, dataset[i], THRESHOLD, hv_type=HV_TYPE)
        )

    # This is the testing part
    # Test for different distortions
    max_distort = 10
    avg_acc = np.zeros(max_distort)

    # This list is for progress bar purposes
    test_run_list = list(range(TEST_RUNS))

    # Do this for TEST_RUNS times
    # Use tqdm for a progress bar display
    for num in tqdm(test_run_list, desc="Running tests: "):
        # Initialize accuracy list
        acc_list = []

        # Iterate through different distortion counts
        for i in range(max_distort):
            # Apply distortions to a test set
            distort_items = distort_inputs(dataset, i, IMG_PIXEL_NUM)

            # Encode set for query hypervectors
            query_hv_set = []
            for j in range(len(distort_items)):
                query_hv_set.append(
                    encode_character(
                        HV_DIM, ortho_im, distort_items[j], THRESHOLD, hv_type=HV_TYPE
                    )
                )

            # Generate predict set
            predict_set = prediction_set(assoc_mem, query_hv_set, hv_type=HV_TYPE)

            # Measure accuray of the test set
            acc_list.append(measure_acc(assoc_mem, predict_set, correct_set))

        # Append acc_list scores to an array
        avg_acc = avg_acc + np.array(acc_list)

    # Average accuracy scores in multiple test runs
    avg_acc = avg_acc / TEST_RUNS

    print("Average accuracy:")
    for i in range(len(avg_acc)):
        print(f"Avg accuracy for distortion num {i}: {avg_acc[i]}")
