# :hammer: Tests Directory

This directory has a mix of unit tests and system tests. Each are briefly described below:

## :zap: Utility Files

:zap: [`set_parameters.py`](set_parameters.py): contains all parameters used for testing the Hypercorex

:zap: [`util.py`](util.py): contains utility functions used in all other tests.

## :nut_and_bolt: Fucntional Unit Tests

:nut_and_bolt: [`test_assoc_mem.py`](test_assoc_mem.py): associative memory capabilities.

:nut_and_bolt: [`test_bundler_set.py`](test_bundler_set.py): a bundler set (i.e., multiple bundler units).

:nut_and_bolt: [`test_bundler_unit.py`](test_bundler_unit.py): a single bundler unit test.

:nut_and_bolt: [`test_ca90_item_memory.py`](test_ca90_item_memory.py): tests the orthogonal projection of the CA90 item memory.

:nut_and_bolt: [`test_cim.py`](test_cim.py): tests the continuous item memory.

:nut_and_bolt: [`test_csr.py`](test_csr.py): functionality and read-write capabilities of the CSR block.

:nut_and_bolt: [`test_data_slicer.py`](test_data_slicer.py): checks functionality of the data slicer for different bit-widths.

:nut_and_bolt: [`test_fifo.py`](test_fifo.py): simple FIFO checker.

:nut_and_bolt: [`test_fixed_ca90_unit.py`](test_fixed_ca90_unit.py): tests the single CA90 XOR and shift unit.

:nut_and_bolt: [`test_ham_dist.py`](test_ham_dist.py): simple checker if the Hamming distance unit counts correctly.

:nut_and_bolt: [`test_hv_alu_pe.py`](test_hv_alu_pe.py): unit checker for the logic of the encoder processing element.

:nut_and_bolt: [`test_hv_encoder.py`](test_hv_encoder.py): the main encoder module test.

:nut_and_bolt: [`test_inst_control.py`](test_inst_control.py): test the loops of the instruction control.

:nut_and_bolt: [`test_inst_decode.py`](test_inst_decode.py): check the decoded outputs of the instruction decoder.

:nut_and_bolt: [`test_item_memory_top.py`](test_item_memory_top.py): check the top-level of the item memory block.

:nut_and_bolt: [`test_item_memory.py`](test_item_memory.py): check the combined orthogonal iM and CiM.

:nut_and_bolt: [`test_reg_file_1w1r.py`](test_reg_file_1w1r.py): test register file for 1 write and 1 read port.

:nut_and_bolt: [`test_reg_file_1w2r.py`](test_reg_file_1w2r.py): test register file for 1 write and 2 read ports.

:nut_and_bolt: [`test_rom_item_memory.py`](test_rom_item_memory.py): read-only item memory.

:nut_and_bolt: [`test_update_counter.py`](test_update_counter.py): test the update counter for automatic fetching.

## :iphone: System Tests

:iphone: [`test_hypercorex_am_search.py`](test_hypercorex_am_search.py): checker if the AM continuous search works.

:iphone: [`test_hypercorex_char_recog_data_slice.py`](test_hypercorex_char_recog_data_slice.py): checker data slicing capabilities works well with the character recognition example.

:iphone: [`test_hypercorex_char_recog.py`](test_hypercorex_char_recog.py): character recognition application but the pixel values and pixel locations are binded instead of permuting if white or black.

:iphone: [`test_hypercorex_csr.py`](test_hypercorex_csr.py): also a CSR test but uses the system control ports for checking read-write operations.

:iphone: [`test_hypercorex_imab_bind.py`](test_hypercorex_imab_bind.py): tests if the continuous binding and outputting high-dimensional data are consistent.

:iphone: [`test_hypercorex_ortho_im_only.py`](test_hypercorex_ortho_im_only.py): checks the contests of the internal orthogonal item memory.

:iphone: [`test_tb_hypercorex.py`](test_tb_hypercorex.py): tests the testbench only.
