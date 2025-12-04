#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Copyright 2024 KU Leuven
Ryan Antonio <ryan.antonio@esat.kuleuven.be>

Description:
Use this program to extract samples from the UCI HAR dataset
and save them in an uint8 format for HDC purposes.
"""

import os


def scale_to_255(value):
    if value < -1 or value > 1:
        raise ValueError("Input must be within [-1, 1]")

    scaled = int(((value + 1) / 2) * 255)
    return scaled


# make sure to make the directory
output_train_dir = "./ucihar_recog/train/"
output_test_dir = "./ucihar_recog/test/"

os.makedirs(output_train_dir, exist_ok=True)
os.makedirs(output_test_dir, exist_ok=True)


ucihar_trainX_dir = "./ucihar_dataset/train/X_train.txt"
ucihar_trainY_dir = "./ucihar_dataset/train/y_train.txt"
ucihar_testX_dir = "./ucihar_dataset/test/X_test.txt"
ucihar_testY_dir = "./ucihar_dataset/test/y_test.txt"

num_classes = 6

# First extract all data
X_train = []
Y_train = []
X_test = []
Y_test = []

with open(ucihar_trainX_dir, "r") as trXf:
    for line in trXf:
        str_line = line.strip().split()
        float_line = [scale_to_255(float(s)) for s in str_line]
        X_train.append(float_line)

with open(ucihar_trainY_dir, "r") as trYf:
    for line in trYf:
        Y_train.append(int(line.strip()))

with open(ucihar_testX_dir, "r") as tsXf:
    for line in tsXf:
        str_line = line.strip().split()
        float_line = [scale_to_255(float(s)) for s in str_line]
        X_test.append(float_line)

with open(ucihar_testY_dir, "r") as tsYf:
    for line in tsYf:
        Y_test.append(int(line.strip()))

trXf.close()
trYf.close()
tsXf.close()
tsYf.close()

# Prepare files to be written to

ucihar_train_files = {
    d: open(os.path.join(output_train_dir, f"uint8_ucihar_train_{d}.txt"), "w")
    for d in range(num_classes)
}

ucihar_test_files = {
    d: open(os.path.join(output_test_dir, f"uint8_ucihar_test_{d}.txt"), "w")
    for d in range(num_classes)
}

# Iterate through train
for i in range(len(X_train)):
    # Get vector list
    ucihar_str = " ".join(map(str, X_train[i]))
    # Get target class
    y_class = Y_train[i] - 1  # Adjust for zero-based index
    # Save vector to appropriate entry
    ucihar_train_files[y_class].write(f"{ucihar_str}\n")

# Iterate through test
for i in range(len(X_test)):
    # Get vector list
    ucihar_str = " ".join(map(str, X_test[i]))
    # Get target class
    y_class = Y_test[i] - 1  # Adjust for zero-based index
    # Save vector to appropriate entry
    ucihar_test_files[y_class].write(f"{ucihar_str}\n")

for f in ucihar_train_files.values():
    f.close()

for f in ucihar_test_files.values():
    f.close()
