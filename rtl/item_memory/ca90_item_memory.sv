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
  parameter int unsigned HVDimension          = 512,
  parameter int unsigned NumTotIm             = 1024,
  parameter int unsigned NumPerImBank         = 128,
  parameter int unsigned SeedWidth            = 32,
  // Don't touch parameters
  parameter int unsigned Ca90ImPerm           = 7,
  parameter int unsigned CA90ImPermShiftWidth = $clog2(Ca90ImPerm),
  parameter int unsigned NumImSets            = NumTotIm/NumPerImBank,
  parameter int unsigned ImSelWidth           = $clog2(NumTotIm)
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
  logic [HVDimension-1:0] item_memory [NumTotIm];
  logic [HVDimension-1:0] item_memory_bases [NumImSets];
  //logic [HVDimension-1:0] item_memory_bases [NumImSets][NumPerImBank];

  // Generate for bases first
  // this is manually separated to avoid
  // unoptimized signal lines in Verilator
  for (i=0; i < NumImSets; i++) begin: gen_item_memory_base
    ca90_hier_base #(
      .HVDimension ( HVDimension          ),
      .SeedWidth   ( SeedWidth            )
    ) i_ca90_hier_base (
      .seed_hv_i   ( seed_hv_i[i]         ),
      .base_hv_o   ( item_memory_bases[i] )
    );
  end

  // Generate for the rest of the item memory
  for (i=0; i < NumImSets; i++) begin: gen_item_memory_set
    for( j=0 ; j < NumPerImBank; j++) begin: gen_item_memory_rows
      // Load the first component
      if(j == 0) begin: gen_first_base
        assign item_memory[i*NumPerImBank+j] = item_memory_bases[i];
      // Generate the rest iteratively
      end else begin: gen_other_ims
        ca90_unit #(
          .Dimension   ( HVDimension                          ),
          // Don't touch but fixed to reduce warnings
          .ShiftWidth  ( CA90ImPermShiftWidth                 )
        ) i_ca90_im_hv (
          .vector_i    ( item_memory[i*NumPerImBank+j-1]      ),
          .shift_amt_i ( Ca90ImPerm[CA90ImPermShiftWidth-1:0] ),
          .vector_o    ( item_memory[i*NumPerImBank+j]        )
        );
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
