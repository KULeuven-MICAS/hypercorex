//---------------------------
// Copyright 2024 KU Leuven
// Ryan Antonio <ryan.antonio@esat.kuleuven.be>
//
// Module: ROM Item Memory
// Description:
// This is an alternative implementation for
// the item memory. This is to check whether,
// the CA90 or this implementation has less area
//---------------------------

module rom_item_memory #(
  parameter int unsigned HVDimension = 512,
  parameter int unsigned NumTotIm    = 1024,
  parameter int unsigned SeedWidth   = 32,
  // Don't touch parameters
  parameter int unsigned ImSelWidth  = $clog2(NumTotIm)
)(
  // Inputs
  input  logic [ ImSelWidth-1:0] im_sel_a_i,
  input  logic [ ImSelWidth-1:0] im_sel_b_i,
  // Outputs
  output logic [HVDimension-1:0] im_a_o,
  output logic [HVDimension-1:0] im_b_o
);

  logic [HVDimension-1:0] item_memory [NumTotIm];

% for idx, item in enumerate(cfg):
  assign item_memory[${idx}] = ${len(item)}'b${item};
% endfor

  //---------------------------
  // Read output ports
  //---------------------------
  always_comb begin
    im_a_o = item_memory[im_sel_a_i];
    im_b_o = item_memory[im_sel_b_i];
  end

endmodule
