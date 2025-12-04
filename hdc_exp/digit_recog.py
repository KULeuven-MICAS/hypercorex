#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Copyright 2025 KU Leuven
Ryan Antonio <ryan.antonio@esat.kuleuven.be>

Description:
This program implements the MNIST classification
task using Hyperdimensional Computing (HDC).
"""

from hdc_util import (
    extract_git_dataset,
    load_dataset,
    train_model,
    test_model,
    retrain_model,
    gen_empty_hv,
    gen_orthogonal_im,
    expand_im,
    bind_hv,
    binarize_hv,
    gen_ca90_im_set,
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
        pixel_val_hv = ortho_im[num_features + image[pixel]]
        pixel_loc_hv = ortho_im[pixel]
        pixel_val_loc_hv = bind_hv(pixel_val_hv, pixel_loc_hv, hv_type="binary")
        encoded_image += pixel_val_loc_hv

    # Binarize the encoded image
    encoded_image = binarize_hv(encoded_image, threshold, "binary")

    return encoded_image


if __name__ == "__main__":
    SEED_DIM = 32
    HV_DIM = 512
    ENABLE_HV_EXPANSION = True
    HV_DIM_EXPANSION = 16
    NUM_TOT_IM = 1024
    NUM_PER_IM_BANK = 128
    NGRAM = 4
    USE_CA90_IM = True
    EXTRACT_DATA = True

    NUM_CLASSES = 10
    NUM_TRAIN = 999
    NUM_RETRAIN = NUM_TRAIN
    NUM_TEST = 1000

    NUM_FEATURES = 28 * 28 - 1

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
        # Generate orthogonal images using the specified parameters
        ortho_im = gen_orthogonal_im(
            num_hv=NUM_TOT_IM,
            hv_dim=HV_DIM,
            p_dense=0.5,
            hv_seed=0,
            permute_base=1,
            hv_type="binary",
            im_type="random",
        )

    if ENABLE_HV_EXPANSION:
        ortho_im = expand_im(ortho_im, HV_DIM_EXPANSION)

    print("Extracting data...")
    train_data = dict()
    for num_class in range(NUM_CLASSES):
        # Training dataset
        read_file = f"{DATA_DIR}/bin_mnist_{num_class}.txt"
        train_data[num_class] = load_dataset(read_file)

    # For simplicity use both train data
    test_data = dict()
    for num_class in range(NUM_CLASSES):
        # Training dataset
        read_file = f"{DATA_DIR}/bin_mnist_{num_class}.txt"
        test_data[num_class] = load_dataset(read_file)

    print("Training model...")
    class_am, class_am_int, class_am_elem_count = train_model(
        train_dataset=train_data,
        num_train=NUM_TRAIN,
        ortho_im=ortho_im,
        cim=None,
        encode_function=encode_digit,
        tqdm_mode=1,
    )

    print("Testing model...")
    counts, scores, accuracies = test_model(
        test_dataset=train_data,
        ortho_im=ortho_im,
        cim=None,
        class_am=class_am,
        encode_function=encode_digit,
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
        cim=None,
        class_am=class_am,
        class_am_int=class_am_int,
        class_am_elem_count=class_am_elem_count,
        encode_function=encode_digit,
        tqdm_mode=1,
    )

    print("Testing re-trained model...")
    counts, scores, accuracies = test_model(
        test_dataset=train_data,
        ortho_im=ortho_im,
        cim=None,
        class_am=class_am_retrained,
        encode_function=encode_digit,
        staring_num_test=0,
        num_test=NUM_TEST,
        tqdm_mode=1,
        print_mode=1,
    )
