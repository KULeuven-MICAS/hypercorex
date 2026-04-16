//---------------------------
// Copyright 2024 KU Leuven
// Ryan Antonio <ryan.antonio@esat.kuleuven.be>
//
// Module: Multi-In Bundler Set
// Description:
// This is a bundler set supporting
// multiple HV inputs at a time.
//
// Parameters:
// - HVDimension:  Dimension of the input hypervectors (and output counter array)
// - NumInputs:    Number of input hypervectors to be bundled together
// - CounterWidth: Bit width of the internal counter (and output)
//
// Inputs and Outputs:
// - clk_i:       Clock input for the counter registers
// - rst_ni:      Active-low reset for the counter registers
// - clr_i:       Synchronous clear for the counters (resets to zero on next clock edge)
// - hv_i:        2D array of input hypervectors (NumInputs x HVDimension) to be bundled together
// - valid_i:     Array of valid signals (NumInputs elements) indicating which input hypervectors are valid for this cycle
// - counter_o:   2D array of output counters (HVDimension x CounterWidth) representing the bundled result of the input hypervectors
// - binarized_hv_o: Array of binarized output bits (HVDimension elements) obtained by thresholding the counters (e.g., sign bit
//---------------------------

module multi_in_bundler_set#(
  parameter int unsigned HVDimension  = 512,
  parameter int unsigned NumInputs    = 4,
  parameter int unsigned CounterWidth = 8
)(
  input  logic                           clk_i,
  input  logic                           rst_ni,
  input  logic        [ HVDimension-1:0] hv_i [NumInputs],
  input  logic        [   NumInputs-1:0] valid_i,
  input  logic                           clr_i,
  output logic signed [CounterWidth-1:0] counter_o [HVDimension],
  output logic        [ HVDimension-1:0] binarized_hv_o
);

  //---------------------------
  // Remapping input hypervector
  //---------------------------
  logic [NumInputs-1:0] remapped_hv [HVDimension];

  always_comb begin
    for (int i = 0; i < NumInputs; i++) begin
      for (int j = 0; j < HVDimension; j++) begin
        remapped_hv[j][i] = hv_i[i][j];
      end
    end
  end

  //---------------------------
  // Multi-in bundler units
  //---------------------------
  genvar i;
  for(i = 0; i < HVDimension; i++ )begin: gen_multi_in_bundler_units
    multi_in_bundler_unit #(
      .CounterWidth ( CounterWidth     ),
      .NumInputs    ( NumInputs        )
    ) i_multi_in_bundler_unit (
      .clk_i        ( clk_i            ),
      .rst_ni       ( rst_ni           ),
      .bit_i        ( remapped_hv [i]  ),
      .valid_i      ( valid_i          ),
      .clr_i        ( clr_i            ),
      .counter_o    ( counter_o[i]     )
    );
  end

  //---------------------------
  // Sign binarization
  //---------------------------
  always_comb begin
    for(int i = 0; i < HVDimension; i++) begin
      binarized_hv_o[i] = (counter_o[i][CounterWidth-1]) ? 1'b0 : 1'b1;
    end
  end
endmodule
