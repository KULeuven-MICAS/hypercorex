//---------------------------
// Copyright 2024 KU Leuven
// Ryan Antonio <ryan.antonio@esat.kuleuven.be>
//
// Module: CA90 Item Memory
// Description:
// This is the base CA90 item memory
//---------------------------

module ca90_item_memory #(
  parameter int unsigned HVDimension   = 512,
  parameter int unsigned NumImElements = 1024,
  // Don't touch parameters
  parameter int unsigned ImSelWidth    = $clog2(NumImElements)
)(
  // Inputs
  input  logic [HVDimension-1:0] seed_hv_i,
  input  logic [ ImSelWidth-1:0] im_sel_a_i,
  input  logic [ ImSelWidth-1:0] im_sel_b_i,
  // Outputs
  output logic [HVDimension-1:0] im_a_o,
  output logic [HVDimension-1:0] im_b_o
);

  //---------------------------
  // Wires
  //---------------------------
  logic [NumImElements-1:0][HVDimension-1:0] item_memory;

  assign item_memory[0] = seed_hv_i;

  //---------------------------
  // Generate item memory HVs with CA90
  //---------------------------
  genvar i;
  for (i=0; i < NumImElements-1; i=i+1) begin: gen_item_hvs
    ca90_unit #(
      .Dimension   (      HVDimension )
    ) i_ca90_im_hv (
      .vector_i    (   item_memory[i] ),
      .shift_amt_i (                1 ),
      .vector_o    ( item_memory[i+1] )
    );
  end

  //---------------------------
  // Read output ports
  //---------------------------
  always_comb begin
    im_a_o = item_memory[im_sel_a_i];
    im_b_o = item_memory[im_sel_b_i];
  end

endmodule
