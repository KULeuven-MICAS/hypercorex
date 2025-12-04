#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Copyright 2024 KU Leuven
Ryan Antonio <ryan.antonio@esat.kuleuven.be>

Description:
This Python program tests and investigates
the case for continuous item memories
"""

from hdc_util import (
    gen_square_cim,
    gen_conf_mat,
    heatmap_plot,
)

"""
    Some base parameters:
        HV_SEED - seed CA 90 HV
        HV_DIM - hypervector dimensions
"""

HV_DIM = 256


"""
    Main function list
"""
if __name__ == "__main__":
    # Set a pre-determined seed
    seed_size = 32

    # Pre-calcualted custom seed
    base_seed = 621635317

    # Generate the CiM
    hv_seed, cim = gen_square_cim(
        HV_DIM,
        seed_size,
        base_seed=base_seed,
        gen_seed=False,
        im_type="ca90_hier",
        debug_info=True,
    )

    # Number of CiM levels
    cim_levels = len(cim)

    # Create a confusion matrix
    conf_mat = gen_conf_mat(cim_levels, cim)

    # Display heatmap
    heatmap_plot(
        conf_mat,
        title="CiM Heatmap",
        xlabel="distance",
        ylabel="distance",
    )
