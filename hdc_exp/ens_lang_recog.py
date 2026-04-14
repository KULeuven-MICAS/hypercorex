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
    train_ensemble_model,
    test_model,
    test_ensemble_model,
    gen_empty_hv,
    gen_orthogonal_im,
    circ_perm_hv,
    bind_hv,
    binarize_hv,
)

TRAINING_URL = "https://github.com/KULeuven-MICAS/hypercorex/releases/download/ds_hdc_lang_recog_v.0.0.1/lang_recog_training.tar.gz"
TESTING_URL = "https://github.com/KULeuven-MICAS/hypercorex/releases/download/ds_hdc_lang_recog_v.0.0.1/lang_recog_testing.tar.gz"
TRAINING_DIR = "training_texts/"
TESTING_DIR = "testing_compressed_texts/"
DATA_DIR = "data_set/lang_recog"

LANG_LIST = {
    0: "bul",
    1: "ces",
    2: "dan",
    3: "nld",
    4: "deu",
    5: "eng",
    6: "est",
    7: "fin",
    8: "fra",
    9: "ell",
    10: "hun",
    11: "ita",
    12: "lav",
    13: "lit",
    14: "pol",
    15: "por",
    16: "ron",
    17: "slk",
    18: "slv",
    19: "spa",
    20: "swe",
}

CHAR_MAP = {
    "a": 0,
    "b": 1,
    "c": 2,
    "d": 3,
    "e": 4,
    "f": 5,
    "g": 6,
    "h": 7,
    "i": 8,
    "j": 9,
    "k": 10,
    "l": 11,
    "m": 12,
    "n": 13,
    "o": 14,
    "p": 15,
    "q": 16,
    "r": 17,
    "s": 18,
    "t": 19,
    "u": 20,
    "v": 21,
    "w": 22,
    "x": 23,
    "y": 24,
    "z": 25,
    " ": 26,  # Space character
}


def extract_lang_dataset(read_file):
    # Extract file to be tested
    text_lines = []
    with open(read_file, "r") as rf:
        for line in rf:
            line = line.strip()
            text_lines.append(line)
    rf.close()
    return text_lines


def encode_lang(line, ortho_im, cim):
    # Parameters
    ngram_count = 4
    hv_dim = len(ortho_im[0])

    # Initializers
    encoded_line = gen_empty_hv(hv_dim)
    threshold_counter = 0

    # Cycle through the entire line
    for char in range(len(line) - ngram_count):
        # Initialize encoded ngram
        encoded_ngram = gen_empty_hv(hv_dim)

        # Grab the ngram
        for ngram in range(ngram_count):
            # Create n-gram by circularly permuting the character
            get_char = line[char + ngram]
            if get_char not in CHAR_MAP:
                # If character is not in CHAR_MAP, skip it
                continue
            # Create character HV
            char_hv = ortho_im[CHAR_MAP[line[char + ngram]]]
            # Permute it
            char_ngram = circ_perm_hv(char_hv, ngram)
            # Bind it nicely
            encoded_ngram = bind_hv(encoded_ngram, char_ngram)

        # Bundle the ngram
        encoded_line += encoded_ngram
        threshold_counter += 1

    # Binarize the encoded line
    threshold = threshold_counter / 2
    encoded_line = binarize_hv(encoded_line, threshold, "binary")

    return encoded_line


if __name__ == "__main__":
    # Download and extract the training dataset
    SEED_DIM = 32
    HV_DIM = 512
    NUM_TOT_IM = 1024
    NUM_PER_IM_BANK = 128
    NGRAM = 4
    USE_CA90_IM = False
    EXTRACT_DATA = True

    NUM_CLASSES = 21
    NUM_TRAIN = 999
    NUM_RETRAIN = NUM_TRAIN
    NUM_TEST = 999
    NUM_ENSEMBLE = 16

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
        extract_git_dataset(TRAINING_URL, DATA_DIR)
        extract_git_dataset(TESTING_URL, DATA_DIR)

    print("Extracting data...")
    training_dir = f"{DATA_DIR}/{TRAINING_DIR}"
    train_data = dict()

    for lang in LANG_LIST:
        read_file = training_dir + LANG_LIST[lang] + ".txt"
        train_data[lang] = extract_lang_dataset(read_file)

    testing_dir = f"{DATA_DIR}/{TESTING_DIR}"
    test_data = dict()

    for lang in LANG_LIST:
        read_file = testing_dir + LANG_LIST[lang] + "_test.txt"
        test_data[lang] = extract_lang_dataset(read_file)

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
        encode_function=encode_lang,
        tqdm_mode=1,
    )

    print("Making prediction sets")
    class_predict_set = test_ensemble_model(
        test_data=test_data,
        ensemble_am=ensemble_am,
        ensemble_ortho_im=ensemble_ortho_im,
        cim=None,
        num_ensemble=NUM_ENSEMBLE,
        num_test=NUM_TEST,
        encode_function=encode_lang,
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
        encode_function=encode_lang,
        staring_num_test=0,
        num_test=NUM_TEST,
        tqdm_mode=0,
        print_mode=1,
    )
