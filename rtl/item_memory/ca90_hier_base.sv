
//---------------------------
// Copyright 2024 KU Leuven
// Ryan Antonio <ryan.antonio@esat.kuleuven.be>
//
// Module: CA90 Item Memory Hierarchical Base
// Description:
// This is a template to generate the CA90
// base HV. A template is needed due to SV limitations.
//---------------------------

module ca90_hier_base #(
  parameter int unsigned HVDimension = 512,
  parameter int unsigned SeedWidth   = 32
)(
  // Inputs
  input  logic [  SeedWidth-1:0] seed_hv_i,
  output logic [HVDimension-1:0] base_hv_o
);

  //---------------------------
  // Wires
  //---------------------------
  logic [31:0] ca90_layer_out_0;
  logic [63:0] ca90_layer_out_1;
  logic [127:0] ca90_layer_out_2;
  logic [255:0] ca90_layer_out_3;

  logic [63:0] ca90_layer_in_1;
  logic [127:0] ca90_layer_in_2;
  logic [255:0] ca90_layer_in_3;

  //---------------------------
  // Wiring concatenation
  //---------------------------
    assign ca90_layer_in_1 = {ca90_layer_out_0, seed_hv_i};
    assign ca90_layer_in_2 = {ca90_layer_out_1, ca90_layer_in_1};
    assign ca90_layer_in_3 = {ca90_layer_out_2, ca90_layer_in_2};

  //---------------------------
  // CA 90 modules
  //---------------------------

  ca90_unit #(
    .Dimension   ( 32 )
  ) i_ca90_im_0 (
    .vector_i    (        seed_hv_i ),
    .shift_amt_i (                1 ),
    .vector_o    ( ca90_layer_out_0 )
  );

  ca90_unit #(
    .Dimension   ( 64 )
  ) i_ca90_im_1 (
    .vector_i    (  ca90_layer_in_1 ),
    .shift_amt_i (                1 ),
    .vector_o    ( ca90_layer_out_1 )
  );

  ca90_unit #(
    .Dimension   ( 128 )
  ) i_ca90_im_2 (
    .vector_i    (  ca90_layer_in_2 ),
    .shift_amt_i (                1 ),
    .vector_o    ( ca90_layer_out_2 )
  );

  ca90_unit #(
    .Dimension   ( 256 )
  ) i_ca90_im_3 (
    .vector_i    (  ca90_layer_in_3 ),
    .shift_amt_i (                1 ),
    .vector_o    ( ca90_layer_out_3 )
  );

  //---------------------------
  // Concatenating for output
  //---------------------------

  assign base_hv_o = {
    ca90_layer_out_3,
    ca90_layer_out_2,
    ca90_layer_out_1,
    ca90_layer_out_0,
    seed_hv_i
  };

endmodule
