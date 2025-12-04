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
    bind_hv,
    binarize_hv,
    extract_dataset,
    measure_acc,
    prediction_set,
    simple_plot2d,
    gen_ri_hv,
    gen_ca90_im_set,
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
HV_DIM = 256
P_DENSE = 0.5
HV_SEED_DIM = HV_DIM
HV_SEED_DENSE = 1 / 2
THRESHOLD = np.floor(IMG_ROW_NUM * IMG_COL_NUM / 2)

# Test parameters
TEST_RUNS = 10


"""
    Other useful useful functions for this test only
"""


# Extract character recognition data set
# and return the integer array form
def char_recog_dataset(file_path):
    # Extract data
    dataset = extract_dataset(file_path)

    # Minor data clean to make the data a list
    # of binary numbers instead of characters
    for i in range(len(dataset)):
        dataset[i] = np.array(list(map(int, list(dataset[i]))))

    return dataset


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
def encode_character(
    hv_dim,
    ortho_im,
    character_input,
    threshold,
    debug=False,
    encode_mode="indexed",
    hv_type="binary",
):
    # Initialize empty character hypervector
    char_hv = gen_empty_hv(hv_dim)

    # Cycle through every pixel
    if encode_mode == "bind":
        # This is a nasty hard fix but the idea is to
        # reverse the order because the tool python list reads
        # the list in a reverse way...
        character_input = character_input[::-1]
        for i in range(len(character_input)):
            pixel_val_hv = ortho_im[character_input[i]]

            pixel_pos_hv = ortho_im[2 + i]
            char_hv += bind_hv(pixel_val_hv, pixel_pos_hv)

            if debug:
                print(f"character_input: {character_input[i]}")
                print(f"position: {i}")
                print(f"pixel_val_hv: {pixel_val_hv}")
                print(f"pixel_pos_hv: {pixel_pos_hv}")
                print(f"char_hv: {pixel_val_hv}")

    else:
        for i in range(len(character_input)):
            # If pixel value is a 1
            if character_input[i] == 1:
                # For non permutative encoding
                # We only select a different
                # orthogonal HV from the ortho im set
                if encode_mode == "indexed":
                    char_hv += ortho_im[35 + i]
                # Otherwise we do the normal orothogonal
                # pemuting based on the original feature
                elif encode_mode == "circ_perm":
                    char_hv += circ_perm_hv(ortho_im[i], 1)
            # If pixel is black, we just select
            # the base othorgonal HV
            else:
                char_hv += ortho_im[i]

    # Binarize the bundled HV
    char_hv = binarize_hv(char_hv, threshold, hv_type)

    return char_hv


# Encoding with binding
def encode_with_bind(
    hv_dim,
    ortho_im,
    character_input,
    threshold,
    debug=False,
    encode_mode="indexed",
    hv_type="binary",
):
    # Initialize empty character hypervector
    char_hv = encode_character(
        hv_dim,
        ortho_im,
        character_input,
        threshold,
        debug=debug,
        encode_mode=encode_mode,
        hv_type=hv_type,
    )
    return char_hv


# Encoding with indices
def encode_with_idx(hv_dim, ortho_im, character_input, threshold, hv_type="binary"):
    # Initialize empty character hypervector
    char_hv = gen_empty_hv(hv_dim)

    # Cycle through every pixel
    for i in character_input:
        char_hv += ortho_im[i]

    # Binarize the bundled HV
    char_hv = binarize_hv(char_hv, threshold, hv_type)

    return char_hv


# Convert pixel and position into im indices
def convert_to_data_indices(dataset):
    data_indices = []
    for i in range(len(dataset)):
        data_idx = []
        for j in range(len(dataset[i])):
            if dataset[i][j] == 1:
                data_idx.append(35 + j)
            else:
                data_idx.append(j)
        data_indices.append(data_idx)
    return data_indices


# Training the character recognition set
def train_char_recog(
    dataset, hv_dim, ortho_im, threshold, encode_mode="indexed", hv_type="binary"
):
    # Initialize empty assoc mem list
    assoc_mem = []

    # For each item in data set to train
    for i in range(len(dataset)):
        # Append the encoded character
        assoc_mem.append(
            encode_character(
                hv_dim=hv_dim,
                ortho_im=ortho_im,
                character_input=dataset[i],
                threshold=threshold,
                encode_mode=encode_mode,
                hv_type=hv_type,
            )
        )

    return assoc_mem


