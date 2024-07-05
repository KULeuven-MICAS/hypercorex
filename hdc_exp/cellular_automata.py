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
from hdc_util import (
    gen_ri_hv,
    simple_plot2d,
    gen_hv_ca90_iterate_rows,
    gen_hv_ca90_hierarchical_rows,
)


"""
    Some base parameters:
        HV_SEED - seed CA 90 HV
        HV_DIM - hypervector dimensions
"""

HV_SEED = 8
HV_DIM = 1024
TEST_RUNS = 100


"""
    Other useful useful functions
"""


"""
    Main function list
"""
if __name__ == "__main__":
    # For different seed sizes,
    # will we get consistent HV density?
    seed_list = [4, 8, 16, 32, 64, 128, 256, 512, 1024]
    density_avg_list_iterate = []
    density_std_list_iterate = []

    for seed_size in seed_list:
        # Initialize score list
        density_list = np.zeros(TEST_RUNS)

        # Try for different runs
        for i in range(TEST_RUNS):
            # Assume 0.5 size
            hv_seed = gen_ri_hv(seed_size, 0.5)
            gen_hv = gen_hv_ca90_iterate_rows(hv_seed, HV_DIM)

            # Save similarity score
            density_list[i] = np.sum(gen_hv)

        # Save average and standard dev
        density_avg_list_iterate.append(np.mean(density_list))
        density_std_list_iterate.append(np.std(density_list))

    # Redo experiment but on a different HV generation thing
    density_avg_list_hierarchical = []
    density_std_list_hierarchical = []

    # Do this for different seed sizes
    for seed_size in seed_list:
        # Initialize score list
        density_list = np.zeros(TEST_RUNS)

        # Try for different runs
        for i in range(TEST_RUNS):
            # Assume 0.5 size
            hv_seed = gen_ri_hv(seed_size, 0.5)
            gen_hv = gen_hv_ca90_hierarchical_rows(hv_seed, HV_DIM)

            # Save similarity score
            density_list[i] = np.sum(gen_hv)

        # Save average and standard dev
        density_avg_list_hierarchical.append(np.mean(density_list))
        density_std_list_hierarchical.append(np.std(density_list))

    # List of y values
    y_list = [density_avg_list_iterate, density_avg_list_hierarchical]

    # This plot answers the iterative
    # style of generating CA
    label_list = ["Iterative Generation", "Hierarchical Generation"]

    # Plot the lines
    simple_plot2d(
        x=seed_list,
        y=y_list,
        title="Average Density",
        xlabel="Seeds",
        ylabel="Density",
        marker="o",
        plt_label=label_list,
        single_plot=False,
    )
