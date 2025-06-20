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
    gen_empty_hv,
    gen_orthogonal_im,
    bind_hv,
    binarize_hv,
    prediction_idx,
    gen_ca90_im_set,
)
from tqdm import tqdm


DATA_URL = "https://github.com/KULeuven-MICAS/hypercorex/releases/download/ds_hdc_digit_recog_v.0.0.1/digit_recog.tar.gz"
DATA_SET_DIR = "data_set"
DATA_DIR = f"{DATA_SET_DIR}/digit_recog"


def encode_image(image, ortho_im, num_features):
    # Encode image
    hv_dim = len(ortho_im[0])
    encoded_image = gen_empty_hv(hv_dim)
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


def train_digit_recog_model(ortho_im, training_dir, num_train, num_features):
    hv_dim = len(ortho_im[0])
    train_threshold = num_train / 2

    class_am = dict()
    class_am_int = dict()
    class_am_elem_count = dict()

    for lang in range(10):
        class_am[lang] = gen_empty_hv(hv_dim)

    for digit in range(10):
        # Training dataset
        read_file = f"{training_dir}/bin_mnist_{digit}.txt"

        image_lines = []
        with open(read_file, "r") as rf:
            for line in rf:
                line = line.strip().split()
                int_line = [int(x) for x in line]
                image_lines.append(int_line)

        class_hv = gen_empty_hv(len(ortho_im[0]))

        for i in tqdm(range(NUM_TRAIN), desc=f"Training digit: {digit}"):
            class_hv += encode_image(image_lines[i], ortho_im, num_features)

        # Save non-binarized AM
        class_am_int[digit] = class_hv

        # Save binarized AM
        class_hv = binarize_hv(class_hv, train_threshold, "binary")
        class_am[digit] = class_hv

        # Save threshold list
        class_am_elem_count[digit] = num_train

    return class_am, class_am_int, class_am_elem_count


def retrain_digit_recog_model(
    class_am,
    class_am_int,
    class_am_elem_count,
    ortho_im,
    training_dir,
    num_retrain,
    num_features,
    staring_num_test,
):
    for digit in range(10):
        # Retraining dataset
        read_file = f"{training_dir}/bin_mnist_{digit}.txt"

        # Open images again
        image_lines = []
        with open(read_file, "r") as rf:
            for line in rf:
                line = line.strip().split()
                int_line = [int(x) for x in line]
                image_lines.append(int_line)

        for i in tqdm(range(num_retrain), desc=f"Retraining digit: {digit}"):
            # Get encodede image
            encoded_line = encode_image(
                image_lines[staring_num_test + i], ortho_im, num_features
            )
            # Get prediction
            prediction = prediction_idx(class_am, encoded_line, hv_type="binary")

            # Update AM for every incorrect prediction
            if prediction != digit:
                # Update the class AM
                class_am_int[prediction] -= encoded_line
                class_am_int[digit] += encoded_line

                # Update the threshold
                class_am_elem_count[prediction] -= 1
                class_am_elem_count[digit] += 1

    # After updating rebinarize the AM
    for digit in range(10):
        # Save binarized AM
        threshold = class_am_elem_count[digit] / 2
        class_am[digit] = binarize_hv(class_am_int[digit], threshold, "binary")

    return class_am, class_am_int, class_am_elem_count


def test_digit_recog_model(
    class_am, ortho_im, testing_dir, num_features, staring_num_test, num_test
):
    overall_count = 0
    overall_score = 0
    total_count = 0
    total_score = 0

    for digit in range(10):
        # Training dataset
        read_file = f"{testing_dir}/bin_mnist_{digit}.txt"

        image_lines = []
        with open(read_file, "r") as rf:
            for line in rf:
                line = line.strip().split()
                int_line = [int(x) for x in line]
                image_lines.append(int_line)

        # Make a prediction
        for i in tqdm(range(num_test), desc=f"Testing digit: {digit}"):
            encoded_line = encode_image(
                image_lines[staring_num_test + i], ortho_im, num_features
            )
            prediction = prediction_idx(class_am, encoded_line, hv_type="binary")
            if prediction == digit:
                total_score += 1
            total_count += 1

        accuracy = total_score / total_count if total_count > 0 else 0
        print(f"Digit: {digit}, Accuracy: {accuracy:.2f}")

        overall_score += total_score
        overall_count += total_count

    overall_accuracy = overall_score / overall_count if overall_count > 0 else 0
    print(f"Overall Accuracy: {overall_accuracy:.2f}")

    return


if __name__ == "__main__":
    SEED_DIM = 32
    HV_DIM = 512
    NUM_TOT_IM = 1024
    NUM_PER_IM_BANK = 128
    NGRAM = 4
    USE_CA90_IM = True
    EXTRACT_DATA = True

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

    # Training
    class_am, class_am_int, class_am_elem_count = train_digit_recog_model(
        ortho_im, DATA_DIR, NUM_TRAIN, NUM_FEATURES
    )

    # Testing
    test_digit_recog_model(
        class_am, ortho_im, DATA_DIR, NUM_FEATURES, NUM_TRAIN, NUM_TEST
    )

    # Retraining
    class_am, class_am_int, class_am_elem_count = retrain_digit_recog_model(
        class_am,
        class_am_int,
        class_am_elem_count,
        ortho_im,
        DATA_DIR,
        NUM_RETRAIN,
        NUM_FEATURES,
        0,
    )

    # Testing
    test_digit_recog_model(
        class_am, ortho_im, DATA_DIR, NUM_FEATURES, NUM_TRAIN, NUM_TEST
    )
