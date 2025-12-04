#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Copyright 2025 KU Leuven
Ryan Antonio <ryan.antonio@esat.kuleuven.be>

Description:
This program implements the UCIHAR classification
using Hyperdimensional Computing (HDC) techniques.
"""

from hdc_util import (
    extract_git_dataset,
    load_dataset,
    convert_levels,
    train_model,
    test_model,
    retrain_model,
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

DATA_URL = "https://github.com/KULeuven-MICAS/hypercorex/releases/download/ds_hdc_ucihar_recog_v0.0.1/ucihar_recog.tar.gz"
DATA_SET_DIR = "data_set/"
DATA_TRAIN_DIR = f"{DATA_SET_DIR}ucihar_recog/train"
DATA_TEST_DIR = f"{DATA_SET_DIR}ucihar_recog/test"


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
    SEED_DIM = 32
    HV_DIM = 512
    ENABLE_HV_EXPANSION = True
    HV_DIM_EXPANSION = 16
    NUM_TOT_IM = 1024
    NUM_PER_IM_BANK = 128
    NGRAM = 4
    USE_CA90_IM = True
    USE_CA90_CIM = True
    EXTRACT_DATA = True

    VAL_LEVELS = 5
    NUM_CLASSES = 6
    NUM_TRAIN = 511
    NUM_RETRAIN = NUM_TRAIN
    NUM_TEST = 400

    NUM_FEATURES = 561

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

    if EXTRACT_DATA:
        extract_git_dataset(DATA_URL, DATA_SET_DIR)

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
    train_data = dict()
    for num_class in range(NUM_CLASSES):
        # Training dataset
        read_file = f"{DATA_TRAIN_DIR}/uint8_ucihar_train_{num_class}.txt"
        train_data[num_class] = load_dataset(read_file)

    test_data = dict()
    for num_class in range(NUM_CLASSES):
        # Training dataset
        read_file = f"{DATA_TEST_DIR}/uint8_ucihar_test_{num_class}.txt"
        test_data[num_class] = load_dataset(read_file)

    print("Converting data...")
    if USE_CA90_CIM:
        train_data = convert_levels(train_data, VAL_LEVELS, VAL_LEVELS - 1)
        test_data = convert_levels(test_data, VAL_LEVELS, VAL_LEVELS - 1)
    else:
        train_data = convert_levels(train_data, VAL_LEVELS)
        test_data = convert_levels(test_data, VAL_LEVELS)

    print("Training model...")
    class_am, class_am_int, class_am_elem_count = train_model(
        train_dataset=train_data,
        num_train=NUM_TRAIN,
        ortho_im=ortho_im,
        cim=cim,
        encode_function=encode_ucihar,
        tqdm_mode=1,
    )

    print("Testing model...")
    counts, scores, accuracies = test_model(
        test_dataset=train_data,
        ortho_im=ortho_im,
        cim=cim,
        class_am=class_am,
        encode_function=encode_ucihar,
        staring_num_test=0,
        num_test=NUM_TEST,
        tqdm_mode=1,
        print_mode=1,
    )

    print("Retraining model...")
    (
        class_am_retrained,
        class_am_int_retrained,
        class_am_elem_count_retrained,
    ) = retrain_model(
        retrain_dataset=train_data,
        num_retrain=NUM_RETRAIN,
        ortho_im=ortho_im,
        cim=cim,
        class_am=class_am,
        class_am_int=class_am_int,
        class_am_elem_count=class_am_elem_count,
        encode_function=encode_ucihar,
        tqdm_mode=1,
    )

    print("Testing re-trained model...")
    counts, scores, accuracies = test_model(
        test_dataset=train_data,
        ortho_im=ortho_im,
        cim=cim,
        class_am=class_am_retrained,
        encode_function=encode_ucihar,
        staring_num_test=0,
        num_test=NUM_TEST,
        tqdm_mode=1,
        print_mode=1,
    )
