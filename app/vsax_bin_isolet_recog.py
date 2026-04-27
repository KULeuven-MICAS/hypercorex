"""
VSAX Binary ISOLET Recognition

This application demonstrates the use of VSAX
for the ISOLET recognition task.
"""

# Parameters
import sys
import os
from pathlib import Path

# Global parameters
HV_SIZE = 512
CLASS_LIST = list(range(26))
GEN_TYPE = "lfsr"
NUM_CIM = 21

# Path directories
curr_dir = os.path.dirname(os.path.abspath(__file__))
model_name = Path(__file__).stem
lib_path = curr_dir + "/../lib"
data_path = curr_dir + "/../data"
dataset_path = data_path + "/isolet"
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

# Downloading and extracting the ISOLET dataset
vsax_util.download_and_extract(
    url=vsax_util.vsax_data_url_bin_isolet,
    out_dir=data_path,
    delete_archive=True,
)

# Read data
X_data = vsax_util.read_data(CLASS_LIST, dataset_path, disable_tqdm=disable_tqdm)
X_data = vsax_util.convert_levels(X_data, NUM_CIM)

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


# Make class for ISOLET model
class isoletVSA(vsax_models.vsaModel):
    def encode(self, item_data):
        # Feature length
        item_len = len(item_data)
        encoded_vec = vsax.hv_gen_empty(self.hv_size)

        # Iterate through different item
        for i in range(item_len):
            # Get ID HV
            attribute_id_hv = self.ortho_im[i]
            # Get value HV at that ID
            attribute_val_hv = self.cim[item_data[i]]
            # Bind ID and value HVs
            attribute_val_loc_hv = vsax.hv_bind(
                attribute_id_hv, attribute_val_hv, hv_type=self.hv_type
            )
            # Accumulate through all samples
            encoded_vec += attribute_val_loc_hv

        # Threshold for binarization
        threshold = item_len // 2
        # Binarization
        if self.binarize_encode:
            encoded_vec = vsax.hv_binarize(encoded_vec, threshold, self.hv_type)
        return encoded_vec


# Make ISOLET class
isolet_model = isoletVSA(
    model_name=model_name,
    hv_size=HV_SIZE,
    class_list=CLASS_LIST,
    gen_type=GEN_TYPE,
    num_cim=NUM_CIM,
)

# Binarize AM
isolet_model.binarize_am = True

# Disabling TQDM debug progress bars
isolet_model.tqdm_train_disable = disable_tqdm
isolet_model.tqdm_retrain_disable = disable_tqdm
isolet_model.tqdm_test_disable = disable_tqdm

if load_mode:
    # Load an existing trained model
    isolet_model.load_model(model_dir)
else:
    # Train the model
    isolet_model.train_model(X_train_set)

    # Retrain the model
    isolet_model.retrain_model(X_valid_set)

# Test the model
isolet_model.test_model(X_test_set)

# Print some statistics
isolet_model.print_model_stats()

# Checker if accuracy is expected
assert isolet_model.model_accuracy > 0.60, "Test accuracy is lower than expected."
print("✓ Test accuracy passed.")

# Save model
if save_mode:
    isolet_model.save_model(model_dir)
