#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
    Copyright 2024 KU Leuven
    Ryan Antonio <ryan.antonio@esat.kuleuven.be>
    
    Description:
    These contain useful functions for testing HDC activities
"""


import numpy as np


"""
    General functions

"""


def extract_dataset(file_path):
    # Initialize empty data set array
    dataset = []

    with open(file_path, "r") as file:
        lines = file.readlines()

        for line in lines:
            dataset.append(line.strip())

    return dataset


"""
    Hypervector functions
    
    gen_ri_hv:
        - used for generating random HVs
        - it uses random indexing mechanism
        - arguments:
            - hv_dim: dimension size of hypervector
            - p_dense: density of hypervector
            - hv_type: element hv_type
        
    bind_hv:
        - for binding two hvs
        - arguments:
            - hv_a, hv_b: two input hypervectors
            - hv_type: element hv_type, if bipolar we do haddamard multiplcation
            - density: hv_type of density binding
    
    circ_perm_hv:
        - for circular permutations
        - arguments:
            - hv_a: hypervector to permute
            - permute_amt: number of circular permutes
    
    binarize_hv:
        - for binarizing summed hypervectors
        - arguments:
            - hv_a: hypervecetor to binarize
            - threshold: threshold to set 1s for binary hv_type
            - hv_type: hv_type of hypervector, if bipolar we threshold at 0

"""


# Generate empty HV
def gen_empty_hv(hv_dim):
    return np.zeros(hv_dim)


# Generate using random indexing style
def gen_ri_hv(hv_dim, p_dense, hv_type="binary"):
    # Generate a list of random integers
    random_list = np.arange(hv_dim)

    # Permute list
    np.random.shuffle(random_list)

    # Determine threshold
    threshold = np.floor(hv_dim * p_dense)

    # Binarize depending on hv_type
    if hv_type == "bipolar":
        random_list = np.where(random_list >= threshold, 1, -1)
    else:
        random_list = np.where(random_list >= threshold, 1, 0)

    return random_list


# Binding dense functions
def bind_hv(hv_a, hv_b, hv_type="binary", density="dense"):
    # If bipolar we do multiplication
    # otherwise we do bit-wise XOR
    if hv_type == "bipolar":
        return np.multiply(hv_a, hv_b)
    else:
        return np.bitwise_xor(hv_a, hv_b)


# Circular permutations
def circ_perm_hv(hv_a, permute_amt):
    return np.roll(hv_a, permute_amt)


# Binarize hypervector
def binarize_hv(hv_a, threshold, hv_type="binary"):
    # Binarize depending on hv_type
    # If it's binary use a threshold for this
    if hv_type == "bipolar":
        hv_a = np.where(hv_a >= 0, 1, -1)
    else:
        hv_a = np.where(hv_a >= threshold, 1, 0)

    return hv_a


# Normalized distance calculation
# the output range is from 0 to 1
# where 1 is the highest similarity
def norm_dist_hv(hv_a, hv_b, hv_type="binary"):
    # If binary we do hamming distance,
    # else we do cosine similarity
    if hv_type == "bipolar":
        hv_dot = np.dot(hv_a, hv_b)
        norm_a = np.linalg.norm(hv_a)
        norm_b = np.linalg.norm(hv_b)
        dist = hv_dot / (norm_a * norm_b)
    else:
        ham_dist = np.sum(np.bitwise_xor(hv_a, hv_b))
        dist = 1 - (ham_dist / hv_a.size)

    return dist


"""
    Functions for generating item memories
    
    gen_orthogonal_im:
        - generates a set of HVs with orthogonal mapping
        - arguments:
            - num_hv: number of hypervectors to generate
            - hv_dim: dimension of each hypervector
            - p_dense: the density of each hypervector
            - hv_type: type of hypervector
"""


# Generating empty memories
def gen_empty_mem_hv(num_hv, hv_dim):
    return np.zeros((num_hv, hv_dim))


# Generating orthogonal item memory
def gen_orthogonal_im(num_hv, hv_dim, p_dense, hv_type="binary"):
    # Initialize empty matrix
    orthogonal_im = gen_empty_mem_hv(num_hv, hv_dim)

    for i in range(num_hv):
        orthogonal_im[i] = gen_ri_hv(hv_dim=hv_dim, p_dense=p_dense, hv_type=hv_type)

    return orthogonal_im


"""
    Functions for testing purposes
    
    prediction_idx:
        - returns the predicted index from the associative memory
        - arguments:
            - assoc_mem: the associative memory
            - query_hv: is the query hypervector
            - hv_type: is HV type to use
            
    prediction_set:
        - returns a set of predicted values
        - arguments:
            - assoc_mem: associative memory model
            - query_hv_set: query hyper vectors set
            - hv_type: is HV type to use
            
    measure_acc:
        - measures the accuracy between a test set and the correct set
        - 
"""


# Returns the predicted index
def prediction_idx(assoc_mem, query_hv, hv_type="binary"):
    score_list = []

    for i in range(len(assoc_mem)):
        score_list.append(norm_dist_hv(assoc_mem[i], query_hv, hv_type=hv_type))

    predict_idx = np.argmax(score_list)

    return predict_idx


# Get prediction set
def prediction_set(assoc_mem, query_hv_set, hv_type="binary"):
    # Initialize prediction set
    predict_set = []
    len_query_hv_set = len(query_hv_set)

    # Predict test element
    for i in range(len_query_hv_set):
        predict_set.append(prediction_idx(assoc_mem, query_hv_set[i], hv_type=hv_type))

    return predict_set


# Measuring accuracy for the test set
# The correct set needs to be in correct order
def measure_acc(assoc_mem, predict_set, correct_set):
    len_predict_set = len(predict_set)

    # Count number of correct elements
    count_correct_items = len(set(predict_set) & set(correct_set))

    # Measure accuracy
    acc = count_correct_items / len_predict_set

    return acc
