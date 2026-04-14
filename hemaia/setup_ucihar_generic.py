#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
  Copyright 2025 KU Leuven
  Ryan Antonio <ryan.antonio@esat.kuleuven.be>

  Description:
  This program re-implements the ucihar but dumps
  data for the Hemaia project
"""
import sys
import os
import numpy as np

# Extract paths
root = os.getcwd()

hdc_util_path = root + "/../hdc_exp/"
print(hdc_util_path)
sys.path.append(hdc_util_path)

from hdc_util import (  # noqa: E402
    extract_git_dataset,
    load_dataset,
    save_am_model,
    load_am_model,
    train_model,
    test_model,
    gen_empty_hv,
    bind_hv,
    binarize_hv,
    gen_ca90_im_set,
    gen_square_cim,
    test_model_cuts_version,
    expand_im,
    expand_cim,
    expand_am_from_dict,
    convert_levels,
    n_sample_per_class,
)

DATA_URL = "https://github.com/KULeuven-MICAS/hypercorex/releases/download/ds_hdc_ucihar_recog_v0.0.1/ucihar_recog.tar.gz"
DATA_SET_DIR = "data_set"
DATA_TRAIN_DIR = f"{DATA_SET_DIR}/ucihar_recog/train"
DATA_TEST_DIR = f"{DATA_SET_DIR}/ucihar_recog/test"


def encode_ucihar(sample, ortho_im, cim):
    # Encode sample
    hv_dim = len(ortho_im[0])
    encoded_sample = gen_empty_hv(hv_dim)
    num_features = len(sample)
    threshold = num_features / 2

    # Cycle through the entire line
    for attribute_num in range(num_features):
        # Get ID HV
        attribute_id_hv = ortho_im[attribute_num]
        # Get value HV at that ID
        attribute_val_hv = cim[sample[attribute_num]]
        # Bind ID and value HVs
        attribute_val_loc_hv = bind_hv(
            attribute_id_hv, attribute_val_hv, hv_type="binary"
        )
        # Accumulate through all samples
        encoded_sample += attribute_val_loc_hv

    # Binarize the encoded sample
    encoded_sample = binarize_hv(encoded_sample, threshold, "binary")

    return encoded_sample


if __name__ == "__main__":
    # Data paremeters
    EXTRACT_DATA = True
    TRAIN_MODEL = True
    TEST_MODEL = True
    SAVE_MODEL = True
    MULTI_MODE = True
    SAVE_SAMPLES = True
    HV_DIM_EXPANSION = 16

    TEST_SAMPLES_FILEPATH = root + "/test_samples/hypx_ucihar_test.txt"
    TEST_NSAMPLES_FILEPATH = root + "/test_samples/hypx_ucihar_nsample_test.txt"

    if MULTI_MODE:
        TRAINED_AM_FILEPATH = root + "/trained_am/hypx_ucihar_am_multi.txt"
    else:
        TRAINED_AM_FILEPATH = root + "/trained_am/hypx_ucihar_am.txt"

    # Hypercorex parameters
    SEED_DIM = 32
    HV_DIM = 512
    NUM_TOT_IM = 1024
    NUM_PER_IM_BANK = 128
    CIM_BASE_SEED = 621635317
    BASE_SEEDS = [
        1103779247,
        2391206478,
        3074675908,
        2850820469,
        811160829,
        4032445525,
        2525737372,
        2535149661,
    ]

    # Application parameters
    NUM_FEATURES = 561
    NUM_CLASSES = 6
    NUM_TRAIN = 511
    NUM_RETRAIN = NUM_TRAIN
    NUM_TEST = 450

    # Take note of granularity
    VAL_LEVELS = 21

    # Extract data
    if EXTRACT_DATA:
        extract_git_dataset(DATA_URL, DATA_SET_DIR)

    # Ortho IM generation
    seed_list, ortho_im, conf_mat = gen_ca90_im_set(
        SEED_DIM,
        HV_DIM,
        NUM_TOT_IM,
        NUM_PER_IM_BANK,
        base_seeds=BASE_SEEDS,
        gen_seed=True,
        ca90_mode="hier",
        debug_info=True,
        display_heatmap=False,
    )

    # CIM generation
    cim_seed, cim = gen_square_cim(
        base_seed=CIM_BASE_SEED,
        gen_seed=False,
        hv_dim=HV_DIM,
        seed_size=SEED_DIM,
        im_type="ca90_hier",
    )

    if MULTI_MODE:
        ortho_im_set = []
        for i in range(HV_DIM_EXPANSION):
            ortho_im_set.append(np.roll(ortho_im, shift=-1 * i, axis=0))

    print("Extracting data...")
    train_data = dict()
    for num_class in range(NUM_CLASSES):
        # Training dataset
        read_file = f"{DATA_TRAIN_DIR}/uint8_ucihar_train_{num_class}.txt"
        train_data[num_class] = load_dataset(read_file)

    # For simplicity use both train data
    test_data = dict()
    for num_class in range(NUM_CLASSES):
        # Training dataset
        read_file = f"{DATA_TEST_DIR}/uint8_ucihar_test_{num_class}.txt"
        test_data[num_class] = load_dataset(read_file)

    print("Converting data...")
    train_data = convert_levels(train_data, VAL_LEVELS, VAL_LEVELS - 1)
    test_data = convert_levels(test_data, VAL_LEVELS, VAL_LEVELS - 1)

    if TRAIN_MODEL:
        print("Training model...")
        if MULTI_MODE:
            class_am = []
            for i in range(HV_DIM_EXPANSION):
                print(f"Set number: {i}")
                class_am_temp, _, _ = train_model(
                    train_dataset=train_data,
                    num_train=NUM_TRAIN,
                    ortho_im=ortho_im_set[i],
                    cim=cim,
                    encode_function=encode_ucihar,
                    tqdm_mode=1,
                )
                class_am.append(class_am_temp)
        else:
            class_am, _, _ = train_model(
                train_dataset=train_data,
                num_train=NUM_TRAIN,
                ortho_im=ortho_im,
                cim=cim,
                encode_function=encode_ucihar,
                tqdm_mode=1,
            )
    else:
        print("Loading AM model...")
        class_am = load_am_model(TRAINED_AM_FILEPATH)

    if SAVE_MODEL:
        if MULTI_MODE:
            save_am_model(TRAINED_AM_FILEPATH, class_am, multi_mode=True)
        else:
            save_am_model(TRAINED_AM_FILEPATH, class_am)

    HV_DIM_EXPANSION = 16
    if TEST_MODEL:
        print("Testing model...")
        if MULTI_MODE:
            counts, scores, accuracies = test_model_cuts_version(
                test_dataset=train_data,
                ortho_im=ortho_im_set,
                cim=cim,
                class_am=class_am,
                num_cuts=HV_DIM_EXPANSION,
                encode_function=encode_ucihar,
                starting_num_test=0,
                num_test=NUM_TEST,
                tqdm_mode=1,
                print_mode=1,
            )
        else:
            counts, scores, accuracies = test_model(
                test_dataset=train_data,
                ortho_im=ortho_im,
                cim=cim,
                class_am=class_am,
                encode_function=encode_ucihar,
                starting_num_test=0,
                num_test=NUM_TEST,
                tqdm_mode=1,
                print_mode=1,
            )

    NUM_SAMPLES = 16
    if SAVE_SAMPLES:
        if MULTI_MODE:
            ortho_im_expand = expand_im(ortho_im, HV_DIM_EXPANSION)
            cim_expand = expand_cim(cim, HV_DIM_EXPANSION)
            class_am_expand = expand_am_from_dict(class_am, HV_DIM_EXPANSION)
        else:
            ortho_im_expand = ortho_im
            class_am_expand = class_am
            cim_expand = cim

        prediction_list = n_sample_per_class(
            num_samples=NUM_SAMPLES,
            num_classes=NUM_CLASSES,
            ortho_im=ortho_im_expand,
            cim=cim_expand,
            class_am=class_am_expand,
            test_data=train_data,
            encode_function=encode_ucihar,
            output_fp=TEST_NSAMPLES_FILEPATH,
        )