# Entire character recognition run
def run_char_recog_test(
    dataset, max_distort, test_runs, hv_seed_dim, encode_mode="indexed", im_gen="random"
):
    # Correct answer set (this is fixed for char recog)
    correct_set = list(range(NUM_CLASSSES))

    # Generate base hypervectors
    # Depending on the type of generation
    if im_gen == "random":
        hv_seed = 0
    else:
        # This case covers CA 90
        hv_seed = gen_ri_hv(hv_seed_dim, P_DENSE)

    if encode_mode == "indexed":
        num_hv = 2 * IMG_PIXEL_NUM
    else:
        num_hv = IMG_PIXEL_NUM

    ortho_im = gen_orthogonal_im(
        num_hv=num_hv,
        hv_dim=HV_DIM,
        p_dense=P_DENSE,
        hv_seed=hv_seed,
        hv_type=HV_TYPE,
        im_type=im_gen,
    )

    # Encode the characters into AM
    # This is the training part
    assoc_mem = train_char_recog(
        dataset=dataset,
        hv_dim=HV_DIM,
        ortho_im=ortho_im,
        threshold=THRESHOLD,
        encode_mode=encode_mode,
        hv_type=HV_TYPE,
    )

    # This is the testing part
    # Test for different distortions
    avg_acc = np.zeros(max_distort)

    # This list is for progress bar purposes
    test_run_list = list(range(test_runs))

    # Do this for test_runs times
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
                        HV_DIM,
                        ortho_im,
                        distort_items[j],
                        THRESHOLD,
                        encode_mode=encode_mode,
                        hv_type=HV_TYPE,
                    )
                )

            # Generate predict set
            predict_set = prediction_set(assoc_mem, query_hv_set, hv_type=HV_TYPE)

            # Measure accuray of the test set
            acc_list.append(measure_acc(assoc_mem, predict_set, correct_set))

        # Append acc_list scores to an array
        avg_acc = avg_acc + np.array(acc_list)

    # Average accuracy scores in multiple test runs
    avg_acc = avg_acc / test_runs

    print("Average accuracy:")
    for i in range(len(avg_acc)):
        print(f"Avg accuracy for distortion num {i}: {avg_acc[i]}")

    return avg_acc


