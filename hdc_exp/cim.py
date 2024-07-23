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
    # Generate the CiM
    cim = gen_square_cim(HV_DIM)

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
