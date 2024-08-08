//---------------------------
// Copyright 2024 KU Leuven
// Ryan Antonio <ryan.antonio@esat.kuleuven.be>
//
// Module: Item Memory Top
// Description:
// This is the top-module of the item memory
// it does a project and fetch mechanism
// that coordinates directly with a data port
//---------------------------

module item_memory_top #(
  parameter int unsigned HVDimension   = 512,
  parameter int unsigned NumTotIm      = 1024,
  parameter int unsigned NumPerImBank  = 128,
  parameter int unsigned SeedWidth     = 32,
  parameter int unsigned HoldFifoDepth = 2,
  // Don't touch!
  parameter int unsigned ImAddrWidth   = $clog2(NumTotIm),
  parameter int unsigned NumImSets     = NumTotIm/NumPerImBank
)(
  // Clock and resets
  input  logic                                  clk_i,
  input  logic                                  rst_ni,
  // Configurations from CSR
  input  logic                            [1:0] port_a_cim_i,
  input  logic                                  port_b_cim_i,
  input  logic                [  SeedWidth-1:0] cim_seed_hv_i,
  input  logic [NumImSets-1:0][  SeedWidth-1:0] im_seed_hv_i,
  // Enable signal for system enable
  input  logic                                  clr_i,
  input  logic                                  enable_i,
  output logic                                  stall_o,
  // Inputs from the fetcher side
  input  logic                [ImAddrWidth-1:0] lowdim_a_data_i,
  input  logic                [HVDimension-1:0] highdim_a_data_i,
  input  logic                                  im_a_data_valid_i,
  output logic                                  im_a_data_ready_o,
  input  logic                [ImAddrWidth-1:0] lowdim_b_data_i,
  input  logic                [HVDimension-1:0] highdim_b_data_i,
  input  logic                                  im_b_data_valid_i,
  output logic                                  im_b_data_ready_o,
  // Outputs towards the encoder
  output logic                [HVDimension-1:0] im_a_o,
  input  logic                                  im_a_pop_i,
  output logic                [HVDimension-1:0] im_b_o,
  input  logic                                  im_b_pop_i
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
  logic [ImAddrWidth-1:0] im_a_addr, im_b_addr;

  logic fifo_full_a, fifo_full_b;
  logic fifo_empty_a, fifo_empty_b;

  logic fifo_push_a, fifo_push_b;
  logic fifo_pop_a, fifo_pop_b;

  logic [HVDimension-1:0] project_im_a, project_im_b;
  logic [HVDimension-1:0] im_a, im_b;

  //---------------------------
  // Combinational assignments
  //---------------------------
  assign im_a_data_ready_o = !fifo_full_a && enable_i;
  assign im_b_data_ready_o = !fifo_full_b && enable_i;

  assign fifo_push_a = im_a_data_valid_i && im_a_data_ready_o;
  assign fifo_push_b = im_b_data_valid_i && im_b_data_ready_o;

  assign fifo_pop_a  = im_a_pop_i && !fifo_empty_a;
  assign fifo_pop_b  = im_b_pop_i && !fifo_empty_b;

  // Stall occurs when a FIFO pops but it is empty
  assign stall_o = (im_a_pop_i && fifo_empty_a) || (im_b_pop_i && fifo_empty_b);

  //---------------------------
  // Combinational item memory
  //---------------------------
  item_memory #(
    .HVDimension   ( HVDimension     ),
    .NumTotIm      ( NumTotIm        ),
    .NumPerImBank  ( NumPerImBank    ),
    .SeedWidth     ( SeedWidth       )
  ) i_item_memory (
    .port_a_cim_i  ( port_a_cim_i[0] ),
    .cim_seed_hv_i ( cim_seed_hv_i   ),
    .im_seed_hv_i  ( im_seed_hv_i    ),
    .im_a_addr_i   ( lowdim_a_data_i ),
    .im_b_addr_i   ( lowdim_b_data_i ),
    .im_a_o        ( project_im_a    ),
    .im_b_o        ( project_im_b    )
  );

  //---------------------------
  // MUX-ing before getting into FIFOs
  //---------------------------
  logic [1:0][HVDimension-1:0] mux_ima_in;

  assign mux_ima_in[0] = project_im_a;
  assign mux_ima_in[1] = highdim_a_data_i;

  mux #(
    .DataWidth  ( HVDimension     ),
    .NumSel     ( 2               )
  ) i_mux_ima (
    .sel_i      ( port_a_cim_i[1] ),
    .signal_i   ( mux_ima_in      ),
    .signal_o   ( im_a            )
  );

  logic [1:0][HVDimension-1:0] mux_imb_in;

  assign mux_imb_in[0] = project_im_b;
  assign mux_imb_in[1] = highdim_b_data_i;

  mux #(
    .DataWidth  ( HVDimension  ),
    .NumSel     ( 2            )
  ) i_mux_imb (
    .sel_i      ( port_b_cim_i ),
    .signal_i   ( mux_imb_in   ),
    .signal_o   ( im_b         )
  );

  //---------------------------
  // FIFO for outputs
  //---------------------------
  fifo_buffer #(
    .FallThrough     ( 1'b1          ),
    .DataWidth       ( HVDimension   ),
    .FifoDepth       ( HoldFifoDepth )
  ) i_fifo_im_a (
    // Clocks and reset
    .clk_i           ( clk_i         ),
    .rst_ni          ( rst_ni        ),
    // Software synchronous clear
    .clr_i           ( clr_i         ),
    // Status flags
    .full_o          ( fifo_full_a   ),
    .empty_o         ( fifo_empty_a  ),
    // Note that this counter state is index 1
    .counter_state_o ( /*Unused*/    ),
    // Input push
    .data_i          ( im_a          ),
    .push_i          ( fifo_push_a   ),
    // Output pop
    .data_o          ( im_a_o        ),
    .pop_i           ( fifo_pop_a    )
  );

  fifo_buffer #(
    .FallThrough     ( 1'b1          ),
    .DataWidth       ( HVDimension   ),
    .FifoDepth       ( HoldFifoDepth )
  ) i_fifo_im_b (
    // Clocks and reset
    .clk_i           ( clk_i         ),
    .rst_ni          ( rst_ni        ),
    // Software synchronous clear
    .clr_i           ( clr_i         ),
    // Status flags
    .full_o          ( fifo_full_b   ),
    .empty_o         ( fifo_empty_b  ),
    // Note that this counter state is index 1
    .counter_state_o ( /*Unused*/    ),
    // Input push
    .data_i          ( im_b          ),
    .push_i          ( fifo_push_b   ),
    // Output pop
    .data_o          ( im_b_o        ),
    .pop_i           ( fifo_pop_b    )
  );

endmodule