# Experiemnt 1 to display trends for distortion
# TODO: clean me later
def exp_distort_test():
    # Get original data set
    file_path = "./data_set/char_recog/characters.txt"
    dataset = char_recog_dataset(file_path)

    # Set max number of distortions
    max_distort = 20

    # For the x-axis plot later
    distort_x_list = list(range(max_distort))

    # Run the character recognition sets
    # First get the normal item memory generation
    avg_acc_random_im = run_char_recog_test(
        dataset,
        max_distort,
        TEST_RUNS,
        hv_seed_dim=0,
        encode_mode="indexed",
        im_gen="random",
    )

    # Get the CA 90 dependent generations
    avg_acc_ca90_iter_im_list = []
    avg_acc_ca90_hier_im_list = []

    for i in range(8):
        # Run the character recognition per CA 90
        avg_acc_ca90_iter_im = run_char_recog_test(
            dataset,
            max_distort,
            TEST_RUNS,
            hv_seed_dim=int(HV_DIM / (2**i)),
            im_gen="ca90_iter",
        )
        avg_acc_ca90_hier_im = run_char_recog_test(
            dataset,
            max_distort,
            TEST_RUNS,
            hv_seed_dim=int(HV_DIM / (2**i)),
            im_gen="ca90_hier",
        )

        # Save into the list
        avg_acc_ca90_iter_im_list.append(avg_acc_ca90_iter_im)
        avg_acc_ca90_hier_im_list.append(avg_acc_ca90_hier_im)

    # List of y-axis value
    avg_acc_list = [
        avg_acc_random_im,
        avg_acc_ca90_iter_im_list[0],
        avg_acc_ca90_hier_im_list[0],
        avg_acc_ca90_iter_im_list[1],
        avg_acc_ca90_hier_im_list[1],
        avg_acc_ca90_iter_im_list[2],
        avg_acc_ca90_hier_im_list[2],
        avg_acc_ca90_iter_im_list[3],
        avg_acc_ca90_hier_im_list[3],
        avg_acc_ca90_iter_im_list[4],
        avg_acc_ca90_hier_im_list[4],
        avg_acc_ca90_iter_im_list[5],
        avg_acc_ca90_hier_im_list[5],
        avg_acc_ca90_iter_im_list[6],
        avg_acc_ca90_hier_im_list[6],
        avg_acc_ca90_iter_im_list[7],
        avg_acc_ca90_hier_im_list[7],
    ]

    # Label list
    label_list = [
        "Random",
        "CA 90 Iterative Seed 256",
        "CA 90 Hierarchical Seed 256",
        "CA 90 Iterative Seed 128",
        "CA 90 Hierarchical Seed 128",
        "CA 90 Iterative Seed 64",
        "CA 90 Hierarchical Seed 64",
        "CA 90 Iterative Seed 32",
        "CA 90 Hierarchical Seed 32",
        "CA 90 Iterative Seed 16",
        "CA 90 Hierarchical Seed 16",
        "CA 90 Iterative Seed 8",
        "CA 90 Hierarchical Seed 8",
        "CA 90 Iterative Seed 4",
        "CA 90 Hierarchical Seed 4",
        "CA 90 Iterative Seed 2",
        "CA 90 Hierarchical Seed 2",
    ]

    # Plot multiple lines
    simple_plot2d(
        x=distort_x_list,
        y=avg_acc_list,
        title="Accuracy vs Distortion",
        xlabel="Distortion Number",
        ylabel="Accuracy",
        plt_label=label_list,
        marker="o",
        single_plot=False,
    )
    return


# Main function to run the character recognition program
if __name__ == "__main__":
    # Some working parameters
    seed_size = 32
    hv_dim = 256
    num_total_im = 512
    num_per_im_bank = int(hv_dim // 4)
    threshold = THRESHOLD
    encode_mode = "bind"

    # Get original data set
    file_path = "./data_set/char_recog/characters.txt"
    dataset = char_recog_dataset(file_path)

    # Correct result
    correct_set = list(range(26))

    # Prepare data indices for the accelerator
    data_indices = convert_to_data_indices(dataset)

    base_seeds = [
        1103779247,
        2391206478,
        3074675908,
        2850820469,
        811160829,
        4032445525,
        2525737372,
        2535149661,
    ]

    # Get a CA90 seed that's working
    seed_list, ortho_im, conf_mat = gen_ca90_im_set(
        seed_size,
        hv_dim,
        num_total_im,
        num_per_im_bank,
        base_seeds=base_seeds,
        gen_seed=True,
        ca90_mode="hier",
        debug_info=True,
        display_heatmap=False,
    )

    # Training of AM and extracting
    # Converted data list
    assoc_mem = []

    assoc_mem = train_char_recog(
        dataset, hv_dim, ortho_im, threshold, encode_mode=encode_mode, hv_type="binary"
    )

    # query_hv = encode_with_bind(
    #             hv_dim,
    #             ortho_im,
    #             dataset[0],
    #             threshold,
    #             debug=True,
    #             encode_mode=encode_mode,
    #             hv_type="binary",
    #         )

    # Encode query_hv_list
    query_hv_set = []

    for i in range(NUM_CLASSSES):
        if encode_mode == "bind":
            query_hv = encode_with_bind(
                hv_dim,
                ortho_im,
                dataset[i],
                threshold,
                encode_mode=encode_mode,
                hv_type="binary",
            )
        else:
            query_hv = encode_with_idx(
                hv_dim, ortho_im, data_indices[i], threshold, hv_type="binary"
            )

        query_hv_set.append(query_hv)

    # Get prediction set
    predict_set = prediction_set(assoc_mem, query_hv_set, hv_type="binary")

    # Accuracy measurement
    acc = measure_acc(predict_set, correct_set)

    print(f"Accuracy: {acc * 100}")
