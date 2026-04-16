//---------------------------
// Copyright 2024 KU Leuven
// Ryan Antonio <ryan.antonio@esat.kuleuven.be>
//
// Module: Multi-In Bundler Set
// Description:
// This is a bundler set supporting
// multiple HV inputs at a time.
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
