# :notebook_with_decorative_cover: Datasets for HDC
- This directory contains several datasets used for several HDC applications
- Take note that some of these are compressed for the sake of demonstration
  - For example, the MNIST data set is in binary instead of `int8`

# :wrench: Useful Python Programs
- `extract_mnist.py`: Used to extract the MNIST dataset. No need to run this as there is already data stored as github release assets. See below.

# :briefcase: Dataset List
- :capital_abcd: **Character Recognition**: It's already stored under the `data_set/char_recog` directory.
- :one: :two: :three: **Digit Recognition**: The `data_set/digit_recog` is generated after running the `digit_recog.py` HDC experiment. The data comes from the uploaded release [asset](https://github.com/KULeuven-MICAS/hypercorex/releases/tag/ds_hdc_digit_recog_v.0.0.1).
- :earth_asia: **Language Recognition**: This data first originated from the [Language Recognition](https://github.com/abbas-rahimi/HDC-Language-Recognition). But here the testing data was compressed into a single text file. The `data_set/lang_recog` directory is generated after running the `lang_recog.py` HDC experiment. It generates 2 sub directories for training and testing texts. The compressed data comes from the uploaded release [asset](https://github.com/KULeuven-MICAS/hypercorex/releases/tag/ds_hdc_digit_recog_v.0.0.1)