#!/usr/bin/env python3

# Copyright 2023 KU Leuven.
# Licensed under the Apache License, Version 2.0, see LICENSE for details.
# SPDX-License-Identifier: Apache-2.0
#
# Ryan Antonio <ryan.antonio@esat.kuleuven.be>

# ------------------------------------
# This is a generator script
# ------------------------------------
from mako.lookup import TemplateLookup
from mako.template import Template
import argparse
import os
import sys

# ------------------------------------
# Useful functions
# ------------------------------------


# For getting the root of the repository
def get_root():
    return os.getcwd()


# Read template
def get_template(tpl_path: str) -> Template:
    dir_name = os.path.dirname(tpl_path)
    file_name = os.path.basename(tpl_path)
    tpl_list = TemplateLookup(directories=[dir_name], output_encoding="utf-8")
    tpl = tpl_list.get_template(file_name)
    return tpl


# Generate file
def gen_file(cfg, tpl, target_path: str, file_name: str) -> None:
    # Check if path exists first if no, create directory
    if not (os.path.exists(target_path)):
        os.makedirs(target_path)

    # Writing file
    file_path = target_path + file_name
    with open(file_path, "w") as f:
        f.write(str(tpl.render_unicode(cfg=cfg)))
    return


# ---------------------
# Utility import
# ---------------------
tests_path = get_root() + "/tests/"
sys.path.append(tests_path)

import set_parameters  # noqa: E402

# Add hdc utility functions
hdc_util_path = get_root() + "/hdc_exp/"
sys.path.append(hdc_util_path)

# Grab the CA90 generation from the
# cellular automata experiment set
from cellular_automata import gen_ca90_im_set  # noqa: E402


# Main function
def main():
    # Parse all arguments
    parser = argparse.ArgumentParser(
        description="Wrapper generator for any file. \
            Inputs are simply the template and configuration files."
    )
    parser.add_argument(
        "--tpl_path",
        type=str,
        default="./",
        help="Points to the streamer template file path",
    )
    parser.add_argument(
        "--gen_rom_im",
        action="store_true",
        help="Generate ROM iM",
    )
    parser.add_argument(
        "--gen_rom_im_size",
        type=int,
        default=0,
        help="Size of ROM iM size",
    )
    parser.add_argument(
        "--gen_rom_im_dw",
        type=int,
        default=0,
        help="Size of ROM iM data width",
    )
    parser.add_argument(
        "--out_path", type=str, default="./", help="Points to the output directory"
    )

    # Get the list of parsing
    args = parser.parse_args()

    if args.gen_rom_im:
        # ------------------------------------------
        # Make sure we have correct parameters
        # ------------------------------------------
        assert args.gen_rom_im_size != 0, "Error! IM memory needs a size!"
        assert args.gen_rom_im_dw != 0, "Error! IM memory needs a datawidth!"

        print(f"Item memory size: {args.gen_rom_im_size}")
        print(f"Item memory data width: {args.gen_rom_im_dw}")

        print(f"Getting tpl from: {args.tpl_path}")
        print(f"Dumping rom at: {args.out_path}")

        num_per_im_bank = int(args.gen_rom_im_dw // 4)

        # Generate seed list and golden IM
        seed_list, golden_im, conf_mat = gen_ca90_im_set(
            seed_size=set_parameters.REG_FILE_WIDTH,
            hv_dim=args.gen_rom_im_dw,
            num_total_im=args.gen_rom_im_size,
            num_per_im_bank=num_per_im_bank,
            gen_seed=True,
            base_seeds=set_parameters.ORTHO_IM_SEEDS,
            ca90_mode=set_parameters.CA90_MODE,
        )

        # Make list
        str_im_list = []
        for item in golden_im:
            temp_str = "".join(str(bin) for bin in item)
            str_im_list.append(temp_str)

        # Read tpl
        rom_tpl = get_template(args.tpl_path)

        # Generate file
        gen_file(
            cfg=str_im_list,
            tpl=rom_tpl,
            target_path=args.out_path,
            file_name="rom_item_memory.sv",
        )

    return


if __name__ == "__main__":
    main()
