#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
  Copyright 2025 KU Leuven
  Ryan Antonio <ryan.antonio@esat.kuleuven.be>

  Description:
  This program re-implements the DIGIT but dumps
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
    test_model_cuts_version,
    expand_im,
    expand_am_from_dict,
    n_sample_per_class,
)


DATA_URL = "https://github.com/KULeuven-MICAS/hypercorex/releases/download/ds_hdc_digit_recog_v.0.0.1/digit_recog.tar.gz"
DATA_SET_DIR = "data_set"
DATA_DIR = f"{DATA_SET_DIR}/digit_recog"


def encode_digit(image, ortho_im, cim):
    # Encode image
    hv_dim = len(ortho_im[0])
    encoded_image = gen_empty_hv(hv_dim)
    num_features = len(image)
    threshold = num_features / 2

    # Cycle through the entire line
    for pixel in range(num_features):
        # Get pixel value
        # Note that each pixel value is either 1 or 0
        # So we use the first 2 ortho im for this
        pixel_val_hv = ortho_im[image[pixel]]
        # Then everything from 2+ will be the pixel locations
        pixel_loc_hv = ortho_im[2 + pixel]
        pixel_val_loc_hv = bind_hv(pixel_val_hv, pixel_loc_hv, hv_type="binary")
        encoded_image += pixel_val_loc_hv

    # Binarize the encoded image
    encoded_image = binarize_hv(encoded_image, threshold, "binary")

    return encoded_image


if __name__ == "__main__":
    # Data paremeters
    EXTRACT_DATA = True
    TRAIN_MODEL = True
    TEST_MODEL = True
    SAVE_MODEL = True
    MULTI_MODE = True
    SAVE_SAMPLES = True
    HV_DIM_EXPANSION = 16

    TEST_SAMPLES_FILEPATH = root + "/test_samples/hypx_digit_test.txt"
    TEST_NSAMPLES_FILEPATH = root + "/test_samples/hypx_digit_nsample_test.txt"

    if MULTI_MODE:
        TRAINED_AM_FILEPATH = root + "/trained_am/hypx_digit_am_multi.txt"
    else:
        TRAINED_AM_FILEPATH = root + "/trained_am/hypx_digit_am.txt"

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
    NUM_FEATURES = 28 * 28
    NUM_CLASSES = 10
    NUM_TRAIN = 501
    NUM_RETRAIN = NUM_TRAIN
    NUM_TEST = 200

    # Take note of granularity
    VAL_LEVELS = 15

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

    if MULTI_MODE:
        ortho_im_set = []
        for i in range(HV_DIM_EXPANSION):
            ortho_im_set.append(np.roll(ortho_im, shift=-1 * i, axis=0))

    print("Extracting data...")
    train_data = dict()
    for num_class in range(NUM_CLASSES):
        # Training dataset
        read_file = f"{DATA_DIR}/bin_mnist_{num_class}.txt"
        train_data[num_class] = load_dataset(read_file)

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
                    cim=None,
                    encode_function=encode_digit,
                    tqdm_mode=1,
                )
                class_am.append(class_am_temp)
        else:
            class_am, _, _ = train_model(
                train_dataset=train_data,
                num_train=NUM_TRAIN,
                ortho_im=ortho_im,
                cim=None,
                encode_function=encode_digit,
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

    HV_DIM_EXPANSION = 2
    if TEST_MODEL:
        print("Testing model...")
        if MULTI_MODE:
            counts, scores, accuracies = test_model_cuts_version(
                test_dataset=train_data,
                ortho_im=ortho_im_set,
                cim=None,
                class_am=class_am,
                num_cuts=HV_DIM_EXPANSION,
                encode_function=encode_digit,
                starting_num_test=0,
                num_test=NUM_TEST,
                tqdm_mode=1,
                print_mode=1,
            )
        else:
            counts, scores, accuracies = test_model(
                test_dataset=train_data,
                ortho_im=ortho_im,
                cim=None,
                class_am=class_am,
                encode_function=encode_digit,
                starting_num_test=0,
                num_test=NUM_TEST,
                tqdm_mode=1,
                print_mode=1,
            )

    NUM_SAMPLES = 10
    if SAVE_SAMPLES:
        if MULTI_MODE:
            ortho_im_expand = expand_im(ortho_im, HV_DIM_EXPANSION)
            # AM expand uses same expand_cim
            class_am_expand = expand_am_from_dict(class_am, HV_DIM_EXPANSION)
        else:
            ortho_im_expand = ortho_im
            class_am_expand = class_am

        prediction_list = n_sample_per_class(
            num_samples=NUM_SAMPLES,
            num_classes=NUM_CLASSES,
            ortho_im=ortho_im_expand,
            cim=None,
            class_am=class_am_expand,
            test_data=train_data,
            encode_function=encode_digit,
            output_fp=TEST_NSAMPLES_FILEPATH,
        )
