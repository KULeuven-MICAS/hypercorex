//---------------------------
// Copyright 2024 KU Leuven
// Ryan Antonio <ryan.antonio@esat.kuleuven.be>
//
// Module: Fixed CA90 Item Memory Generation Unit
// Description:
// This is the base CA90 generation unit
// but with fixed shifts only. This change
// becomes necessary only because CA90 here is fixed
//---------------------------

module fixed_ca90_unit #(
  parameter int unsigned Dimension = 512,
  parameter int unsigned ShiftAmt  = 1
)(
  // Inputs
  input  logic [ Dimension-1:0] vector_i,
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
    vector_left_shift  = {
      vector_i[(Dimension-ShiftAmt)-1:0],
      vector_i[Dimension-1:(Dimension-ShiftAmt)]
    };
    vector_right_shift = {
      vector_i[ShiftAmt-1:0],
      vector_i[Dimension-1:ShiftAmt]
    };
    vector_o = vector_left_shift ^ vector_right_shift;
  end




endmodule
