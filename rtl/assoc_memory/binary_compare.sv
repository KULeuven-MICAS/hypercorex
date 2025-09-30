//---------------------------
// Copyright 2024 KU Leuven
// Ryan Antonio <ryan.antonio@esat.kuleuven.be>
//
// Module: Binary compare for finding
//         the greatest hamming similarity
// Description:
// This module is to find the greatest hamming similarity
// but a bit fixed as of the moment to have a working version
// Here, we do a binary search tree to find the min value
// since Hamming distance measures amount of differing bits
// and we want the maminimum similarity
//---------------------------

module binary_compare #(
    parameter int unsigned CompareRegsWidth = 16,
    // Don't touch!
    parameter int unsigned NumCompareRegs   = 32,
    parameter int unsigned NumCompareWidth  = $clog2(NumCompareRegs)
)(
    input  logic [  NumCompareRegs-1:0][CompareRegsWidth-1:0] compare_regs ,
    output logic [CompareRegsWidth-1:0] min_value_o,
    output logic [ NumCompareWidth-1:0] min_index_o
);

    //---------------------------
    // Wires and logic
    //---------------------------
    logic [NumCompareRegs/2-1:0] [CompareRegsWidth-1:0]  stage1_vals ;
    logic [NumCompareRegs/2-1:0] [ NumCompareWidth-1:0]  stage1_idxs ;

    logic [NumCompareRegs/4-1:0] [CompareRegsWidth-1:0]  stage2_vals ;
    logic [NumCompareRegs/4-1:0] [ NumCompareWidth-1:0]  stage2_idxs ;

    logic [NumCompareRegs/8-1:0] [CompareRegsWidth-1:0]  stage3_vals ;
    logic [NumCompareRegs/8-1:0] [ NumCompareWidth-1:0]  stage3_idxs ;

    logic [NumCompareRegs/16-1:0] [CompareRegsWidth-1:0] stage4_vals ;
    logic [NumCompareRegs/16-1:0] [ NumCompareWidth-1:0] stage4_idxs ;

    logic [CompareRegsWidth-1:0] stage5_val;
    logic [ NumCompareWidth-1:0] stage5_idx;

    //---------------------------
    // Stage 1 - 16 comparisons
    //---------------------------
    genvar i;
    generate
        for (i = 0; i < NumCompareRegs/2; i++) begin : gen_compare_stage_1
            always_comb begin
                if (compare_regs[2*i] <= compare_regs[2*i+1]) begin
                    stage1_vals[i] = compare_regs[2*i];
                    stage1_idxs[i] = 2*i;
                end else begin
                    stage1_vals[i] = compare_regs[2*i+1];
                    stage1_idxs[i] = 2*i+1;
                end
            end
        end
    endgenerate

    //---------------------------
    // Stage 2 - 8 comparisons
    //---------------------------
    generate
        for (i = 0; i < NumCompareRegs/4; i++) begin : gen_compare_stage_2
            always_comb begin
                if (stage1_vals[2*i] <= stage1_vals[2*i+1]) begin
                    stage2_vals[i] = stage1_vals[2*i];
                    stage2_idxs[i] = stage1_idxs[2*i];
                end else begin
                    stage2_vals[i] = stage1_vals[2*i+1];
                    stage2_idxs[i] = stage1_idxs[2*i+1];
                end
            end
        end
    endgenerate

    //---------------------------
    // Stage 3 - 4 comparisons
    //---------------------------
    generate
        for (i = 0; i < NumCompareRegs/8; i++) begin : gen_compare_stage_3
            always_comb begin
                if (stage2_vals[2*i] <= stage2_vals[2*i+1]) begin
                    stage3_vals[i] = stage2_vals[2*i];
                    stage3_idxs[i] = stage2_idxs[2*i];
                end else begin
                    stage3_vals[i] = stage2_vals[2*i+1];
                    stage3_idxs[i] = stage2_idxs[2*i+1];
                end
            end
        end
    endgenerate

    //---------------------------
    // Stage 4 - 2 comparisons
    //---------------------------
    generate
        for (i = 0; i < NumCompareRegs/16; i++) begin : gen_compare_stage_4
            always_comb begin
                if (stage3_vals[2*i] <= stage3_vals[2*i+1]) begin
                    stage4_vals[i] = stage3_vals[2*i];
                    stage4_idxs[i] = stage3_idxs[2*i];
                end else begin
                    stage4_vals[i] = stage3_vals[2*i+1];
                    stage4_idxs[i] = stage3_idxs[2*i+1];
                end
            end
        end
    endgenerate

    //---------------------------
    // Stage 5 - Final comparison
    //---------------------------
    always_comb begin
        if (stage4_vals[0] <= stage4_vals[1]) begin
            stage5_val = stage4_vals[0];
            stage5_idx = stage4_idxs[0];
        end else begin
            stage5_val = stage4_vals[1];
            stage5_idx = stage4_idxs[1];
        end
    end

    //---------------------------
    // Output assignments
    //---------------------------
    assign min_value_o = stage5_val;
    assign min_index_o = stage5_idx;

endmodule
