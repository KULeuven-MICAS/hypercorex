//---------------------------
// Copyright 2024 KU Leuven
// Ryan Antonio <ryan.antonio@esat.kuleuven.be>
//
// Module: CA90 Item Memory
// Description:
// This is the main item memory block
// It consists of both the CiM and CA90
// with control ports that are used to select
// the IM addresses and whether it gets
// from CiM or from the CA 90
//---------------------------

module item_memory #(
  parameter int unsigned HVDimension = 512,
  parameter int unsigned NumTotIm    = 1024,
  parameter int unsigned NumPerImBank= 128,
  parameter int unsigned ImAddrWidth = 32,
  parameter int unsigned SeedWidth   = 32,
  // Don't touch!
  parameter int unsigned NumImSets   = NumTotIm/NumPerImBank
)(
  input  logic                                  port_a_cim_i,
  input  logic                [  SeedWidth-1:0] cim_seed_hv_i,
  input  logic [NumImSets-1:0][  SeedWidth-1:0] im_seed_hv_i,
  input  logic                [ImAddrWidth-1:0] im_a_addr_i,
  input  logic                [ImAddrWidth-1:0] im_b_addr_i,
  output logic                [HVDimension-1:0] im_a_o,
  output logic                [HVDimension-1:0] im_b_o
);

  //---------------------------
  // Local parameters
  //---------------------------
  localparam int unsigned NumCimLevels = HVDimension/2;
  localparam int unsigned CimSelWidth  = $clog2(NumCimLevels);
  localparam int unsigned ImSelWidth   = $clog2(NumTotIm);

  //---------------------------
  // Wires
  //---------------------------
  logic [HVDimension-1:0] cim_a;
  logic [HVDimension-1:0] im_a;

  logic [1:0][HVDimension-1:0] mux_porta_out_in;

  logic [1:0][CimSelWidth-1:0] mux_cim_addr_in;
  logic      [CimSelWidth-1:0] mux_cim_addr_out;


  logic [1:0][ ImSelWidth-1:0] mux_im_addr_in;
  logic      [ ImSelWidth-1:0] mux_im_addr_out;

  //---------------------------
  // Input MUX for CiM
  //---------------------------
  assign mux_cim_addr_in = {
    im_a_addr_i[CimSelWidth-1:0],
    {CimSelWidth{1'b0}}
  };

  mux #(
    .DataWidth  ( CimSelWidth       ),
    .NumSel     ( 2                 )
  ) i_mux_cim_in (
    .sel_i      ( port_a_cim_i      ),
    .signal_i   ( mux_cim_addr_in   ),
    .signal_o   ( mux_cim_addr_out  )
  );

  //---------------------------
  // CiM Module
  //---------------------------
  cim #(
    .HVDimension ( HVDimension      ),
    .SeedWidth   ( SeedWidth        )
  ) i_cim (
    .seed_hv_i   ( cim_seed_hv_i    ),
    .cim_sel_i   ( mux_cim_addr_out ),
    .cim_o       ( cim_a            )
  );

  //---------------------------
  // Input MUX for iM
  //---------------------------
  assign mux_im_addr_in = {
    {ImSelWidth{1'b0}},
    im_a_addr_i[ImSelWidth-1:0]
  };

  mux #(
    .DataWidth  ( ImSelWidth      ),
    .NumSel     ( 2               )
  ) i_mux_im_in (
    .sel_i      ( port_a_cim_i    ),
    .signal_i   ( mux_im_addr_in  ),
    .signal_o   ( mux_im_addr_out )
  );

  //---------------------------
  // CA90 iM Module
  //---------------------------
  ca90_item_memory #(
    .HVDimension  ( HVDimension     ),
    .NumTotIm     ( NumTotIm        ),
    .NumPerImBank ( NumPerImBank    ),
    .SeedWidth    ( SeedWidth       )
  ) i_ca90_item_memory (
    .seed_hv_i    ( im_seed_hv_i    ),
    .im_sel_a_i   ( mux_im_addr_out ),
    .im_sel_b_i   ( im_b_addr_i     ),
    .im_a_o       ( im_a            ),
    .im_b_o       ( im_b_o          )
  );

  //---------------------------
  // Output MUX
  //---------------------------
  assign mux_porta_out_in = {
    cim_a,
    im_a
  };

  mux #(
    .DataWidth  ( HVDimension      ),
    .NumSel     ( 2                )
  ) i_mux_porta_out (
    .sel_i      ( port_a_cim_i     ),
    .signal_i   ( mux_porta_out_in ),
    .signal_o   ( im_a_o           )
  );

endmodule
