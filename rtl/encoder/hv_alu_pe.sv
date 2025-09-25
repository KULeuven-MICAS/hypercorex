//---------------------------
// Copyright 2024 KU Leuven
// Ryan Antonio <ryan.antonio@esat.kuleuven.be>
//
// Module: Hypervector ALU Processing Element
// Description:
// Combinational ALU to process basic element-wise
// operations for hypervectors
//---------------------------
module hv_alu_pe #(
  parameter int unsigned HVDimension   = 512,
  parameter int unsigned NumOps        = 8,
  parameter int unsigned NumOpsWidth   = $clog2(NumOps),
  parameter int unsigned MaxShiftAmt   = 4,
  parameter int unsigned ShiftWidth    = $clog2(MaxShiftAmt)
)(
  // Inputs
  input  logic [HVDimension-1:0] A_i,
  input  logic [HVDimension-1:0] B_i,
  // Outputs
  output logic [HVDimension-1:0] C_o,
  // Control ports
  input  logic [NumOpsWidth-1:0] op_i,
  input  logic [ ShiftWidth-1:0] shift_amt_i
);

  //---------------------------
  // Logic for shifting
  //
  // Shifting modes:
  // 0: 1 shift
  // 1: 4 shift
  // 2: 8 shift
  // 3: 16 shift
  //---------------------------
  logic [HVDimension-1:0] circular_shift_right;
  logic [HVDimension-1:0] circular_shift_left;

  // Doing selections through wire slicing
  // rather than actual shifts to optimize synthesis

  // Shift right
  always_comb begin
    case (shift_amt_i)
      default: circular_shift_right = {A_i[   0], A_i[ HVDimension-1:1]};
            1: circular_shift_right = {A_i[ 3:0], A_i[ HVDimension-1:4]};
            2: circular_shift_right = {A_i[ 7:0], A_i[ HVDimension-1:8]};
            3: circular_shift_right = {A_i[15:0], A_i[HVDimension-1:16]};
    endcase
  end

  // Shift left
  always_comb begin
    case (shift_amt_i)
      default: circular_shift_left = {A_i[HVDimension-2:0],  A_i[HVDimension-1]};
            1: circular_shift_left = {A_i[HVDimension-5:0],  A_i[HVDimension-1:HVDimension-4]};
            2: circular_shift_left = {A_i[HVDimension-9:0],  A_i[HVDimension-1:HVDimension-8]};
            3: circular_shift_left = {A_i[HVDimension-17:0], A_i[HVDimension-1:HVDimension-16]};
    endcase
  end

  //---------------------------
  // Logic table:
  // op_i | operation         |
  // 0    | XOR               |
  // 1    | A_i pass through  |
  // 2    | B_i pass through  |
  // 3    | Circular shifts   |
  //---------------------------
  always_comb begin : alu_logic
    case (op_i)
      3'b001:  C_o = A_i;
      3'b010:  C_o = B_i;
      3'b011:  C_o = circular_shift_right;
      3'b100:  C_o = circular_shift_left;
      3'b101:  C_o = circular_shift_right ^ B_i;
      default: C_o = A_i ^ B_i;
    endcase
  end

endmodule
