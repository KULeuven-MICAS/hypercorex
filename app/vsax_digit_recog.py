"""
VSAX Digit Recognition Application

This application demonstrates the use of VSAX for digit recognition using the MNIST dataset.
"""

# Parameters
import os
import sys

# Path directories
curr_dir = os.getcwd()
lib_path = curr_dir + "/../lib"
extract_path = curr_dir + "/../data/extract_data"
data_path = curr_dir + "/../data"
dir_bin_data = data_path + "/mnist_uint"

# Appending other paths for libraries
sys.path.append(lib_path)
sys.path.append(extract_path)

# Importing VSAX libraries
import vsax
import vsax_models
import vsax_util

# Downloading and extracting the MNIST dataset
vsax_util.download_and_extract(
    url=vsax_util.vsax_data_url_mnist,
    out_dir=data_path,
    delete_archive=True,
)

# Set class list
class_list = [0, 1, 2, 3, 4, 5, 6, 7, 8, 9]

# Read data
X_data = vsax_util.read_data(class_list, dir_bin_data)

# Train and test split
train_test_split = 0.6
train_valid_split = 0.75

X_train_set, X_test_set = vsax_util.split_data(
    X_data, class_list, split_percent=train_test_split
)
X_train_set_src, X_valid_set = vsax_util.split_data(
    X_train_set, class_list, split_percent=train_valid_split
)


# Make class for digit model
class digitVSA(vsax_models.vsaModel):
    def encode(self, item_data):
        # Feature length
        item_len = len(item_data)
        # Threshold for binarization
        threshold = item_len // 2
        # Encode hypervector
        encoded_vec = item_data @ self.ortho_im[0:item_len]
        # Binarization
        if self.binarize_encode:
            encoded_vec = vsax.hv_binarize(encoded_vec, threshold, self.hv_type)
        return encoded_vec


# Make digit class
digit_model = digitVSA(
    hv_size=1024,
    class_list=class_list,
)

# Train the model
digit_model.train_model(X_train_set_src)

# Test the model
digit_model.test_model(X_test_set)

# Print some statistics
digit_model.print_model_stats()
