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
    train_ensemble_model,
    test_model,
    test_ensemble_model,
    gen_empty_hv,
    gen_orthogonal_im,
    bind_hv,
    binarize_hv,
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
    NUM_TOT_IM = 1024
    NUM_PER_IM_BANK = 128
    NGRAM = 4
    USE_CA90_IM = False
    EXTRACT_DATA = True

    NUM_CLASSES = 10
    NUM_TRAIN = 999
    NUM_RETRAIN = NUM_TRAIN
    NUM_TEST = 1000
    NUM_ENSEMBLE = 16

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

    print("Generating ortho_im data...")
    ensemble_ortho_im = dict()
    for i in range(NUM_ENSEMBLE):
        if i == 0:
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
            ensemble_ortho_im[i] = ortho_im
        else:
            ensemble_ortho_im[i] = ortho_im[i:]

    print("Training ensemble model...")
    ensemble_am = train_ensemble_model(
        train_dataset=train_data,
        num_train=NUM_TRAIN,
        num_ensemble=NUM_ENSEMBLE,
        ensemble_ortho_im=ensemble_ortho_im,
        cim=None,
        encode_function=encode_digit,
        tqdm_mode=1,
    )

    print("Making prediction sets")
    class_predict_set = test_ensemble_model(
        test_data=test_data,
        ensemble_am=ensemble_am,
        ensemble_ortho_im=ensemble_ortho_im,
        num_ensemble=NUM_ENSEMBLE,
        num_test=NUM_TEST,
        encode_function=encode_digit,
    )

    enesemble_accuracy = 0
    for i in range(NUM_CLASSES):
        enesemble_accuracy += class_predict_set[i].count(i)
    enesemble_accuracy = enesemble_accuracy / (NUM_TEST * NUM_CLASSES)
    print(f"ensemble acc: {enesemble_accuracy}")

    print("Testing model for 512 only")
    counts, scores, accuracies = test_model(
        test_dataset=train_data,
        ortho_im=ensemble_ortho_im[0],
        cim=None,
        class_am=ensemble_am[0],
        encode_function=encode_digit,
        staring_num_test=0,
        num_test=NUM_TEST,
        tqdm_mode=0,
        print_mode=1,
    )
