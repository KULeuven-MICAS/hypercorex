#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
    Copyright 2024 KU Leuven
    Ryan Antonio <ryan.antonio@esat.kuleuven.be>
    
    Description:
    These contain useful functions for testing HDC activities
"""


import numpy as np
from tqdm import tqdm
import matplotlib.pyplot as plt
import requests
import tarfile
import io


"""
    General functions

"""


# For extracting information from tar.gz files
def extract_git_dataset(url, target_dir):
    # Extract the dataset
    response = requests.get(url, stream=True)
    response.raise_for_status()  # Raise an error on bad status

    # Extract the data sets
    with tarfile.open(fileobj=io.BytesIO(response.content), mode="r:gz") as tar:
        # Extract all files to a directory
        tar.extractall(path=target_dir)
    return


# For simple file extraction
def extract_dataset(file_path):
    # Initialize empty data set array
    dataset = []

    with open(file_path, "r") as file:
        lines = file.readlines()

        for line in lines:
            dataset.append(line.strip())

    return dataset


# Convert a number in binary to a list
# Used to feed each bundler unit
def numbin2list(numbin, dim):
    # Convert binary inputs first
    bin_hv = np.array(list(map(int, format(numbin, f"0{dim}b"))))
    return bin_hv


# Convert a number in binary to a list
# Used to feed each bundler unit
def numbip2list(numbin, dim):
    # Convert binary inputs first
    bin_hv = np.array(list(map(int, format(numbin, f"0{dim}b"))))
    # Get marks that have 0s
    mask = bin_hv == 0
    # Convert 0s to -1s
    bin_hv[mask] = -1
    return bin_hv


# Convert from list to binary value
def hvlist2num(hv_list):
    # Bring back into an integer itself!
    # Sad workaround is to convert to str
    # The convert to integer
    hv_num = "".join(hv_list.astype(str))
    hv_num = int(hv_num, 2)

    return hv_num


def reshape_hv(hv, sub_elem_size):
    div_check = len(hv) % sub_elem_size
    num_sub_elem = len(hv) // sub_elem_size
    if div_check == 0:
        return hv.reshape(num_sub_elem, sub_elem_size)
    else:
        print(f"Error! Not divisible by sub_elem_size - > div check: {div_check}")


def reshape_hv_list(hv_list, sub_elem_size):
    for i in range(len(hv_list)):
        if i == 0:
            return_list = reshape_hv(hv_list[i], sub_elem_size)
        else:
            temp_reshape = reshape_hv(hv_list[i], sub_elem_size)
            return_list = np.concatenate((return_list, temp_reshape), axis=0)
    return return_list


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
            
    norm_dist_hv:
        - for calculating the normalized distances
        - arguments:
            - hv_a, hv_b: input hypervectors
            - hv_type: hv_type of hypervector, if bipolar we threshold at 0
            
    gen_conf_mat:
        - for generating a confusion matrix
        - arguments:
            - num_levels: number of levels to generate
            - hv_list: list of hypervectors to use

"""


# Generate empty HV
def gen_empty_hv(hv_dim):
    return np.zeros(hv_dim, dtype=int)


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
def bind_hv(hv_a, hv_b, hv_type="binary"):
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


# Calculatiing confusion matrix
def gen_conf_mat(num_levels, hv_list):
    # Intiialize empty confusion matrix
    conf_mat = np.zeros((num_levels, num_levels))

    # Iterate through different levels
    for i in tqdm(range(num_levels), desc="Generating confusion matrix"):
        for j in range(num_levels):
            conf_mat[i][j] = norm_dist_hv(hv_list[i], hv_list[j])

    return conf_mat


