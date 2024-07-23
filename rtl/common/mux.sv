//---------------------------
// Copyright 2024 KU Leuven
// Ryan Antonio <ryan.antonio@esat.kuleuven.be>
//
// Module: MUX
// Description:
// A simple MUX with variable size
//---------------------------

module mux #(
  parameter int unsigned DataWidth   = 32,
  parameter int unsigned NumSel      = 4,
  // Don't touch!
  parameter int unsigned NumSelWidth = $clog2(NumSel)
)(
  input  logic             [NumSelWidth-1:0] sel_i,
  input  logic [NumSel-1:0][  DataWidth-1:0] signal_i,
  output logic             [  DataWidth-1:0] signal_o
);

  assign signal_o = signal_i[sel_i];

endmodule
