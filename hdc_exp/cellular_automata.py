#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
    Copyright 2024 KU Leuven
    Ryan Antonio <ryan.antonio@esat.kuleuven.be>
    
    Description:
    This Python program investigates some properties
    of the cellular automata
"""

import numpy as np
from tqdm import tqdm
from hdc_util import (
    gen_ri_hv,
    simple_plot2d,
    gen_hv_ca90_iterate_rows,
    gen_hv_ca90_hierarchical_rows,
    gen_orthogonal_im,
    gen_conf_mat,
    heatmap_plot,
)


"""
    Some base parameters:
        HV_SEED - seed CA 90 HV
        HV_DIM - hypervector dimensions
"""

HV_SEED = 32
HV_DIM = 256
HV_ORTHO_DIST = int(HV_DIM / 2)
TEST_RUNS = 100


"""
    Other useful useful functions
"""


# Converting number to a binary numpy array
def numbin2list(numbin, dim):
    # Convert binary inputs first
    bin_hv = np.array(list(map(int, format(numbin, f"0{dim}b"))))
    return bin_hv


# Convert from list to binary value
def hvlist2num(hv_list):
    # Bring back into an integer itself!
    # Sad workaround is to convert to str
    # The convert to integer
    hv_num = "".join(hv_list.astype(str))
    hv_num = int(hv_num, 2)

    return hv_num


# Getting averageand std of scores
def gen_avg_std_scores(seed_list, ca90_mode="iter"):
    density_avg_list = []
    density_std_list = []

    for seed_size in seed_list:
        # Initialize score list
        density_list = np.zeros(TEST_RUNS)

        # Try for different runs
        for i in range(TEST_RUNS):
            # Assume 0.5 size
            hv_seed = gen_ri_hv(seed_size, 0.5)

            if ca90_mode == "iter":
                gen_hv = gen_hv_ca90_iterate_rows(hv_seed, HV_DIM)
            else:
                gen_hv = gen_hv_ca90_hierarchical_rows(hv_seed, HV_DIM)

            # Save similarity score
            density_list[i] = np.sum(gen_hv)

        # Save average and standard dev
        density_avg_list.append(np.mean(density_list))
        density_std_list.append(np.std(density_list))

    return density_avg_list, density_std_list


# For finding indices
def find_target_indices(lst, number):
    return list(np.where(np.array(lst) == number)[0])


"""
    Test functions
"""


"""
    seed_density_gen:
        - This determines the average generated
          density for different seed sizes.

    gen_density_list:
        - This is for generating a density list
          used for identifying which HV seeds
          generated the desired list!

    extract_target_seeds:
        - This function is for extracting seeds
          That give the target 50% density of a base HV
          
    gen_ca90_im_set
        - This generates the seeds for the item memory
          moreover it also generates a confusion matrix
          and a heatmap for inspection purposes
