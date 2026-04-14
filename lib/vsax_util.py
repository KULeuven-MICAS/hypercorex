"""
================================
VSAX Utility Functions
================================

This library consists of utility functions like data downloading and processing.
Also consists of plotting functions that are useful for profiling too.
"""

# ---------------------------------------------------------------------------
# File extraction functions
# ---------------------------------------------------------------------------


# For simple file extraction
def extract_dataset(file_path):
    """
    Extract dataset from a text file.

    Parameters:
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
