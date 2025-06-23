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
    gen_empty_hv,
    gen_orthogonal_im,
    bind_hv,
    binarize_hv,
    prediction_idx,
    gen_ca90_im_set,
    gen_cim,
)
from tqdm import tqdm

DATA_URL = "https://github.com/KULeuven-MICAS/hypercorex/releases/download/ds_hdc_ucihar_recog_v0.0.1/ucihar_recog.tar.gz"
DATA_SET_DIR = "data_set/"
DATA_TRAIN_DIR = f"{DATA_SET_DIR}ucihar_recog/train"
DATA_TEST_DIR = f"{DATA_SET_DIR}ucihar_recog/test"


# Convert from one uint level to another
def uint_convert_level(in_data, dst_levels):
    # Scale the input value
    return in_data // dst_levels


def encode_sample(sample, ortho_im, cim, num_features):
    # Encode sample
    hv_dim = len(ortho_im[0])
    encoded_sample = gen_empty_hv(hv_dim)
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


def train_ucihar_recog_model(
    ortho_im, cim, val_levels, training_dir, num_classes, num_train, num_features
):
    hv_dim = len(ortho_im[0])
    train_threshold = num_train / 2

    class_am = dict()
    class_am_int = dict()
    class_am_elem_count = dict()

    for lang in range(num_classes):
        class_am[lang] = gen_empty_hv(hv_dim)

    for ucihar in range(num_classes):
        # Training dataset
        read_file = f"{training_dir}/uint8_ucihar_train_{ucihar}.txt"

        sample_lines = []
        with open(read_file, "r") as rf:
            for line in rf:
                line = line.strip().split()
                int_line = [uint_convert_level(int(x), val_levels) for x in line]
                sample_lines.append(int_line)

        class_hv = gen_empty_hv(hv_dim)

        for i in tqdm(range(NUM_TRAIN), desc=f"Training ucihar: {ucihar}"):
            class_hv += encode_sample(sample_lines[i], ortho_im, cim, num_features)

        # Save non-binarized AM
        class_am_int[ucihar] = class_hv

        # Save binarized AM
        class_hv = binarize_hv(class_hv, train_threshold, "binary")
        class_am[ucihar] = class_hv

        # Save threshold list
        class_am_elem_count[ucihar] = num_train

    return class_am, class_am_int, class_am_elem_count


def retrain_ucihar_recog_model(
    class_am,
    class_am_int,
    class_am_elem_count,
    ortho_im,
    cim,
    val_levels,
    training_dir,
    num_classes,
    num_retrain,
    num_features,
    staring_num_test,
):
    for ucihar in range(num_classes):
        # Retraining dataset
        read_file = f"{training_dir}/uint8_ucihar_train_{ucihar}.txt"

        sample_lines = []
        with open(read_file, "r") as rf:
            for line in rf:
                line = line.strip().split()
                int_line = [uint_convert_level(int(x), val_levels) for x in line]
                sample_lines.append(int_line)

        for i in tqdm(range(num_retrain), desc=f"Retraining ucihar: {ucihar}"):
            # Get encodede sample
            encoded_line = encode_sample(
                sample_lines[staring_num_test + i], ortho_im, cim, num_features
            )

            # Get prediction
            prediction = prediction_idx(class_am, encoded_line, hv_type="binary")

            # Update AM for every incorrect prediction
            if prediction != ucihar:
                # Update the class AM
                class_am_int[prediction] -= encoded_line

                class_am_int[ucihar] += encoded_line

                # Update the threshold
                class_am_elem_count[prediction] -= 1
                class_am_elem_count[ucihar] += 1

    # After updating rebinarize the AM
    for ucihar in range(num_classes):
        # Save binarized AM
        threshold = class_am_elem_count[ucihar] / 2
        class_am[ucihar] = binarize_hv(class_am_int[ucihar], threshold, "binary")

    return class_am, class_am_int, class_am_elem_count


def test_ucihar_recog_model(
    class_am,
    ortho_im,
    cim,
    val_levels,
    testing_dir,
    num_classes,
    num_features,
    staring_num_test,
    num_test,
):
    overall_count = 0
    overall_score = 0
    total_count = 0
    total_score = 0

    for ucihar in range(num_classes):
        # Training dataset
        read_file = f"{testing_dir}/uint8_ucihar_train_{ucihar}.txt"

        sample_lines = []
        with open(read_file, "r") as rf:
            for line in rf:
                line = line.strip().split()
                int_line = [uint_convert_level(int(x), val_levels) for x in line]
                # int_line = [int(x) for x in line]
                sample_lines.append(int_line)

        # Make a prediction
        for i in tqdm(range(num_test), desc=f"Testing ucihar: {ucihar}"):
            encoded_line = encode_sample(
                sample_lines[staring_num_test + i], ortho_im, cim, num_features
            )
            prediction = prediction_idx(class_am, encoded_line, hv_type="binary")
            if prediction == ucihar:
                total_score += 1
            total_count += 1

        accuracy = total_score / total_count if total_count > 0 else 0
        print(f"ucihar: {ucihar}, Accuracy: {accuracy:.2f}")

        overall_score += total_score
        overall_count += total_count

    overall_accuracy = overall_score / overall_count if overall_count > 0 else 0
    print(f"Overall Accuracy: {overall_accuracy:.2f}")

    return


if __name__ == "__main__":
    SEED_DIM = 32
    HV_DIM = 10000
    NUM_TOT_IM = 1024
    NUM_PER_IM_BANK = 128
    NGRAM = 4
    USE_CA90_IM = False
    EXTRACT_DATA = True

    VAL_LEVELS = 21
    NUM_CLASSES = 6
    NUM_TRAIN = 951
    NUM_RETRAIN = NUM_TRAIN
    NUM_TEST = 300

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

    cim = gen_cim(
        hv_dim=HV_DIM,
        seed_size=32,
        num_hv=VAL_LEVELS,
        base_seed=CIM_BASE_SEED,
        gen_seed=False,
        max_ortho=False,
        im_type="random",
        hv_type="binary",
        debug_info=False,
    )

    # Training
    class_am, class_am_int, class_am_elem_count = train_ucihar_recog_model(
        ortho_im, cim, VAL_LEVELS, DATA_TRAIN_DIR, NUM_CLASSES, NUM_TRAIN, NUM_FEATURES
    )
    # Testing
    test_ucihar_recog_model(
        class_am,
        ortho_im,
        cim,
        VAL_LEVELS,
        DATA_TRAIN_DIR,
        NUM_CLASSES,
        NUM_FEATURES,
        0,
        NUM_TEST,
    )

    # Retraining
    class_am, class_am_int, class_am_elem_count = retrain_ucihar_recog_model(
        class_am,
        class_am_int,
        class_am_elem_count,
        ortho_im,
        cim,
        VAL_LEVELS,
        DATA_TRAIN_DIR,
        NUM_CLASSES,
        NUM_RETRAIN,
        NUM_FEATURES,
        0,
    )

    # Testing
    test_ucihar_recog_model(
        class_am,
        ortho_im,
        cim,
        VAL_LEVELS,
        DATA_TRAIN_DIR,
        NUM_CLASSES,
        NUM_FEATURES,
        0,
        NUM_TEST,
    )
