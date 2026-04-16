"""
================================
VSAX Model Classes and Functions
================================

This library consists classes and functions for implementing various VSA models.
These classes are meant to be reproducible and extendable to other applications.
"""

import os
import vsax
import vsax_util
import numpy as np
from tqdm import tqdm
from typing import Optional
import argparse

# ============================================================================
# General Model Functions
# ============================================================================


# For general parsing
def vsax_general_parser():
    parser = argparse.ArgumentParser(description="VSAX Model Training and Testing")

    parser.add_argument(
        "--save", "-s", action="store_true", help="Train and save the model"
    )
    parser.add_argument("--load", "-l", action="store_true", help="Load the model")
    parser.add_argument(
        "--dtqdm", "-d", action="store_true", help="Disable tqdm progress bars"
    )
    args = parser.parse_args()

    save_mode = args.save
    load_mode = args.load
    disable_tqdm = args.dtqdm

    return save_mode, load_mode, disable_tqdm


# ============================================================================
# Main VSA Model class
# ============================================================================


class vsaModel:
    """
    Base class for VSA models.

    Parameters:
        model_name (str): The name of the model.
        hv_size (int): The size of the hypervectors.
        hv_type (str): The type of hypervector.
                       Can be 'bipolar', 'binary', 'real', or 'complex'.
        num_ortho_im (int): The number of orthogonal item memories.
        num_cim (int): The number of continuous item memories.
        cim_max_is_ortho (bool): If True, the maximum distance between
                                 CIM hypervectors is orthogonal.
        class_list (list): List of class labels.
        gen_type (str): The type of hypervector generation. Can be 'ri' or 'lfsr'.
        gen_ri_p_dense (float): The density of the random index hypervectors.
        gen_lfsr_base_seed (int): The base seed for the LFSR generator.

    Attributes:
        ortho_im (np.ndarray): The orthogonal item memory hypervectors.
        cim (np.ndarray): The continuous item memory hypervectors.
        class_am (np.ndarray): The AM for each class.
        class_am_frozen (np.ndarray): The frozen AM for each class.
        class_am_bin (np.ndarray): The binarized AM for each class.
        class_am_count (np.ndarray): The count of items in each class AM.
        test_class_score (np.ndarray): The score for each class during testing.
        test_class_accuracy (np.ndarray): The accuracy for each class during testing.
        model_accuracy (float): The overall accuracy of the model during testing.

    Debugging Parameters:
        tqdm_train_disable (bool): If True, show progress bar during training.
        tqdm_retrain_disable (bool): If True, show progress bar during retraining.
        tqdm_test_disable (bool): If True, show progress bar during testing.

    Methods:
        encode(item_data): Encode the input data into a hypervector.
        train_model(X_train): Train the VSA model using the provided training data.
        retrain_model(X_train): Retrain the VSA model using the provided training data.
        test_model(X_test): Test the VSA model using the provided test data.
        print_model_stats(): Print the statistics of the VSA model.
        save_model(save_path): Save the model parameters to a file.
        load_model(load_path): Load the model parameters from a file.
    """

    def __init__(
        self,
        model_name: str = "vsaModel",
        hv_size: int = 1024,
        hv_type: str = "bipolar",
        num_ortho_im: int = 1024,
        num_cim: int = 21,
        cim_max_is_ortho: bool = True,
        class_list: Optional[list] = None,
        gen_type: str = "ri",
        gen_ri_p_dense: float = 0.5,
        gen_lfsr_base_seed: int = 42,
    ):
        # Model name
        self.model_name = model_name

        # Base parameters
        self.hv_size = hv_size
        self.hv_type = hv_type

        # Item memory parameters
        self.num_ortho_im = num_ortho_im
        self.num_cim = num_cim
        self.cim_max_is_ortho = cim_max_is_ortho
        self.gen_type = gen_type
        self.gen_ri_p_dense = gen_ri_p_dense
        self.gen_lfsr_base_seed = gen_lfsr_base_seed

        # Parameters that will be determined later
        self.class_list = class_list
        self.num_classes = len(class_list)

        # Some extra internal parameters
        self.binarize_encode = False
        self.binarize_am = False

        # Generate list of item memories (iMs)
        self.ortho_im = vsax.hv_gen_orthogonal_im(
            num_items=self.num_ortho_im,
            hv_size=self.hv_size,
            hv_type=self.hv_type,
            gen_type=self.gen_type,
            gen_ri_p_dense=self.gen_ri_p_dense,
            gen_lfsr_base_seed=self.gen_lfsr_base_seed,
        )

        # Generate list of CiM
        self.cim = vsax.hv_gen_continuous_im(
            num_items=self.num_cim,
            hv_size=self.hv_size,
            cim_max_is_ortho=self.cim_max_is_ortho,
            hv_type=self.hv_type,
        )

        # Initialization of associative memories
        self.class_am = vsax.hv_gen_empty_mem(self.num_classes, self.hv_size)
        self.class_am_frozen = vsax.hv_gen_empty_mem(self.num_classes, self.hv_size)
        self.class_am_bin = vsax.hv_gen_empty_mem(self.num_classes, self.hv_size)
        self.class_am_count = np.zeros(self.num_classes)

        # Some statistics for testing
        self.test_class_score = np.zeros(self.num_classes)
        self.test_class_accuracy = np.zeros(self.num_classes)
        self.model_accuracy = None

        # Some debugging parameters
        self.tqdm_train_disable = False
        self.tqdm_retrain_disable = False
        self.tqdm_test_disable = False

    # Main encoding function
    def encode(self, item_data):
        """
        Encode the input data into a hypervector.
        Make sure to replace or override this section with your designated encoder.

        Parameters:
            item_data: The input data to be encoded. The format of this data will
            depend on the specific application and should be defined in the subclass.
        Returns:
            np.ndarray: The encoded hypervector representation of the input data.
        """
        print(
            "Empty encoding, please make sure to \
            override this function in the subclass."
        )

    # Training function
    def train_model(self, X_train):
        """
        Train the VSA model using the provided training data.

        Parameters:
            X_train (list): A list of training data for each class.
        Returns:
            Updates the AM of the model based on the training data.
        """
        print("Training model...")
        for class_label in range(self.num_classes):
            data_len = len(X_train[class_label])

            # Non-binarized training
            for item_num in tqdm(
                range(data_len),
                desc=f"Training class {class_label}",
                disable=self.tqdm_train_disable,
            ):
                # Getting encodede HV
                encoded_vec = self.encode(X_train[class_label][item_num])
                # Bundle to the appropriate class
                self.class_am[class_label] += encoded_vec

            # Automatically compute binarized output
            threshold = data_len / 2
            self.class_am_bin[class_label] = vsax.hv_binarize(
                self.class_am[class_label], threshold, self.hv_type
            )

            # Setting the frozen class
            self.class_am_frozen[class_label] = np.copy(self.class_am[class_label])

            # Updating class number
            self.class_am_count[class_label] = data_len
        print("Training complete!")

    # Retraining function
    def retrain_model(self, X_train):
        print("Retraining model...")
        """
        Retrain the VSA model using the provided training data.

        Args:
            X_train (list): A list of training data for each class.
        """
        # Select if binarized AM or not
        if self.binarize_am:
            temp_class_am = self.class_am_bin
        else:
            temp_class_am = self.class_am_frozen

        for class_label in range(self.num_classes):
            data_len = len(X_train[class_label])

            # Retraining with binarized AM
            for item_num in tqdm(
                range(data_len),
                desc=f"Retraining class {class_label}",
                disable=self.tqdm_retrain_disable,
            ):
                # Getting encoded HV
                encoded_vec = self.encode(X_train[class_label][item_num])

                # Predict item
                predict_label = vsax.hv_prediction_idx(
                    temp_class_am, encoded_vec, hv_type=self.hv_type
                )

                # If incorrect we update the AMs
                if predict_label != class_label:
                    # Subtract from wrong class AM
                    self.class_am[predict_label] -= encoded_vec
                    self.class_am_count[predict_label] -= 1
                    # Add to correct class AM
                    self.class_am[class_label] += encoded_vec
                    self.class_am_count[class_label] += 1

            # Automatically compute binarized output
            threshold = self.class_am_count[class_label] / 2
            self.class_am_bin[class_label] = vsax.hv_binarize(
                self.class_am[class_label], threshold, self.hv_type
            )

        # For updating the frozen AM
        for class_label in range(self.num_classes):
            # Update frozen AM
            self.class_am_frozen[class_label] = np.copy(self.class_am[class_label])

        print("Retraining complete!")

    # Testing function
    def test_model(self, X_test):
        """
        Test the VSA model using the provided test data.

        Parameters:
            X_test (list): A list of test data for each class.
        Returns:
            float: The overall accuracy of the model.
        """
        print("Testing model...")

        correct_count = 0
        class_correct_count = 0
        total_count = 0

        if self.binarize_am:
            class_am = self.class_am_bin
        else:
            class_am = self.class_am_frozen

        for class_label in range(self.num_classes):
            data_len = len(X_test[class_label])
            class_correct_count = 0
            for item_num in tqdm(
                range(data_len),
                desc=f"Testing class {class_label}",
                disable=self.tqdm_test_disable,
            ):
                # Getting encoded HV
                encoded_vec = self.encode(X_test[class_label][item_num])
                # Compare with each class AM
                predict_label = vsax.hv_prediction_idx(
                    class_am, encoded_vec, hv_type=self.hv_type
                )

                if predict_label == class_label:
                    correct_count += 1
                    class_correct_count += 1
                total_count += 1

            self.test_class_score[class_label] = class_correct_count
            self.test_class_accuracy[class_label] = class_correct_count / data_len

        # Total score
        accuracy = correct_count / total_count
        self.model_accuracy = accuracy
        print("Testing complete!")
        return accuracy

    # Function to print model statistics
    def print_model_stats(self):
        """
        Print the statistics of the VSA model.
        """

        print("")
        print("===================")
        print(" Model Statistics:")
        print("===================")

        # Print internal parameters
        print(f"Model Name: {self.model_name}")
        print(f"HV Size: {self.hv_size}")
        print(f"HV Type: {self.hv_type}")
        print(f"Number of Orthogonal IMs: {self.num_ortho_im}")
        print(f"Number of Continuous IMs: {self.num_cim}")
        print(f"Number of Classes: {self.num_classes}")
        print(f"Generation Type: {self.gen_type}")
        if self.gen_type == "ri":
            print(f"RI p_dense: {self.gen_ri_p_dense}")
        elif self.gen_type == "lfsr":
            print(f"LFSR Base Seed: {self.gen_lfsr_base_seed}")

        # Print modes
        print(f"Binarize Encode: {self.binarize_encode}")
        print(f"Binarize AM: {self.binarize_am}")

        print("===================")
        print(" Accuracy Statistics:")
        print("===================")
        # Printing accuracies
        for class_label in range(self.num_classes):
            class_acc = self.test_class_accuracy[class_label]
            print(f"Class {class_label} Accuracy: {class_acc*100:.2f}%")

        print(f"Overall Accuracy: {self.model_accuracy*100:.2f}%")

    # Function to save the model parameters
    def save_model(self, save_path):
        """
        Save the model parameters to a file.

        Parameters:
            save_path (str): The path to save the model parameters.
        """
        np.savez_compressed(
            save_path,
            model_name=self.model_name,
            hv_size=self.hv_size,
            hv_type=self.hv_type,
            num_ortho_im=self.num_ortho_im,
            num_cim=self.num_cim,
            cim_max_is_ortho=self.cim_max_is_ortho,
            class_list=self.class_list,
            gen_type=self.gen_type,
            gen_ri_p_dense=self.gen_ri_p_dense,
            gen_lfsr_base_seed=self.gen_lfsr_base_seed,
            ortho_im=self.ortho_im,
            cim=self.cim,
            class_am=self.class_am,
            class_am_frozen=self.class_am_frozen,
            class_am_bin=self.class_am_bin,
            class_am_count=self.class_am_count,
        )
        print(f"Saved model: {save_path}!")

    # Function to load the model parameters
    def load_model(self, load_path):
        """
        Load the model parameters from a file.

        Parameters:
            load_path (str): The path to load the model parameters from.
        """
        data = np.load(load_path, allow_pickle=True)
        self.model_name = data["model_name"].item()
        self.hv_size = data["hv_size"].item()
        self.hv_type = data["hv_type"].item()
        self.num_ortho_im = data["num_ortho_im"].item()
        self.num_cim = data["num_cim"].item()
        self.cim_max_is_ortho = data["cim_max_is_ortho"].item()
        self.class_list = data["class_list"].tolist()
        self.gen_type = data["gen_type"].item()
        self.gen_ri_p_dense = data["gen_ri_p_dense"].item()
        self.gen_lfsr_base_seed = data["gen_lfsr_base_seed"].item()
        self.ortho_im = data["ortho_im"]
        self.cim = data["cim"]
        self.class_am = data["class_am"]
        self.class_am_frozen = data["class_am_frozen"]
        self.class_am_bin = data["class_am_bin"]
        self.class_am_count = data["class_am_count"]
        print(f"Loaded model: {load_path}!")


