//---------------------------
// Copyright 2024 KU Leuven
// Ryan Antonio <ryan.antonio@esat.kuleuven.be>
//
// Module: Continuous Item Memory (CiM)
// Description:
// This is the CiM used to represent
// real values signals. It generates a
// square CiM which is at max half
// of the specified working dimension
//---------------------------

module cim #(
  parameter int unsigned HVDimension   = 512,
  parameter int unsigned SeedWidth     = 32,
  // Don't touch parameters
  parameter int unsigned NumCimLevels  = HVDimension/2,
  parameter int unsigned ImSelWidth    = $clog2(NumCimLevels)
)(
  // Inputs
  input  logic [  SeedWidth-1:0] seed_hv_i,
  input  logic [ ImSelWidth-1:0] cim_sel_i,
  // Outputs
  output logic [HVDimension-1:0] cim_o
);
  //---------------------------
  // Wires and logic
  //---------------------------
  logic [NumCimLevels-1:0][HVDimension-1:0] cim;
  logic                   [HVDimension-1:0] cim_base;

  // First generate the base
  ca90_hier_base #(
      .HVDimension ( HVDimension ),
      .SeedWidth   ( SeedWidth   )
  ) i_ca90_hier_base (
      .seed_hv_i   ( seed_hv_i   ),
      .base_hv_o   ( cim_base    )
  );

  //---------------------------
  // Fully-combinational flipping
  // Note that we flip every other
  // bit position after index 0
  //---------------------------
  genvar i;

  for (i = 0; i < NumCimLevels; i++) begin: gen_cim_levels
    if (i == 0) begin: gen_first_level
      // First copy the base
      assign cim[0] = cim_base;

    end else begin: gen_other_levels

      // Bit flips combinationally
      cim_bit_flip # (
        .HVDimension ( HVDimension ),
        .FlipBitPos  ( i*2-1       )
      ) i_cim_bit_flip (
        .hv_i        (cim[i-1]),
        .hv_o        (cim[  i])
      );
    end

  end

  //---------------------------
  // Read output port
  //---------------------------
  always_comb begin
    cim_o = cim[cim_sel_i];
  end

endmodule