"""
    Functions for generating item memories
    
    gen_empty_mem_hv:
        - arguments:
            - for generating an empty IM matrix used for
              initializing an im
            - num_hv: number of hypervectors to generate
            - hv_dim: dimension of each hypervector
    
    gen_ca90:
        - CA 90 generation of new HV
        - argeuments:
            - hv_seed: base hypervector seed
            - cycle_time: number of iterations
            
    gen_hv_ca90_iterate_rows:
        - CA 90 generation of an entire HV by
          iterating each chunk of the hypervector
        - arguments:
            - hv_seed: base hypervector seed
            - hv_dim: target hypervector dimension
    
    gen_hv_ca90_hierarchical_rows:
        - CA 90 generation of an entire HV by
          hierarchical means (faster generation)
        - arguments:
            - hv_seed: base hypervector seed
            - hv_dim: target hypervector dimension    
    
    gen_orthogonal_im:
        - generates a set of HVs with orthogonal mapping
        - arguments:
            - num_hv: number of hypervectors to generate
            - hv_dim: dimension of each hypervector
            - p_dense: the density of each hypervector
            - hv_type: type of hypervector

    ca90_extract_seeds:
        - This function is for extracting seeds
          That give the target 50% density of a base HV
          
    gen_ca90_im_set:
        - This generates the seeds for the item memory
          moreover it also generates a confusion matrix
          and a heatmap for inspection purposes

    gen_square_cim:
        - Generates a square cim that is half of the dimension size
"""


# Generating empty memories
def gen_empty_mem_hv(num_hv, hv_dim):
    return np.zeros((num_hv, hv_dim), dtype=int)


# The CA 90 generation
def gen_ca90(hv_seed, cycle_time):
    shift_left = np.roll(hv_seed, -1 * cycle_time)
    shift_right = np.roll(hv_seed, cycle_time)
    new_hv = np.bitwise_xor(shift_left, shift_right)
    return new_hv


# Iterative splitting of iterative ca90
def gen_hv_ca90_iterate_rows(hv_seed, hv_dim):
    # Extract number of lengths
    len_hv_seed = len(hv_seed)

    # Total iterations is number of seeds
    # within target HV but -1 to include the base seed
    iterations = int(hv_dim / len_hv_seed) - 1

    # Initialize generated hv
    gen_hv = hv_seed

    # Iterate until we reach HV size
    for i in range(iterations):
        gen_hv = np.concatenate((gen_hv, gen_ca90(hv_seed, i + 1)))

    return gen_hv


# Hierarchical generation of the ca90
def gen_hv_ca90_hierarchical_rows(hv_seed, hv_dim, permute_base=1):
    # Initialize generated hv
    gen_hv = hv_seed

    # Initialize number
    len_gen_hv = len(gen_hv)

    # Iterate until we reach HV size
    while len_gen_hv != hv_dim:
        gen_ca90_hv = gen_ca90(gen_hv, permute_base)
        gen_hv = np.concatenate((gen_ca90_hv, gen_hv))
        len_gen_hv = len(gen_hv)

    return gen_hv


# This function is for extracting seeds
# That give the target 50% density of a base HV
def ca90_extract_seeds(seed_size, seed_num, hv_dim, ca90_mode="iter", debug_info=False):
    hv_half_dim = int(hv_dim / 2)
    seed_list = []
    seed_count = 0
    run_count = 0

    while seed_count != seed_num:
        run_count += 1
        hv_seed = gen_ri_hv(seed_size, 0.5)
        if ca90_mode == "iter":
            gen_hv = gen_hv_ca90_iterate_rows(hv_seed, hv_dim)
        else:
            gen_hv = gen_hv_ca90_hierarchical_rows(hv_seed, hv_dim)

        density_hv = np.sum(gen_hv)

        if density_hv == hv_half_dim:
            seed_idx = hvlist2num(hv_seed)
            seed_list.append(seed_idx)
            seed_count += 1

    if debug_info:
        print(f"Search count time: {run_count}")
        print(f"Target HV Dimension: {hv_dim}")
        print(f"Seed size: {seed_size}")
        print(f"Number of seeds: {seed_num}")

    return seed_list