if __name__ == "__main__":
    # Simple test on the character recognition application
    base_dir = os.path.dirname(os.path.abspath(__file__))
    char_recog_dataset = vsax_util.extract_dataset(
        os.path.join(base_dir, "../hdc_exp/data_set/char_recog/characters.txt")
    )

    # Post-process to get list of character inputs
    # Use this as both train and test inputs
    char_recog_dict = dict()
    for i in range(len(char_recog_dataset)):
        char_recog_dict[i] = [np.array(list(map(int, list(char_recog_dataset[i]))))]

    # Create char encode model
    class vsaCharModel(vsaModel):
        def encode(self, item_data):
            # Feature length
            item_len = len(item_data)
            # Threshold
            threshold = item_len / 2
            encoded_vec = vsax.hv_gen_empty(self.hv_size)
            # Iterate per item
            for i in range(item_len):
                # If black pixel retain original orthogonal iM,
                # if white pixel permute orthogonal iM by 1
                if item_data[i] == 0:
                    encoded_vec += self.ortho_im[i]
                else:
                    encoded_vec += vsax.hv_circ_perm(self.ortho_im[i], 1)
            # Binarize input data
            if self.binarize_encode:
                encoded_vec = vsax.hv_binarize(encoded_vec, threshold, self.hv_type)
            return encoded_vec

    # Create the model
    vsa_char_model = vsaCharModel(
        hv_size=1024,
        hv_type="bipolar",
        num_ortho_im=35,
        num_cim=11,
        cim_max_is_ortho=True,
        class_list=list(range(10)),
        gen_type="ri",
        gen_ri_p_dense=0.5,
        gen_lfsr_base_seed=42,
    )

    # Train the model
    vsa_char_model.train_model(char_recog_dict)

    # Test the model
    accuracy = vsa_char_model.test_model(char_recog_dict)

    # Print model statistics
    vsa_char_model.print_model_stats()

    # Expected output is around 98%
    if accuracy >= 0.98:
        print("VSAX Model Pass!")
    else:
        raise ValueError("VSAX Model did not achieve expected accuracy.")
