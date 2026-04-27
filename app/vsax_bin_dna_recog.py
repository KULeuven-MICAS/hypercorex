"""
VSAX Binary DNA Recognition

This application demonstrates the use of VSAX
for the DNA recognition task.
"""

# Parameters
import os
import sys
from pathlib import Path

# Global parameters
HV_SIZE = 2048
CLASS_LIST = [0, 1, 2]
GEN_TYPE = "lfsr"

# Path directories
curr_dir = os.path.dirname(os.path.abspath(__file__))
model_name = Path(__file__).stem
lib_path = curr_dir + "/../lib"
data_path = curr_dir + "/../data"
dataset_path = data_path + "/dna"
model_path = curr_dir + "/../models"

# Appending other paths for libraries
sys.path.append(lib_path)

# Importing VSAX libraries
import vsax  # noqa: E402
import vsax_models  # noqa: E402
import vsax_util  # noqa: E402

(
    save_mode,
    load_mode,
    disable_tqdm,
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

# Downloading and extracting the DNA dataset
vsax_util.download_and_extract(
    url=vsax_util.vsax_data_url_bin_dna,
    out_dir=data_path,
    delete_archive=True,
)

# Read data
X_data = vsax_util.read_data(CLASS_LIST, dataset_path, disable_tqdm=disable_tqdm)

# Train and test split
train_test_split = 0.6
train_valid_split = 0.75

X_train_set, X_valid_set, X_test_set = vsax_util.split_train_valid_test_set(
    X_data=X_data,
    class_list=CLASS_LIST,
    train_test_split=train_test_split,
    train_valid_split=train_valid_split,
    disable_tqdm=disable_tqdm,
)


# Make class for DNA model
class dnaVSA(vsax_models.vsaModel):
    def encode(self, item_data):
        # Feature length
        item_len = len(item_data)
        encoded_vec = vsax.hv_gen_empty(self.hv_size)

        # Iterate through different item
        for i in range(item_len):
            # Fetch and permute i-times
            encoded_vec += vsax.hv_circ_perm(self.ortho_im[item_data[i]], i)
        # Threshold for binarization
        threshold = item_len // 2
        # Binarization
        if self.binarize_encode:
            encoded_vec = vsax.hv_binarize(encoded_vec, threshold, self.hv_type)
        return encoded_vec


# Make DNA class
dna_model = dnaVSA(
    model_name=model_name,
    hv_size=HV_SIZE,
    class_list=CLASS_LIST,
    gen_type=GEN_TYPE,
)

# Disabling TQDM debug progress bars
dna_model.tqdm_train_disable = disable_tqdm
dna_model.tqdm_retrain_disable = disable_tqdm
dna_model.tqdm_test_disable = disable_tqdm

if load_mode:
    # Load an existing trained model
    dna_model.load_model(model_dir)
else:
    # Train the model
    dna_model.train_model(X_train_set)

    # Retrain the model
    dna_model.retrain_model(X_valid_set)

# Test the model
dna_model.test_model(X_test_set)

# Print some statistics
dna_model.print_model_stats()

# Checker if accuracy is expected
assert dna_model.model_accuracy > 0.8, "Test accuracy is lower than expected."
print("✓ Test accuracy passed.")

# Save model
if save_mode:
    dna_model.save_model(model_dir)