# Generating orthogonal item memory
def gen_orthogonal_im(
    num_hv,
    hv_dim,
    p_dense,
    hv_seed=0,
    permute_base=1,
    hv_type="binary",
    im_type="random",
):
    # Initialize empty matrix
    orthogonal_im = gen_empty_mem_hv(num_hv, hv_dim)

    # Do this for initialize first seed first
    if im_type == "ca90_iter":
        orthogonal_im[0] = gen_hv_ca90_iterate_rows(hv_seed, hv_dim)
    elif im_type == "ca90_hier":
        orthogonal_im[0] = gen_hv_ca90_hierarchical_rows(hv_seed, hv_dim)
    else:
        orthogonal_im[0] = gen_ri_hv(hv_dim=hv_dim, p_dense=p_dense, hv_type=hv_type)

    # Generate all other item memories
    for i in range(1, num_hv):
        if im_type == "random":
            orthogonal_im[i] = gen_ri_hv(
                hv_dim=hv_dim, p_dense=p_dense, hv_type=hv_type
            )
        else:
            orthogonal_im[i] = gen_ca90(orthogonal_im[i - 1], permute_base)

    return orthogonal_im


# This function generates an item memory
# for the specified number of items and items per im bank
# It displays a heat map and displays the seeds to use
# Returns the seeds and the confusion matrix
def gen_ca90_im_set(
    seed_size,
    hv_dim,
    num_total_im,
    num_per_im_bank,
    base_seeds=[0],
    gen_seed=False,
    ca90_mode="hier",
    display_heatmap=False,
    debug_info=False,
):
    # Sanity checker for parameter
    if num_per_im_bank >= int(hv_dim / 2):
        print(" ------------------------------------------ ")
        print("            !!!!!  WARNING  !!!!!           ")
        print(f" The number of IM per bank {num_per_im_bank}")
        print(f" must be less than half of the HV dimension size {hv_dim}")
        print(" It is recommended that it is 1/4th of the dimension size to avoid")
        print(" saturating at all 1s or all 0s due to CA90 limitations")
        print(" ------------------------------------------ ")

    num_ims = int(num_total_im / num_per_im_bank)

    # Extract seed list that give
    # 50% density of a base HV
    if gen_seed:
        assert (
            len(base_seeds) >= num_ims
        ), "Error! Base seed length needs to be same as num of ims."
        seed_list = base_seeds
    else:
        seed_list = ca90_extract_seeds(seed_size, num_ims, hv_dim, ca90_mode=ca90_mode)

    # Generate the 1st orthogonal item memory
    hv_seed = numbin2list(seed_list[0], seed_size)
    ortho_im = gen_orthogonal_im(
        num_per_im_bank, hv_dim, 0.5, hv_seed, permute_base=7, im_type="ca90_hier"
    )

    # Generate all other sets
    for i in range(1, num_ims):
        hv_seed = numbin2list(seed_list[i], seed_size)
        temp_orth_im = gen_orthogonal_im(
            num_per_im_bank, hv_dim, 0.5, hv_seed, permute_base=7, im_type="ca90_hier"
        )
        ortho_im = np.concatenate((ortho_im, temp_orth_im), axis=0)

    # Plot the working heat map
    if display_heatmap:
        # Get the confusion matrix!
        conf_mat = gen_conf_mat(num_total_im, ortho_im)

        # Plot the heatmap
        heatmap_plot(conf_mat)

    else:
        conf_mat = None

    # Print the IM seeds to use
    if debug_info:
        for i in range(num_ims):
            print()  # for new line purposes
            print(f"IM seed #{i}: {seed_list[i]}; hex code: {hex(seed_list[i])}")

    return seed_list, ortho_im, conf_mat