"""


def seed_density_gen():
    # For different seed sizes,
    # will we get consistent HV density?
    seed_list = [4, 8, 16, 32, 64, 128, 256, 512, 1024]

    # Extract for CA 90 iterative generation
    density_avg_list_iterate, density_std_list_iterate = gen_avg_std_scores(
        seed_list, ca90_mode="iter"
    )

    # Redo experiment but on a different HV generation thing
    density_avg_list_hierarchical, density_std_list_hierarchical = gen_avg_std_scores(
        seed_list, ca90_mode="hier"
    )

    # Ideal density
    density_ideal = len(seed_list) * [HV_ORTHO_DIST]

    # List of y values
    y_list = [density_avg_list_iterate, density_avg_list_hierarchical, density_ideal]

    # This plot answers the iterative
    # style of generating CA
    label_list = ["Iterative Generation", "Hierarchical Generation", "Ideal distance"]

    # Plot the lines
    simple_plot2d(
        x=seed_list,
        y=y_list,
        title="Average Density",
        xlabel="Seeds",
        ylabel="Density",
        marker="o",
        plt_label=label_list,
        legend=True,
        single_plot=False,
    )

    return


def gen_density_list(seed_size, hv_dim, ca90_mode="iter"):
    # Set total number of iterations
    seed_iterations = 2**seed_size
    half_dim = int(hv_dim / 2)

    # Initialize density list
    density_list = []

    # Iterate through all seed values
    for i in tqdm(range(seed_iterations), desc="Iterating seeds"):
        # Convert seed into binary numpy arrya
        hv_seed = numbin2list(i, seed_size)

        # Decide whether iterative or hierarchical
        if ca90_mode == "iter":
            gen_hv = gen_hv_ca90_iterate_rows(hv_seed, hv_dim)
        else:
            gen_hv = gen_hv_ca90_hierarchical_rows(hv_seed, hv_dim)

        # Sum up to determine the density
        density = np.sum(gen_hv)

        # Append density score to the list
        density_list.append(density)

    # Find all those densities with 50%
    # orthogonal values!
    density_half_list = find_target_indices(density_list, half_dim)

    return density_list, density_half_list


# This function is for extracting seeds
# That give the target 50% density of a base HV
def extract_target_seeds(seed_size, seed_num, hv_dim, ca90_mode="iter"):
    hv_half_dim = int(hv_dim / 2)
    seed_list = []
    seed_count = 0
    run_count = 0

    while seed_count != seed_num:
        run_count += 1
        hv_seed = gen_ri_hv(seed_size, 0.5)
        if ca90_mode == "iter":
            gen_hv = gen_hv_ca90_iterate_rows(hv_seed, hv_dim)
        else:
            gen_hv = gen_hv_ca90_hierarchical_rows(hv_seed, hv_dim)

        density_hv = np.sum(gen_hv)

        if density_hv == hv_half_dim:
            seed_idx = hvlist2num(hv_seed)
            seed_list.append(seed_idx)
            seed_count += 1

    print(f"Search count time: {run_count}")
    print(f"Target HV Dimension: {hv_dim}")
    print(f"Seed size: {seed_size}")
    print(f"Number of seeds: {seed_num}")

    return seed_list


# This function generates an item memory
# for the specified number of items and items per im bank
# It displays a heat map and displays the seeds to use
# Returns the seeds and the confusion matrix
def gen_ca90_im_set(
    seed_size,
    hv_dim,
    num_total_im,
    num_per_im_bank,
    ca90_mode="hier",
    display_heatmap=False,
):
    num_ims = int(num_total_im / num_per_im_bank)

    # Extract seed list that give
    # 50% density of a base HV
    seed_list = extract_target_seeds(seed_size, num_ims, hv_dim, ca90_mode=ca90_mode)

    # Generate the 1st orthogonal item memory
    hv_seed = numbin2list(seed_list[0], seed_size)
    ortho_im = gen_orthogonal_im(
        num_per_im_bank, hv_dim, 0.5, hv_seed, permute_base=7, im_type="ca90_hier"
    )

    # Generate all other sets
    for i in range(1, num_ims):
        hv_seed = numbin2list(seed_list[i], seed_size)
        temp_orth_im = gen_orthogonal_im(
            num_per_im_bank, hv_dim, 0.5, hv_seed, permute_base=7, im_type="ca90_hier"
        )
        ortho_im = np.concatenate((ortho_im, temp_orth_im), axis=0)

    # Get the confusion matrix!
    conf_mat = gen_conf_mat(num_total_im, ortho_im)

    # Plot the working heat map
    if display_heatmap:
        heatmap_plot(conf_mat)

    # Print the IM seeds to use
    print()  # for new line purposes
    for i in range(num_ims):
        print(f"IM seed #{i}: {seed_list[i]}")

    return seed_list, ortho_im, conf_mat


"""
    Main function list
"""
if __name__ == "__main__":
    # Current test to test the extraction
    # of target seeds for generating 50% density
    seed_size = 32
    hv_dim = 256
    ca90_mode = "hier"
    num_total_im = 512
    num_per_im_bank = 64

    seed_list, ortho_im, conf_mat = gen_ca90_im_set(
        seed_size,
        hv_dim,
        num_total_im,
        num_per_im_bank,
        ca90_mode=ca90_mode,
        display_heatmap=True,
    )
