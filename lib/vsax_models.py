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

# ============================================================================-------
# Main VSA Model class
# ============================================================================-------


class vsaModel:
    """
    Base class for VSA models.

    Parameters:
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
    """

    def __init__(
        self,
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
        self.tqdm_train_dbg = True
        self.tqdm_retrain_dbg = True
        self.tqdm_test_dbg = True

    # Main encoding function
    def encode(self, item_data):
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
        """
        for class_label in range(self.num_classes):
            data_len = len(X_train[class_label])

            # Non-binarized training
            for item_num in tqdm(
                range(data_len),
                desc=f"Training class {class_label}",
                disable=not self.tqdm_train_dbg,
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

    # Testing function
    def test_model(self, X_test):
        """
        Test the VSA model using the provided test data.
        Parameters:
            X_test (list): A list of test data for each class.
        Returns:
            float: The overall accuracy of the model.
        """
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
                disable=not self.tqdm_test_dbg,
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
        print(f"HV Size: {self.hv_size}")
        print(f"HV Type: {self.hv_type}")
        print(f"Number of Orthogonal IMs: {self.num_ortho_im}")
        print(f"Number of Continuous IMs: {self.num_cim}")
        print(f"Number of Classes: {self.num_classes}")

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