# Generating a square CiM
# The number of levels is the ortho distance
# depending on the dimension size
def gen_square_cim(
    hv_dim, seed_size, base_seed=0, gen_seed=True, im_type="random", debug_info=False
):
    if gen_seed:
        # Set a pre-determined seed
        lowdim_seed_list = ca90_extract_seeds(seed_size, 1, hv_dim, ca90_mode=im_type)
        base_seed = lowdim_seed_list[0]

    if debug_info:
        print(f"CiM seed: {base_seed}")

    lowdim_hv_seed = numbin2list(base_seed, seed_size)

    # Half of the distance
    # which marks the number of levels
    hv_ortho_dist = int(hv_dim / 2)

    # First initialize some seed HV
    # Depending on which mode we choose
    # Do this for initialize first seed first
    if im_type == "ca90_iter":
        hv_seed = gen_hv_ca90_iterate_rows(lowdim_hv_seed, hv_dim)
    elif im_type == "ca90_hier":
        hv_seed = gen_hv_ca90_hierarchical_rows(lowdim_hv_seed, hv_dim)
    else:
        hv_seed = gen_ri_hv(hv_dim=hv_dim, p_dense=0.5, hv_type="binary")

    # Initialize empty memory
    cim = gen_empty_mem_hv(hv_ortho_dist, hv_dim)

    # Set first seed for the empty memory
    cim[0] = hv_seed.copy()

    # Fill-in and flip bits
    # On every other skip step
    for i in range(1, hv_ortho_dist):
        if cim[i - 1][2 * i - 1] == 0:
            cim[i] = cim[i - 1]
            cim[i][2 * i - 1] = 1
        else:
            cim[i] = cim[i - 1]
            cim[i][2 * i - 1] = 0

    return lowdim_hv_seed, cim


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
        - arguments:
            - assoc_mem: associative memory model
            - predict_set: the set of qeury hvs
            - correct_set: golden answers that need to match
                           the predict_set
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
def measure_acc(predict_set, correct_set):
    len_predict_set = len(predict_set)

    # Count number of correct elements
    count_correct_items = len(set(predict_set) & set(correct_set))

    # Measure accuracy
    acc = count_correct_items / len_predict_set

    return acc


"""
    Simple matplotlib plotting functions
    
    simple_plot2d:
        - For plotting simple 2D plots
        - arguments:
            - x, y: the x and y values,
                    y can be a list of multiple arrays
            - title: title of the plot
            - xlabel: label of x-axis
            - ylabel: label of y-axis
            - plt_label: list of labels, only useful for multiple plots
            - linestyle: type of lines
            - marker: type of data point marks
            - grid: activate grid
            - legend: activate legend for lines
            - single_plot: if single line only or multiple lines
"""


# Simple 2D plot
def simple_plot2d(
    x,
    y,
    title="Cool title",
    xlabel="x-axis",
    ylabel="y-axis",
    plt_label=[],
    linestyle="-",
    marker="",
    grid=True,
    legend=True,
    single_plot=True,
):
    # Check if single plot only or not
    if single_plot:
        # Plot figure
        plt.plot(
            x,
            y,
            linestyle=linestyle,
            marker=marker,
        )

        # Add title and axes titles
        plt.title(title)
        plt.xlabel(xlabel)
        plt.ylabel(ylabel)
        plt.grid(grid)

        # Show plot
        plt.show()
    else:
        num_plots = len(y)

        # Iterative plotting
        for i in range(num_plots):
            plt.plot(
                x,
                y[i],
                label=plt_label[i],
                linestyle=linestyle,
                marker=marker,
            )

        # Add title and axes titles
        plt.title(title)
        plt.xlabel(xlabel)
        plt.ylabel(ylabel)
        plt.grid(grid)

        # Plot legend if true
        if legend:
            plt.legend(loc="center right")

        # Show plot
        plt.show()

    return


# Plotting heatmaps


def heatmap_plot(
    data,
    title="Cool title",
    xlabel="x-axis",
    ylabel="y-axis",
    cmap="viridis",
):
    # Heatmap
    plt.imshow(data, cmap=cmap, interpolation="nearest")

    # Add colorbar
    plt.colorbar()

    # Add title and axes titles
    plt.title(title)
    plt.xlabel(xlabel)
    plt.ylabel(ylabel)

    # Step 4: Display the plot
    plt.show()
    return
