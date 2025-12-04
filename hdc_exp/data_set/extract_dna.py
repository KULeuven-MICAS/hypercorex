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


def convert_dna_to_num(input_list):
    new_list = []
    for i in range(len(input_list)):
        new_list.append(feature_dict[input_list[i]])
    return new_list


# fetch dataset
dna = fetch_ucirepo(id=69)

# data (as pandas dataframes)
X = dna.data.features
y = dna.data.targets

# make sure to make the directory
output_dir = "./dna_recog/"
os.makedirs(output_dir, exist_ok=True)

dna_counts = defaultdict(int)
dna_files = {d: open(os.path.join(output_dir, f"dna_{d}.txt"), "w") for d in range(3)}

num_items = len(y["class"])

class_dict = {"EI": 0, "IE": 1, "N": 2}

feature_dict = {
    "A": 0,
    "C": 1,
    "G": 2,
    "T": 3,
    "N": 4,
    "D": 5,
    "R": 6,
    "S": 7,
}

num_features = len(X.iloc[0])

X_vector = X.iloc[0]

for i in tqdm(range(len(y))):
    # Get vector list
    X_vector = convert_dna_to_num(list(X.iloc[i]))
    dna_str = " ".join(map(str, X_vector))
    # Get target class
    y_class = class_dict[y["class"].iloc[i]]
    # Save vector to appropriate entry
    dna_files[y_class].write(f"{dna_str}\n")

for f in dna_files.values():
    f.close()
