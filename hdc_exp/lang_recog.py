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
    gen_empty_hv,
    gen_orthogonal_im,
    circ_perm_hv,
    bind_hv,
    binarize_hv,
    prediction_idx,
    gen_ca90_im_set,
)
from tqdm import tqdm
import requests
import tarfile
import io


TRAINING_URL = "https://github.com/KULeuven-MICAS/hypercorex/releases/download/ds_hdc_lang_recog_v.0.0.1/lang_recog_training.tar.gz"
TESTING_URL = "https://github.com/KULeuven-MICAS/hypercorex/releases/download/ds_hdc_lang_recog_v.0.0.1/lang_recog_testing.tar.gz"
TRAINING_DIR = "training_texts/"
TESTING_DIR = "testing_compressed_texts/"

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


def extract_lang_recog_dataset(url, target_dir):
    # Extract the dataset
    response = requests.get(url, stream=True)
    response.raise_for_status()  # Raise an error on bad status

    # Extract the data sets
    with tarfile.open(fileobj=io.BytesIO(response.content), mode="r:gz") as tar:
        # Extract all files to a directory
        tar.extractall(path=target_dir)
    return


def encode_line(line, ortho_im, ngram=4):
    # Encode line
    hv_dim = len(ortho_im[0])
    encoded_line = gen_empty_hv(hv_dim)
    threshold_counter = 0

    # Cycle through the entire line
    for char in range(len(line) - NGRAM):
        encoded_ngram = gen_empty_hv(hv_dim)
        # Grab the ngram
        for ngram in range(NGRAM):
            # Create n-gram by circularly permuting the character
            get_char = line[char + ngram]
            if get_char not in CHAR_MAP:
                # If character is not in CHAR_MAP, skip it
                continue
            char_hv = ortho_im[CHAR_MAP[line[char + ngram]]]
            char_ngram = circ_perm_hv(char_hv, ngram)
            encoded_ngram = bind_hv(encoded_ngram, char_ngram)

        # Bundle the ngram
        encoded_line += encoded_ngram
        threshold_counter += 1

    # Binarize the encoded line
    threshold = threshold_counter / 2
    encoded_line = binarize_hv(encoded_line, threshold, "binary")

    return encoded_line


def train_lang_recog_model(ortho_im, training_dir, num_train, ngram=4):
    hv_dim = len(ortho_im[0])
    class_am = dict()
    for lang in LANG_LIST:
        class_am[lang] = gen_empty_hv(hv_dim)

    for lang in LANG_LIST:
        # Training dataset
        read_file = training_dir + LANG_LIST[lang] + ".txt"

        text_lines = []
        with open(read_file, "r") as rf:
            for line in rf:
                line = line.strip()
                text_lines.append(line)

        # Class HV
        class_hv = gen_empty_hv(hv_dim)
        # len(text_lines)
        for i in tqdm(range(num_train), desc=f"Encoding training data: {read_file}"):
            encoded_line = encode_line(text_lines[i], ortho_im, ngram=4)

            # Bundle class HV
            class_hv += encoded_line

        # threshold = len(text_lines) / 2
        threshold = num_train / 2  # Use a fixed threshold for demonstration
        class_hv = binarize_hv(class_hv, threshold, "binary")
        class_am[lang] = class_hv

    return class_am


def test_lang_recog_model(class_am, ortho_im, testing_dir, num_test, ngram=4):
    overall_count = 0
    overall_score = 0
    total_count = 0
    total_score = 0

    for lang in LANG_LIST:
        read_file = testing_dir + LANG_LIST[lang] + "_test.txt"

        # Extract file to be tested
        text_lines = []
        with open(read_file, "r") as rf:
            for line in rf:
                line = line.strip()
                text_lines.append(line)

        # Make a prediction
        for i in tqdm(range(num_test), desc=f"Testing data: {read_file}"):
            encoded_line = encode_line(text_lines[i], ortho_im, ngram=4)
            prediction = prediction_idx(class_am, encoded_line, hv_type="binary")
            if prediction == lang:
                total_score += 1
            total_count += 1

        accuracy = total_score / total_count if total_count > 0 else 0
        print(f"Language: {lang}, Accuracy: {accuracy:.2f}")

        overall_score += total_score
        overall_count += total_count

    overall_accuracy = overall_score / overall_count if overall_count > 0 else 0
    print(f"Overall Accuracy: {overall_accuracy:.2f}")

    return


if __name__ == "__main__":
    # Download and extract the training dataset
    SEED_DIM = 32
    HV_DIM = 4096
    NUM_TOT_IM = 1024
    NUM_PER_IM_BANK = 128
    NGRAM = 4
    USE_CA90_IM = False
    EXTRACT_DATA = False

    TAREGET_DIR = "extracted_datasets"

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
        extract_lang_recog_dataset(TRAINING_URL, TAREGET_DIR)
        extract_lang_recog_dataset(TESTING_URL, TAREGET_DIR)

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

    training_dir = TAREGET_DIR + "/" + TRAINING_DIR
    class_am = train_lang_recog_model(ortho_im, training_dir, num_train=1000, ngram=4)

    # Training dataset
    testing_dir = TAREGET_DIR + "/" + TESTING_DIR
    test_lang_recog_model(class_am, ortho_im, testing_dir, num_test=100, ngram=4)
