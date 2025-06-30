#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
  Copyright 2025 KU Leuven
  Ryan Antonio <ryan.antonio@esat.kuleuven.be>

  Description:
  This program re-implements the lang but dumps
  data for the Hemaia project
"""
import sys
import os

# Extract paths
root = os.getcwd()

hdc_util_path = root + "/../hdc_exp/"
print(hdc_util_path)
sys.path.append(hdc_util_path)

from hdc_util import (  # noqa: E402
    extract_git_dataset,
    save_am_model,
    load_am_model,
    train_model,
    test_model,
    gen_empty_hv,
    gen_square_cim,
    bind_hv,
    binarize_hv,
    circ_perm_hv,
    predict_item,
    gen_ca90_im_set,
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


# Note that the encoding here is different because we need
# to support the one that Hemaia can do
def encode_lang(line, ortho_im, cim):
    # Parameters
    ngram_count = 3
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
            char_ngram = circ_perm_hv(char_hv, ((2 - ngram) * 4))
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
    # Data paremeters
    EXTRACT_DATA = True
    TRAIN_MODEL = True
    TEST_MODEL = True
    TEST_PRUNED_MODEL = True
    SAVE_MODEL = True
    TRAINED_AM_FILEPATH = root + "/trained_am/hypx_lang_am.txt"
    TEST_SAMPLES_FILEPATH = root + "/test_samples/hypx_lang_test.txt"

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
    NUM_FEATURES = 128
    NUM_CLASSES = 21
    NUM_TRAIN = 999
    NUM_RETRAIN = NUM_TRAIN
    NUM_TEST = 999

    if EXTRACT_DATA:
        extract_git_dataset(TRAINING_URL, DATA_DIR)
        extract_git_dataset(TESTING_URL, DATA_DIR)

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

    # We need to post-process the trained data to be shortened to 64 only
    # But here, we will get 1 sample each only and regardless of prediction
    pruned_test_data = dict()
    pruned_test_data_char = dict()
    for i in range(NUM_CLASSES):
        # Get a slice
        for k in range(10):
            if len(test_data[i][k]) < NUM_FEATURES:
                continue
            else:
                vector_to_get = test_data[i][k][:NUM_FEATURES]
                vector_to_num = []
                for j in range(NUM_FEATURES):
                    vector_to_num.append(CHAR_MAP[vector_to_get[j]])
                break
        pruned_test_data[i] = vector_to_num
        pruned_test_data_char[i] = vector_to_get

    if TRAIN_MODEL:
        print("Training model...")
        class_am, _, _ = train_model(
            train_dataset=train_data,
            num_train=NUM_TRAIN,
            ortho_im=ortho_im,
            cim=cim,
            encode_function=encode_lang,
            tqdm_mode=1,
        )
    else:
        print("Loading AM model...")
        class_am = load_am_model(TRAINED_AM_FILEPATH)

    if SAVE_MODEL:
        save_am_model(TRAINED_AM_FILEPATH, class_am)

    if TEST_MODEL:
        print("Testing model...")
        counts, scores, accuracies = test_model(
            test_dataset=train_data,
            ortho_im=ortho_im,
            cim=cim,
            class_am=class_am,
            encode_function=encode_lang,
            staring_num_test=0,
            num_test=NUM_TEST,
            tqdm_mode=1,
            print_mode=1,
        )

    if TEST_PRUNED_MODEL:
        pruned_prediction_set = []
        for i in range(len(pruned_test_data)):
            prediction = predict_item(
                ortho_im,
                cim,
                class_am,
                pruned_test_data_char[i],
                encode_lang,
                hv_type="binary",
            )
            print(prediction)
            pruned_prediction_set.append(prediction)

    # Write to output
    with open(TEST_SAMPLES_FILEPATH, "w") as wf:
        for i in range(NUM_CLASSES):
            line = " ".join(map(str, pruned_test_data[i]))
            wf.write(line + "\n")
