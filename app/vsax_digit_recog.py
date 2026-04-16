"""
VSAX Digit Recognition Application

This application demonstrates the use of VSAX
for digit recognition using the MNIST dataset.
"""

# Packages
import os
import sys
from pathlib import Path

# Global parameters
HV_SIZE = 1024
CLASS_LIST = [0, 1, 2, 3, 4, 5, 6, 7, 8, 9]

# Path directories
curr_dir = os.path.dirname(os.path.abspath(__file__))
lib_path = curr_dir + "/../lib"
data_path = curr_dir + "/../data"
dataset_path = data_path + "/mnist_uint"
model_path = curr_dir + "/../models"
model_name = Path(__file__).stem

# Appending other paths for libraries
sys.path.append(lib_path)

# Importing VSAX libraries
import vsax  # noqa: E402
import vsax_models  # noqa: E402
import vsax_util  # noqa: E402

(
    save_mode,
    load_mode,
) = vsax_models.vsax_general_parser()
model_file = model_name + f"_d{HV_SIZE}.npz"
model_dir = model_path + f"/{model_file}"

# Download pre-trained model
if load_mode:
    vsax_util.download_file(
        url=f"{vsax_util.git_trained_models_url}/{model_file}",
        out_dir=model_path,
        filename=model_file,
    )

# Downloading and extracting the MNIST dataset
vsax_util.download_and_extract(
    url=vsax_util.vsax_data_url_mnist,
    out_dir=data_path,
)

# Read data
X_data = vsax_util.read_data(CLASS_LIST, dataset_path)

# Train and test split
train_test_split = 0.6
train_valid_split = 0.75

X_train_set, X_valid_set, X_test_set = vsax_util.split_train_valid_test_set(
    X_data=X_data,
    class_list=CLASS_LIST,
    train_test_split=train_test_split,
    train_valid_split=train_valid_split,
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
    model_name=model_name,
    hv_size=HV_SIZE,
    class_list=CLASS_LIST,
)

if load_mode:
    # Load an existing trained model
    digit_model.load_model(model_dir)
else:
    # Train the model
    digit_model.train_model(X_train_set)

    # Retrain the model
    digit_model.retrain_model(X_valid_set)

# Test the model
digit_model.test_model(X_test_set)

# Print some statistics
digit_model.print_model_stats()

# Save model
if save_mode:
    digit_model.save_model(model_dir)
