//---------------------------
// Copyright 2024 KU Leuven
// Ryan Antonio <ryan.antonio@esat.kuleuven.be>
//
// Module: CA90 Item Memory Generation Unit
// Description:
// This is the base CA90 generation unit
// It is parametrizable to accommodate dimension changes
//---------------------------

module ca90_unit #(
  parameter int unsigned Dimension    = 512,
  parameter int unsigned MaxShiftAmt  = 128,
  // Don't touch!
  parameter int unsigned ShiftWidth   = $clog2(MaxShiftAmt)
)(
  // Inputs
  input  logic [ Dimension-1:0] vector_i,
  input  logic [ShiftWidth-1:0] shift_amt_i,
  // Outputs
  output logic [ Dimension-1:0] vector_o
);

  //---------------------------
  // Wires
  //---------------------------
  logic [Dimension-1:0] vector_left_shift;
  logic [Dimension-1:0] vector_right_shift;

  //---------------------------
  // CA90 Logic
  //---------------------------
  always_comb begin
    vector_left_shift  = (vector_i << shift_amt_i) | (vector_i >> (Dimension - shift_amt_i));
    vector_right_shift = (vector_i >> shift_amt_i) | (vector_i << (Dimension - shift_amt_i));
    vector_o           = vector_left_shift ^ vector_right_shift;
  end




endmodule
