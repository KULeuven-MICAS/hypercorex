//---------------------------
// Copyright 2024 KU Leuven
// Ryan Antonio <ryan.antonio@esat.kuleuven.be>
//
// Module: CA90 Item Memory
// Description:
// This is the base CA90 item memory
// Note that this item memory
// will be a bit more customized and less
// flexible. Only the dimension size can change.
//
// Because of the CA90 limitations despite being
// a good compressive mechanism, we need to generate
// 8 item memories to generate 1024 cases
//
// Therevore we need 8 different seeds for this!
//---------------------------

module ca90_item_memory #(
  parameter int unsigned HVDimension   = 512,
  parameter int unsigned NumTotIm      = 1024,
  parameter int unsigned NumPerImBank  = 128,
  parameter int unsigned SeedWidth     = 32,
  // Don't touch parameters
  parameter int unsigned Ca90ImPerm    = 7,
  parameter int unsigned NumImSets     = NumTotIm/NumPerImBank,
  parameter int unsigned ImSelWidth    = $clog2(NumTotIm)
)(
  // Inputs
  input  logic [  NumImSets-1:0][SeedWidth-1:0] seed_hv_i,
  input  logic [ ImSelWidth-1:0] im_sel_a_i,
  input  logic [ ImSelWidth-1:0] im_sel_b_i,
  // Outputs
  output logic [HVDimension-1:0] im_a_o,
  output logic [HVDimension-1:0] im_b_o
);
  //---------------------------
  // Some working variable
  //---------------------------
  genvar i, j;

  //---------------------------
  // Wires
  //---------------------------
  logic [NumTotIm-1:0][HVDimension-1:0] item_memory;
  logic [NumImSets-1:0][NumPerImBank-1:0][HVDimension-1:0] item_memory_bases;

  //---------------------------
  // Base Item Memory
  //---------------------------
  for ( i = 0; i < NumImSets; i++) begin: gen_per_im_set

    // First generate the base
    ca90_hier_base #(
      .HVDimension ( HVDimension    ),
      .SeedWidth   ( SeedWidth      )
    ) i_ca90_hier_base (
      .seed_hv_i   ( seed_hv_i[i]            ),
      .base_hv_o   ( item_memory_bases[i][0] )
    );

    // Generate IM set with all other bases
    for ( j = 0; j < NumPerImBank-1; j++) begin: gen_per_im_bank
      ca90_unit #(
        .Dimension   (               HVDimension )
      ) i_ca90_im_hv (
        .vector_i    (   item_memory_bases[i][j] ),
        .shift_amt_i (                Ca90ImPerm ),
        .vector_o    ( item_memory_bases[i][j+1] )
      );

    end
  end

  always_comb begin
    for ( int i = 0; i < NumImSets; i++) begin
      for ( int j = 0; j < NumPerImBank; j++) begin
        item_memory[i*NumPerImBank+j] = item_memory_bases[i][j];
      end
    end
  end


  //---------------------------
  // Read output ports
  //---------------------------
  always_comb begin
    im_a_o = item_memory[im_sel_a_i];
    im_b_o = item_memory[im_sel_b_i];
  end

endmodule
