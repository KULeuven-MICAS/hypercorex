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
  parameter int unsigned NumOps        = 4,
  parameter int unsigned NumOpsWidth   = $clog2(NumOps),
  parameter int unsigned MaxShiftAmt   = 128,
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
  //---------------------------
  logic [HVDimension-1:0] circular_shift_res;

  always_comb begin
    circular_shift_res = (A_i >> shift_amt_i) | (A_i << (HVDimension - shift_amt_i));
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
      2'b01:   C_o = A_i;
      2'b10:   C_o = B_i;
      2'b11:   C_o = circular_shift_res;
      default: C_o = A_i ^ B_i;
    endcase
  end

endmodule
