"""
VSAX Digit Recognition Application

This application demonstrates the use of VSAX
for digit recognition using the MNIST dataset.
"""

# Parameters
import os
import sys

# Path directories
curr_dir = os.path.dirname(os.path.abspath(__file__))
lib_path = curr_dir + "/../lib"
data_path = curr_dir + "/../data"
dataset_path = data_path + "/mnist_bin"

# Appending other paths for libraries
sys.path.append(lib_path)

# Importing VSAX libraries
import vsax  # noqa: E402
import vsax_models  # noqa: E402
import vsax_util  # noqa: E402

save_mode, load_mode, model_name = vsax_models.vsax_general_parser()
model_dir = curr_dir + f"/../models/{model_name}.npz"

# Downloading and extracting the MNIST dataset
vsax_util.download_and_extract(
    url=vsax_util.vsax_data_url_bin_mnist,
    out_dir=data_path,
    delete_archive=True,
)

# Set class list
class_list = [0, 1, 2, 3, 4, 5, 6, 7, 8, 9]

# Read data
X_data = vsax_util.read_data(class_list, dataset_path)

# Train and test split
train_test_split = 0.6
train_valid_split = 0.75

X_train_set, X_valid_set, X_test_set = vsax_util.split_train_valid_test_set(
    X_data=X_data,
    class_list=class_list,
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
        encoded_vec = vsax.hv_gen_empty(self.hv_size)
        for i in range(item_len):
            if item_data[i] == 0:
                encoded_vec += self.ortho_im[i]
            else:
                encoded_vec += vsax.hv_circ_perm(self.ortho_im[i], 1)
        # Binarization
        if self.binarize_encode:
            encoded_vec = vsax.hv_binarize(encoded_vec, threshold, self.hv_type)
        return encoded_vec


# Make digit class
digit_model = digitVSA(
    model_name=model_name,
    hv_size=1024,
    class_list=class_list,
    gen_type="lfsr",
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
