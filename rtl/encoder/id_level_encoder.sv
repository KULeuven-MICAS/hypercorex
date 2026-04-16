//---------------------------
// Copyright 2024 KU Leuven
// Ryan Antonio <ryan.antonio@esat.kuleuven.be>
//
// Module: ID-level encoder
// Description:
// This is a hardwired encoder that does the
// ID-level encoding for the input tokens.
// ID-level is simply an equivalent of a MAC
// but since we dill with binary vectors it's
// an XOR operation that is combined per bit.
// In this module, we support multi-input as well.
//
// Parameters:
// - HVDimension: The dimensionality of the hypervectors
// - NumInputs: The number of input tokens to encode
// - CounterWidth: The width of the counter for the spatial bundler
//
// Inputs and Outputs:
// - clk_i: Clock input
// - rst_ni: Active-low reset input
// - clr_i: Clear signal for the spatial bundler
// - valid_i: Valid signals for each input token
// - hv_id_i: Hypervector IDs for each input token
// - hv_level_i: Hypervector levels for each input token
// - hv_encoded_o: The encoded hypervectors for each dimension
// - hv_bin_encoded_o: The binarized encoded hypervector
//---------------------------

module id_level_encoder #(
  parameter int unsigned HVDimension  = 512,
  parameter int unsigned NumInputs    = 4,
  parameter int unsigned CounterWidth = 8
)(
  // Clocks and reset
  input  logic                           clk_i,
  input  logic                           rst_ni,
  // Other input logic
  input  logic                           clr_i,
  // Inputs
  input  logic        [   NumInputs-1:0] valid_i,
  input  logic        [ HVDimension-1:0] hv_id_i          [NumInputs],
  input  logic        [ HVDimension-1:0] hv_level_i       [NumInputs],
  // Outputs
  output logic signed [CounterWidth-1:0] hv_encoded_o     [HVDimension],
  output logic        [ HVDimension-1:0] hv_bin_encoded_o
);

  //---------------------------
  // Wires
  //---------------------------
  logic [HVDimension-1:0] hv_xored [NumInputs];

  //---------------------------
  // ID-level encoding logic
  //---------------------------
  // Simply an XOR array
  always_comb begin: comb_xor_array
    for (int i = 0; i < NumInputs; i++) begin
      for (int j = 0; j < HVDimension; j++) begin
        hv_xored[i][j] = hv_id_i[i][j] ^ hv_level_i[i][j];
      end
    end
  end

  //---------------------------
  // Spatial bundler
  //---------------------------
  multi_in_bundler_set #(
    .HVDimension    ( HVDimension      ),
    .NumInputs      ( NumInputs        ),
    .CounterWidth   ( CounterWidth     )
  ) i_multi_in_bundler_set (
    .clk_i          ( clk_i            ),
    .rst_ni         ( rst_ni           ),
    .clr_i          ( clr_i            ),
    .hv_i           ( hv_xored         ),
    .valid_i        ( valid_i          ),
    .counter_o      ( hv_encoded_o     ),
    .binarized_hv_o ( hv_bin_encoded_o )
  );

endmodule
