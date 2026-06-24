# set TCL_DIR [file dirname [file normalize [info script]]]
# set ROOT_DIR $TCL_DIR/../..
set ROOT_DIR "/users/micas/rantonio/no_backup/kul_main/hypercorex"
set RTL_DIR "$ROOT_DIR/rtl"
set WORK_DIR "$ROOT_DIR/questa/work_vsim"

if {[catch { vlog -incr -sv \
    -svinputport=compat \
    -override_timescale 1ns/1ps \
    -timescale 1ns/1ps \
    -work $WORK_DIR  \
    +define+  \
    "$RTL_DIR/common/adder_tree.sv" \
    "$RTL_DIR/common/latch_memory.sv" \
    "$RTL_DIR/item_memory/rom_lfsr_item_memory.sv" \
    "$RTL_DIR/encoder/multi_in_bundler_unit.sv" \
    "$RTL_DIR/encoder/multi_in_bundler_set.sv" \
    "$RTL_DIR/encoder/qhv.sv" \
    "$RTL_DIR/encoder/id_level_encoder.sv" \
    "$RTL_DIR/assoc_memory/ham_dist.sv" \
    "$RTL_DIR/assoc_memory/binary_compare.sv" \
    "$RTL_DIR/assoc_memory/bin_sim_search.sv" \
    "$RTL_DIR/assoc_memory/assoc_mem_top.sv" \
    "$RTL_DIR/system_top/vsax_id_level_top.sv" \
    "$RTL_DIR/tb/tb_vsax_id_level_top.sv" \
}]} {return 1}

return 0
