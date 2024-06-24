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
  input  logic binarize_i,
  output logic signed [HVDimension-1:0][CounterWidth-1:0] counter_o
);

  genvar i;
  for(i = 0; i < HVDimension; i++ )begin
    bundler_unit #(
      .CounterWidth (CounterWidth )
    ) i_bundler_unit (
      .clk_i        (clk_i        ),
      .rst_ni       (rst_ni       ),
      .bit_i        (hv_i[i]      ),
      .valid_i      (valid_i      ),
      .clr_i        (clr_i        ),
      .binarize_i   (binarize_i   ),
      .counter_o    (counter_o[i] )
    );
  end

endmodule