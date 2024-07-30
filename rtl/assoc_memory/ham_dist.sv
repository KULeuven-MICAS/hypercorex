//---------------------------
// Copyright 2024 KU Leuven
// Ryan Antonio <ryan.antonio@esat.kuleuven.be>
//
// Module: Hamming Distance Unit
// Description:
// Fully combinational hamming distance unit
// First creates an XOR vector
// Then does a fully-combinational population count
//---------------------------

module ham_dist #(
  parameter int unsigned HVDimension = 512,
  parameter int unsigned DataWidth   = 32
)(
  // Inputs
  input  logic [HVDimension-1:0] A_i,
  input  logic [HVDimension-1:0] B_i,
  // Outputs
  output logic [  DataWidth-1:0] hamming_dist_o
);

  //---------------------------
  // Logic for XOR vector
  //---------------------------
  logic [HVDimension-1:0] xor_vector;

  assign xor_vector = A_i ^ B_i;

  always_comb begin
    // A necessary initialization
    // to set other values
    hamming_dist_o = {HVDimension{1'b0}};

    // This is still synthesizable as a tree
    for (int i = 0; i < HVDimension; i++) begin
        hamming_dist_o = hamming_dist_o + xor_vector[i];
    end
  end


endmodule
