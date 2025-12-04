#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Copyright 2024 KU Leuven
Ryan Antonio <ryan.antonio@esat.kuleuven.be>

Description:
These contain useful functions for generating golden values
for regression tests.
"""
# Main importations
from hdc_util import (
    bind_hv,
    gen_ca90_im_set,
)

snax_hypercorex_parameters = {
    "seed_size": 32,
    "hv_dim": 512,
    "num_total_im": 1024,
    "num_per_im_bank": 128,
    "base_seeds": [
        1103779247,
        2391206478,
        3074675908,
        2850820469,
        811160829,
        4032445525,
        2525737372,
        2535149661,
    ],
    "gen_seed": True,
    "ca90_mode": "ca90_hier",
}


# Load out iM data only
def data_ortho_im_only(
    seed_size,
    hv_dim,
    num_total_im,
    num_per_im_bank,
    base_seeds,
    gen_seed,
    ca90_mode,
):
    # Generate ortho im
    im_seed_list, ortho_im, conf_mat = gen_ca90_im_set(
        seed_size=seed_size,
        hv_dim=hv_dim,
        num_total_im=num_total_im,
        num_per_im_bank=num_per_im_bank,
        base_seeds=base_seeds,
        gen_seed=gen_seed,
        ca90_mode=ca90_mode,
    )
    golden_list = ortho_im
    return ortho_im, golden_list


# Low dim fetch and bind check
def data_autofetch_bind(
    seed_size,
    hv_dim,
    num_total_im,
    num_per_im_bank,
    base_seeds,
    gen_seed,
    ca90_mode,
):
    # Gmake cenerate ortho im
    im_seed_list, ortho_im, conf_mat = gen_ca90_im_set(
        seed_size=seed_size,
        hv_dim=hv_dim,
        num_total_im=num_total_im,
        num_per_im_bank=num_per_im_bank,
        base_seeds=base_seeds,
        gen_seed=gen_seed,
        ca90_mode=ca90_mode,
    )
    # For half of the seed bind the IM
    # then generate results for it
    # Half of iM memory count
    half_im = num_total_im // 2
    golden_list = []
    for i in range(half_im):
        golden_list.append(bind_hv(ortho_im[i], ortho_im[i + half_im]))

    return ortho_im, golden_list


if __name__ == "__main__":
    ortho_im, golden_list = data_autofetch_bind(
        seed_size=snax_hypercorex_parameters["seed_size"],
        hv_dim=snax_hypercorex_parameters["hv_dim"],
        num_total_im=snax_hypercorex_parameters["num_total_im"],
        num_per_im_bank=snax_hypercorex_parameters["num_per_im_bank"],
        base_seeds=snax_hypercorex_parameters["base_seeds"],
        gen_seed=snax_hypercorex_parameters["gen_seed"],
        ca90_mode=snax_hypercorex_parameters["ca90_mode"],
    )
