#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Copyright 2024 KU Leuven
Ryan Antonio <ryan.antonio@esat.kuleuven.be>

Description:
Use this program just to extract a few samples of the MNIST dataset
However, after extraction we will save it as released assets
"""

import os
import torch
from torchvision import datasets, transforms
from collections import defaultdict

# Parameters
samples_per_digit = 3000
output_dir = "./digit_recog/"
os.makedirs(output_dir, exist_ok=True)

# Load MNIST training data
mnist = datasets.MNIST(
    root="./digit_recog/mnist_data",
    train=True,
    download=True,
    transform=transforms.ToTensor(),
)

# Initialize counters and file handlers
digit_counts = defaultdict(int)
digit_files = {
    d: open(os.path.join(output_dir, f"bin_mnist_{d}.txt"), "w") for d in range(10)
}

# Collect and write samples
for img, label in mnist:
    if digit_counts[label] < samples_per_digit:
        binary_img = (img > 0).to(torch.uint8).view(-1).tolist()
        pixel_str = " ".join(map(str, binary_img))
        digit_files[label].write(f"{pixel_str}\n")
        digit_counts[label] += 1

    if all(digit_counts[d] >= samples_per_digit for d in range(10)):
        break

# Close files
for f in digit_files.values():
    f.close()

print(f"Saved 3000 samples per digit to '{output_dir}' directory.")
