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
HV_ORTHO_DIST = int(HV_DIM / 2)
TEST_RUNS = 100


"""
    Other useful useful functions
"""


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


"""
    Main function list
"""
if __name__ == "__main__":
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
