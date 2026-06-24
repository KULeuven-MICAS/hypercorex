# VSAX Applications

This directory contains information about the different programs for various applications.

## List of Programs and their Descriptions
- `vsax_bin_digit_recog` - This is a simple binary digit recognition program. It uses a pre-processed MNIST data set.
- `vsax_bin_idlvl_digit_recog` - Similar to bin digit, but instead of permuting with white pixels, this uses a separate HV for the black and white pixels.
- `vsax_digit_recog` - This uses MNIST data sets in their grey-scale values (0-255) and not binary inputs. Therefore it uses ID-level but with matrix-multiplications.
- `vsax_bin_dna_recog` - This does a gene recognition based on the sequences of the DNA bases.
- `vsax_bin_lang_recog` - This is for the language recognition that uses `ngram` encoding.
- `vsax_bin_isolet_recog` - This is for voice recognitio and uses ID-level encoding.
