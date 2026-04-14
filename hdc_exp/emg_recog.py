#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
  Copyright 2025 KU Leuven
  Ryan Antonio <ryan.antonio@esat.kuleuven.be>

  Description:
  This program implements the emg classification
  using Hyperdimensional Computing (HDC) techniques.
"""

import numpy as np

from hdc_util import (
    load_dataset,
    train_model,
    test_model,
    circ_perm_hv,
    gen_empty_hv,
    gen_orthogonal_im,
    expand_im,
    expand_cim,
    bind_hv,
    binarize_hv,
    gen_ca90_im_set,
    gen_cim,
    gen_square_cim,
)

# DATA_URL = "https://github.com/KULeuven-MICAS/hypercorex/releases/download/ds_hdc_emg_recog_v.0.01/emg_recog.tar.gz"
DATA_SET_DIR = "data_set"
DATA_DIR = f"{DATA_SET_DIR}/emg_recog/train"
NGRAM = 4


def encode_emg(sample, ortho_im, cim):
    # Encode sample
    hv_dim = len(ortho_im[0])
    encoded_sample = gen_empty_hv(hv_dim)
    num_features = len(sample)
    ngram = NGRAM
    threshold = 2

    # Cycle through the entire line
    encoded_sample = gen_empty_hv(hv_dim)
    ngram_num = 0

    for attribute_num in range(0, num_features, ngram):
        # channel samples
        ch_hv_1 = ortho_im[attribute_num]
        ch_hv_2 = ortho_im[attribute_num + 1]
        ch_hv_3 = ortho_im[attribute_num + 2]
        ch_hv_4 = ortho_im[attribute_num + 3]
        # Get value HV at that ID
        val_hv_1 = cim[sample[attribute_num]]
        val_hv_2 = cim[sample[attribute_num + 1]]
        val_hv_3 = cim[sample[attribute_num + 2]]
        val_hv_4 = cim[sample[attribute_num + 3]]
        # Bind ID and value HVs
        ch_val_hv_1 = bind_hv(ch_hv_1, val_hv_1, hv_type="binary")
        ch_val_hv_2 = bind_hv(ch_hv_2, val_hv_2, hv_type="binary")
        ch_val_hv_3 = bind_hv(ch_hv_3, val_hv_3, hv_type="binary")
        ch_val_hv_4 = bind_hv(ch_hv_4, val_hv_4, hv_type="binary")
        # Bundle the bounded HVs
        spatial_bundle_sum = ch_val_hv_1 + ch_val_hv_2 + ch_val_hv_3 + ch_val_hv_4
        spatial_bundle = binarize_hv(spatial_bundle_sum, threshold, "binary")
        # permute the spatial HV
        temp_bind = circ_perm_hv(spatial_bundle, ngram_num)
        encoded_sample = bind_hv(encoded_sample, temp_bind, hv_type="binary")
        ngram_num += 1

    return encoded_sample


if __name__ == "__main__":
    SEED_DIM = 32
    HV_DIM = 8192
    ENABLE_HV_EXPANSION = False
    HV_DIM_EXPANSION = 16
    NUM_TOT_IM = 1024
    NUM_PER_IM_BANK = 128

    USE_CA90_IM = False
    USE_CA90_CIM = False
    EXTRACT_DATA = False

    VAL_LEVELS = 21
    NUM_CLASSES = 5
    NUM_TRAIN = 200
    NUM_RETRAIN = NUM_TRAIN
    NUM_TEST = 200

    NUM_FEATURES = 16

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

    # if EXTRACT_DATA:
    #     extract_git_dataset(DATA_URL, DATA_SET_DIR)

    if USE_CA90_IM:
        # Get a CA90 seed that's working
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
    else:
        # Generate orthogonal samples using the specified parameters
        ortho_im = gen_orthogonal_im(
            num_hv=NUM_TOT_IM,
            hv_dim=HV_DIM,
            p_dense=0.5,
            hv_seed=0,
            permute_base=1,
            hv_type="binary",
            im_type="random",
        )

    if USE_CA90_CIM:
        _, cim = gen_square_cim(
            hv_dim=HV_DIM,
            seed_size=32,
            base_seed=CIM_BASE_SEED,
            gen_seed=False,
            im_type="ca90_hier",
            debug_info=False,
        )
    else:
        cim = gen_cim(
            hv_dim=HV_DIM,
            seed_size=32,
            num_hv=VAL_LEVELS,
            base_seed=CIM_BASE_SEED,
            gen_seed=False,
            max_ortho=True,
            im_type="random",
            hv_type="binary",
            debug_info=False,
        )

    if ENABLE_HV_EXPANSION:
        ortho_im = expand_im(ortho_im, HV_DIM_EXPANSION)
        cim = expand_cim(cim, HV_DIM_EXPANSION)

    print("Extracting data...")
    train_data_orig = dict()
    for num_class in range(NUM_CLASSES):
        # Training dataset
        read_file = f"{DATA_DIR}/emg_train_data{num_class}.txt"
        train_data_orig[num_class] = load_dataset(read_file)

    # Re-aligning data into windows
    train_data = {
        0: [],
        1: [],
        2: [],
        3: [],
        4: [],
    }

    # Making the sliding window data
    for num_class in range(NUM_CLASSES):
        item_num = 0
        for train_count in range(NUM_TRAIN):
            temp_data = train_data_orig[num_class][item_num]
            for feature_count in range(NUM_FEATURES - 1):
                temp_data = np.concatenate(
                    (
                        temp_data,
                        train_data_orig[num_class][item_num + feature_count + 1],
                    ),
                    axis=0,
                )
            train_data[num_class].append(temp_data)
            item_num += NUM_FEATURES

    # For simplicity use both train data
    test_data = train_data

    print("Training model...")
    class_am, class_am_int, class_am_elem_count = train_model(
        train_dataset=train_data,
        num_train=NUM_TRAIN,
        ortho_im=ortho_im,
        cim=cim,
        encode_function=encode_emg,
        tqdm_mode=1,
    )

    print("Testing model...")
    counts, scores, accuracies = test_model(
        test_dataset=train_data,
        ortho_im=ortho_im,
        cim=cim,
        class_am=class_am,
        encode_function=encode_emg,
        starting_num_test=0,
        num_test=NUM_TEST,
        tqdm_mode=1,
        print_mode=1,
    )

    # print("Retraining model...")
    # (
    #     class_am_retrained,
    #     class_am_int_retrained,
    #     class_am_elem_count_retrained,
    # ) = retrain_model(
    #     retrain_dataset=train_data,
    #     num_retrain=NUM_RETRAIN,
    #     ortho_im=ortho_im,
    #     cim=cim,
    #     class_am=class_am,
    #     class_am_int=class_am_int,
    #     class_am_elem_count=class_am_elem_count,
    #     encode_function=encode_emg,
    #     tqdm_mode=1,
    # )

    # print("Testing re-trained model...")
    # counts, scores, accuracies = test_model(
    #     test_dataset=train_data,
    #     ortho_im=ortho_im,
    #     cim=cim,
    #     class_am=class_am_retrained,
    #     encode_function=encode_emg,
    #     starting_num_test=0,
    #     num_test=NUM_TEST,
    #     tqdm_mode=1,
    #     print_mode=1,
    # )
