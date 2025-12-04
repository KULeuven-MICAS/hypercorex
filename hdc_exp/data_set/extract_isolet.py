#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Copyright 2024 KU Leuven
Ryan Antonio <ryan.antonio@esat.kuleuven.be>

Description:
Use this program just to extract the samples from the HDNA
"""

import os
from tqdm import tqdm
from collections import defaultdict
from ucimlrepo import fetch_ucirepo


def scale_to_255(value):
    if value < -1 or value > 1:
        raise ValueError("Input must be within [-1, 1]")

    scaled = int(((value + 1) / 2) * 255)
    return scaled


# fetch dataset
isolet = fetch_ucirepo(id=54)

# data (as pandas dataframes)
X = isolet.data.features
y = isolet.data.targets

# make sure to make the directory
output_dir = "./isolet_recog/"
os.makedirs(output_dir, exist_ok=True)

isolet_counts = defaultdict(int)
isolet_files = {
    d: open(os.path.join(output_dir, f"uint8_isolet_{d}.txt"), "w") for d in range(26)
}


# Iterate through the samples
for i in tqdm(range(len(y))):
    # Get vector list
    X_vector = X.iloc[i].to_numpy()
    X_vector_list = []
    for j in range(len(X_vector)):
        X_vector_list.append(scale_to_255(X_vector[j]))
    isolet_str = " ".join(map(str, X_vector_list))
    # Get target class
    y_class = int(y["class"].iloc[i]) - 1
    # Save vector to appropriate entry
    isolet_files[y_class].write(f"{isolet_str}\n")

for f in isolet_files.values():
    f.close()
