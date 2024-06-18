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
  parameter int unsigned HVDimension  = 512,
  parameter int unsigned NumOps       = 4,
  parameter int unsigned NumOpsWidth  = $clog2(NumOps),
  parameter int unsigned PermuteWidth = 5
)(
  // Inputs
  input  logic [ HVDimension-1:0] A_i,
  input  logic [ HVDimension-1:0] B_i,
  // Outputs
  output logic [ HVDimension-1:0] C_o,
  // Control ports
  input  logic [ NumOpsWidth-1:0] op_i
);

  //---------------------------
  // Logic table:
  // op_i | operation                    |
  // 0    | XOR                          |
  // 1    | AND                          |
  // 2    | OR                           |
  //---------------------------
  always_comb begin : alu_logic
    case (op_i)
      2'b01:   C_o = A_i & B_i;
      2'b10:   C_o = A_i | B_i;
      default: C_o = A_i ^ B_i;
    endcase
  end

endmodule
