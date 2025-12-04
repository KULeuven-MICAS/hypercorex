#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Copyright 2025 KU Leuven
Ryan Antonio <ryan.antonio@esat.kuleuven.be>

Description:
This program implements the language recognition
classification task using Hyperdimensional Computing (HDC).
"""

from hdc_util import (
    extract_git_dataset,
    train_model,
    test_model,
    gen_empty_hv,
    gen_orthogonal_im,
    expand_im,
    circ_perm_hv,
    bind_hv,
    binarize_hv,
    gen_ca90_im_set,
    quantize_hv,
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

# initialize global params
HV_TYPE = None
QUANT_TYPE = None

# Baseline?  (https://dl.acm.org/doi/pdf/10.1145/3558000 survey from 2023)
# 10.1109/AICAS48895.2020.9073871 -> 97.23% (10k dims, binary, hamming dist)
# 10.1109/MDAT.2017.2740839 -> 95.4% (sparse 4%, 10k dims, binary, 4-gram), 96.1% (dense, 10k dims, binary, 3-gram)
# 10.1145/2934583.2934624 -> 3-gram: 96.7% HDC (10k dims), 97.9% nearest neighbour
#                         -> 4-gram: 97.1%, 99.2%
#                         -> 5-gram: 95.0%, 99.8%
# https://redwood.berkeley.edu/wp-content/uploads/2020/08/JoshiEtAl-QI2016-language-geometry-copy.pdf  -> 3-gram 97.3%, 4-gram 97.8%, 5-gram 97.3% (10k dims)


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
            if ngram == 0:
                encoded_ngram = char_ngram
            else:
                encoded_ngram = bind_hv(encoded_ngram, char_ngram, hv_type=HV_TYPE)

        # Bundle the ngram
        encoded_line += encoded_ngram
        threshold_counter += 1

    # Binarize the encoded line
    threshold = threshold_counter / 2
    if QUANT_TYPE is not None:
        encoded_line = quantize_hv(
            encoded_line, threshold, hv_type=HV_TYPE, quant_type=QUANT_TYPE
        )
    else:
        encoded_line = binarize_hv(encoded_line, threshold, hv_type=HV_TYPE)

    return encoded_line


def main(hv_dim, hv_type, quant_type):
    # Overwrite global parameters
    global HV_DIM
    HV_DIM = hv_dim
    global HV_TYPE
    HV_TYPE = hv_type
    global QUANT_TYPE
    QUANT_TYPE = quant_type

    # Download and extract the training dataset
    SEED_DIM = 32
    # HV_DIM = 512*16
    ENABLE_HV_EXPANSION = False  # enabling this increases HV_dim by a ton, which gave the default high 90% accuracy, similar to when increasing HV_DIM with that factor directly
    HV_DIM_EXPANSION = 16
    NUM_TOT_IM = 1024
    NUM_PER_IM_BANK = 128
    # NGRAM = 4
    USE_CA90_IM = False
    EXTRACT_DATA = True

    NUM_TRAIN = 999
    # NUM_RETRAIN = NUM_TRAIN
    NUM_TEST = 999

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
            hv_type=HV_TYPE,
            im_type="random",
        )

    if ENABLE_HV_EXPANSION:
        ortho_im = expand_im(ortho_im, HV_DIM_EXPANSION)

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

    print("Training model...")
    class_am, class_am_int, class_am_elem_count = train_model(
        train_dataset=train_data,
        num_train=NUM_TRAIN,
        ortho_im=ortho_im,
        cim=None,
        encode_function=encode_lang,
        tqdm_mode=2,
        hv_type=HV_TYPE,
        quant_type=QUANT_TYPE,
    )

    print("Testing model...")
    counts, scores, accuracies, overall_accuracy = test_model(
        test_dataset=train_data,
        ortho_im=ortho_im,
        cim=None,
        class_am=class_am,
        encode_function=encode_lang,
        starting_num_test=0,
        num_test=NUM_TEST,
        tqdm_mode=2,
        print_mode=1,
        hv_type=HV_TYPE,
        quant_type=QUANT_TYPE,
    )

    return overall_accuracy


if __name__ == "__main__":
    main(hv_dim=512, hv_type="bipolar", quant_type=None)

    # print("Retraining model...")
    # (
    #     class_am_retrained,
    #     class_am_int_retrained,
    #     class_am_elem_count_retrained,
    # ) = retrain_model(
    #     retrain_dataset=train_data,
    #     num_retrain=NUM_RETRAIN,
    #     ortho_im=ortho_im,
    #     cim=None,
    #     class_am=class_am,
    #     class_am_int=class_am_int,
    #     class_am_elem_count=class_am_elem_count,
    #     encode_function=encode_lang,
    #     tqdm_mode=1,
    #     hv_type=HV_TYPE
    # )

    # print("Testing re-trained model...")
    # counts, scores, accuracies = test_model(
    #     test_dataset=train_data,
    #     ortho_im=ortho_im,
    #     cim=None,
    #     class_am=class_am_retrained,
    #     encode_function=encode_lang,
    #     starting_num_test=0,
    #     num_test=NUM_TEST,
    #     tqdm_mode=1,
    #     print_mode=1,
    # )
