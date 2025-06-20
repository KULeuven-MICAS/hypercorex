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
- :ab: **ISOLET Recognition**: Technically speech recognition where someone says a letter and the classification task is to identify which letter of the alphabet it is. Data comes from the [ISOLET dataset](https://archive.ics.uci.edu/dataset/54/isolet). The data was originally 617 frequency features that ranges from $[-1,+1]$ but the [uploaded asset](https://github.com/KULeuven-MICAS/hypercorex/releases/tag/ds_hdc_isolet_recog_v.0.01) pre-processes the data into $[0,255]$ range for simplicity.