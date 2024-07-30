//---------------------------
// Copyright 2024 KU Leuven
// Ryan Antonio <ryan.antonio@esat.kuleuven.be>
//
// Module: Bundler Set
// Description:
// A wrapper for vectorizing the
// bundler unit to hypervector dimension
//---------------------------

module bundler_set#(
  parameter int unsigned HVDimension  = 512,
  parameter int unsigned CounterWidth = 8
)(
  input  logic clk_i,
  input  logic rst_ni,
  input  logic [HVDimension-1:0] hv_i,
  input  logic valid_i,
  input  logic clr_i,
  output logic signed [HVDimension-1:0][CounterWidth-1:0] counter_o,
  output logic [HVDimension-1:0] binarized_hv_o
);

  //---------------------------
  // Bundler units
  //---------------------------

  genvar i;
  for(i = 0; i < HVDimension; i++ )begin: gen_bundler_units
    bundler_unit #(
      .CounterWidth (CounterWidth )
    ) i_bundler_unit (
      .clk_i        (clk_i        ),
      .rst_ni       (rst_ni       ),
      .bit_i        (hv_i[i]      ),
      .valid_i      (valid_i      ),
      .clr_i        (clr_i        ),
      .counter_o    (counter_o[i] )
    );
  end

  //---------------------------
  // Combinational threshold
  //---------------------------

  always_comb begin
    for(int i = 0; i < HVDimension; i++) begin
      binarized_hv_o[i] = (counter_o[i] >= 0) ? 1'b1 : 1'b0;
    end
  end


endmodule
