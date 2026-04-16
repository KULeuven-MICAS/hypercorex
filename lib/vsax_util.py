"""
================================
VSAX Utility Functions
================================

This library consists of utility functions like data downloading and processing.
Also consists of plotting functions that are useful for profiling too.
"""

# Importing packages
import urllib.request
import zipfile
import tarfile
import random
import numpy as np
from tqdm import tqdm
from pathlib import Path

# ---------------------------------------------------------------------------
# List of data sets
# ---------------------------------------------------------------------------
vsax_data_url_mnist = "https://github.com/rgantonio/chronomatica/releases/download/mnist_dataset_v1.0/chronomatica_mnist_uint.tar.gz"
vsax_data_url_bin_mnist = "https://github.com/rgantonio/chronomatica/releases/download/mnist_dataset_v1.0/chronomatica_mnist_bin.tar.gz"

# ---------------------------------------------------------------------------
# Main pre-trained model url
# ---------------------------------------------------------------------------
ver_trained_models = "v0.1.0"
git_trained_models_url = f"https://github.com/KULeuven-MICAS/hypercorex/releases/download/vsax_trained_models_{ver_trained_models}"

# ---------------------------------------------------------------------------
# File extraction functions
# ---------------------------------------------------------------------------


# For simple file extraction
def extract_dataset(file_path: str) -> list[str]:
    """
    Extract dataset from a text file.

    Args:
        file_path (str): The path to the text file containing the dataset.
    Returns:
        list: A list of strings, where each string is a line from the file.
    """
    # Initialize empty data set array
    dataset = []

    with open(file_path, "r") as file:
        lines = file.readlines()

        for line in lines:
            dataset.append(line.strip())

    return dataset


# For downloading only
def download_file(url: str, out_dir: str | Path = "data", filename: str | None = None):
    """
    Download a file from a URL.

    Args:
        url (str): The URL to download the file from.
        out_dir (str | Path): The directory to save the downloaded file in.
        filename (str | None): Optional override for downloaded filename.
    """
    out_dir = Path(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    if filename is None:
        filename = url.split("/")[-1]

    file_path = out_dir / filename

    # Download (skip if already exists)
    if not file_path.exists():
        print(f"Downloading {filename}...")
        urllib.request.urlretrieve(url, file_path)
    else:
        print(f"{filename} already exists, skipping download.")


# For downloading and extracting archives
def download_and_extract(
    url: str,
    out_dir: str | Path = "data",
    filename: str | None = None,
    delete_archive: bool = False,
):
    """
    Download an archive from a URL and extract it.

    Args:
        url (str): Download URL
        out_dir (str | Path): Output directory
        filename (str | None): Optional override for downloaded filename
        delete_archive (bool): Delete archive after successful extraction
    """
    out_dir = Path(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    if filename is None:
        filename = url.split("/")[-1]

    archive_path = out_dir / filename

    # Download (skip if already exists)
    if not archive_path.exists():
        print(f"Downloading {filename}...")
        urllib.request.urlretrieve(url, archive_path)
    else:
        print(f"{filename} already exists, skipping download.")

    # Extract
    print("Extracting...")
    try:
        if filename.endswith(".zip"):
            with zipfile.ZipFile(archive_path, "r") as zf:
                zf.extractall(out_dir)
        elif filename.endswith((".tar.gz", ".tgz")):
            with tarfile.open(archive_path, "r:gz") as tf:
                tf.extractall(out_dir)
        else:
            raise ValueError(f"Unsupported archive format: {filename}")
    except Exception as e:
        raise RuntimeError(f"Extraction failed: {e}")

    # Optional cleanup
    if delete_archive:
        archive_path.unlink()
        print(f"Deleted archive: {archive_path.name}")

    print("Extraction complete!")


# For reading and loading a data
def load_dataset(file_path: str) -> np.ndarray:
    """
    Load dataset from a text file.

    Args:
        file_path (str): Path to the text file
    Returns:
        dataset (np.ndarray): Loaded dataset as a NumPy array
    """
    # Initialize empty data set array
    dataset = []
    with open(file_path, "r") as rf:
        for line in rf:
            line = line.strip().split()
            int_line = [int(x) for x in line]
            dataset.append(int_line)
    # Close the file
    rf.close()
    return np.array(dataset, dtype=np.uint8)


# Reading of data from files for each class label
def read_data(class_list: list, data_path: str, disable_tqdm: bool = False) -> list:
    """
    Read data from files for each class label.

    Args:
        class_list: list of class labels
        data_path: path to the data files
        disable_tqdm: whether to disable tqdm progress bars
    Returns:
        X_data: list of NumPy arrays with data for each class label
    """
    X_data = []
    for class_label in tqdm(class_list, desc="Reading data", disable=disable_tqdm):
        # Training dataset
        read_file = f"{data_path}/{class_label}.txt"
        X_data.append(load_dataset(read_file))
    return X_data


# Splitting the data and randomizing items
def split_data(
    X_data: list,
    class_list: list,
    split_percent: float = 0.8,
    disable_tqdm: bool = False,
) -> tuple[list, list]:
    """
    Split data into two parts based on split_percent.

    Args:
        X_data: list of NumPy arrays with data for each class label
        class_list: list of class labels
        split_percent: percentage of data to go into first split
    Returns:
        X_split_data1: first split of data
        X_split_data2: second split of data
    """
    # Initialize empty lists
    X_split_data1 = []
    X_split_data2 = []

    for class_label in tqdm(class_list, desc="Splitting data", disable=disable_tqdm):
        # Get item counts first
        item_len = len(X_data[class_label])
        split1_len = round(item_len * split_percent)
        split2_len = item_len - split1_len

        # Randomize the contents of the list first
        random.shuffle(X_data[class_label])

        # Get split 1 first
        split1_list = []
        for item_num in range(split1_len):
            split1_list.append(X_data[class_label][item_num])

        # Get split 2 next but starts at split1_len count
        split2_list = []
        for item_num in range(split1_len, split1_len + split2_len):
            split2_list.append(X_data[class_label][item_num])

        # Load into dictionaries
        X_split_data1.append(split1_list)
        X_split_data2.append(split2_list)

    return X_split_data1, X_split_data2


# Splitting the data but in train, valid, and test sets
def split_train_valid_test_set(
    X_data: list,
    class_list: list,
    train_test_split: float = 0.6,
    train_valid_split: float = 0.75,
    disable_tqdm: bool = False,
) -> tuple[list, list, list]:
    """
    Split data into training, validation, and test sets.

    Args:
        X_data: list of NumPy arrays with data for each class label
        class_list: list of class labels
        train_test_split: percentage of data to go into
        training set (rest goes to test set)
        train_valid_split: percentage of training set to
        go into training set (rest goes to validation set)
    Returns:
        X_train_set: training set
        X_valid_set: validation set
        X_test_set: test set
    """
    X_train_set, X_test_set = split_data(
        X_data, class_list, split_percent=train_test_split, disable_tqdm=disable_tqdm
    )
    X_train_set, X_valid_set = split_data(
        X_train_set,
        class_list,
        split_percent=train_valid_split,
        disable_tqdm=disable_tqdm,
    )
    return X_train_set, X_valid_set, X_test_set
