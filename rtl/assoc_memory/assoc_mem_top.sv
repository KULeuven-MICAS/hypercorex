//---------------------------
// Copyright 2024 KU Leuven
// Ryan Antonio <ryan.antonio@esat.kuleuven.be>
//
// Module: assoc_mem_top
// Description:
//   Top-level wrapper for the associative memory subsystem.
//
// Parameters:
//    HVDimension : dimensionality of the hypervectors (default 512)
//    NumClass    : number of class hypervectors held in the latch memory
//                  (sets latch_memory NumWords; must satisfy 2^DataWidth >= NumClass)
//    DataWidth   : width of the prediction output and the read address bus (default 8)
// IO ports:
//    clk_i                  : clock input
//    rst_ni                 : active-low reset input
//    -- Write side (latch_memory) --
//    w_valid_i              : write valid
//    w_ready_o              : write ready
//    w_en_i                 : write enable
//    w_addr_i               : write address
//    w_data_i               : write data (one class hypervector)
//    -- External read port --
//    external_read_sel_i    : 1 = external port owns the read channel; 0 = bin_sim_search
//    ext_r_req_valid_i      : external read request valid
//    ext_r_req_ready_o      : external read request ready (gated off when sel=0)
//    ext_r_addr_i           : external read address
//    ext_r_resp_valid_o     : external read response valid (gated off when sel=0)
//    ext_r_resp_ready_i     : external read response ready
//    ext_r_resp_data_o      : external read response data
//    -- Search control (bin_sim_search) --
//    query_hv_i             : query hypervector input
//    am_start_i             : start similarity search
//    am_busy_o              : search in progress
//    am_stall_o             : stall upstream (busy and start asserted together)
//    am_num_class_i         : number of classes to compare (from CSR)
//    am_predict_valid_o     : prediction valid (CSR-facing)
//    am_predict_valid_clr_i : clear prediction valid
//    predict_o              : predicted class index
//    predict_valid_o        : prediction valid (stream-facing)
//    predict_ready_i        : downstream ready for prediction
//---------------------------

module assoc_mem_top #(
  parameter int unsigned HVDimension = 512,
  parameter int unsigned NumClass    = 32,
  parameter int unsigned DataWidth   = 8,
  // Don't touch
  parameter int unsigned AddrWidth   = $clog2(NumClass)
)(
  // Clocks and reset
  input  logic                   clk_i,
  input  logic                   rst_ni,
  // Write side (latch_memory)
  input  logic                   w_valid_i,
  output logic                   w_ready_o,
  input  logic                   w_en_i,
  input  logic [AddrWidth-1:0]   w_addr_i,
  input  logic [HVDimension-1:0] w_data_i,
  // External read port
  input  logic                   external_read_sel_i,
  input  logic                   ext_r_req_valid_i,
  output logic                   ext_r_req_ready_o,
  input  logic [AddrWidth-1:0]   ext_r_addr_i,
  output logic                   ext_r_resp_valid_o,
  input  logic                   ext_r_resp_ready_i,
  output logic [HVDimension-1:0] ext_r_resp_data_o,
  // Search control (bin_sim_search)
  input  logic [HVDimension-1:0] query_hv_i,
  input  logic                   am_start_i,
  output logic                   am_busy_o,
  output logic                   am_stall_o,
  input  logic [  DataWidth-1:0] am_num_class_i,
  output logic                   am_predict_valid_o,
  input  logic                   am_predict_valid_clr_i,
  output logic [  DataWidth-1:0] predict_o,
  output logic                   predict_valid_o,
  input  logic                   predict_ready_i
);

  //---------------------------
  // Wires: bin_sim_search outputs
  // (drive into the MUX)
  //---------------------------
  logic                   class_hv_req_valid;
  logic [  AddrWidth-1:0] class_hv_addr;
  logic                   class_hv_resp_ready;

  //---------------------------
  // Wires: latch_memory outputs
  // (raw; distributed by MUX)
  //---------------------------
  logic                   lm_r_req_ready;
  logic                   lm_r_resp_valid;
  logic [HVDimension-1:0] lm_r_resp_data;

  //---------------------------
  // Wires: MUX outputs to latch_memory
  //---------------------------
  logic                   lm_r_req_valid;
  logic [  AddrWidth-1:0] lm_r_addr;
  logic                   lm_r_resp_ready;

  //---------------------------
  // Wires: MUX feedback to bin_sim_search
  //---------------------------
  logic class_hv_req_ready;
  logic class_hv_resp_valid;

  //---------------------------
  // Read-channel MUX
  // sel=0 : bin_sim_search owns the read channel (inference)
  // sel=1 : external port owns the read channel
  //---------------------------

  // Requests toward latch_memory
  assign lm_r_req_valid  = external_read_sel_i ? ext_r_req_valid_i  : class_hv_req_valid;
  assign lm_r_addr       = external_read_sel_i ? ext_r_addr_i       : class_hv_addr;
  assign lm_r_resp_ready = external_read_sel_i ? ext_r_resp_ready_i : class_hv_resp_ready;

  // Ready/valid feedback to bin_sim_search (gated off when external is selected)
  assign class_hv_req_ready  = external_read_sel_i ? 1'b0            : lm_r_req_ready;
  assign class_hv_resp_valid = external_read_sel_i ? 1'b0            : lm_r_resp_valid;

  // Ready/valid feedback to external port (gated off when internal is selected)
  assign ext_r_req_ready_o  = external_read_sel_i ? lm_r_req_ready  : 1'b0;
  assign ext_r_resp_valid_o = external_read_sel_i ? lm_r_resp_valid : 1'b0;

  // Response data is always routed to both consumers;
  // qualification is handled by the valid gating above
  assign ext_r_resp_data_o = lm_r_resp_data;

  //---------------------------
  // latch_memory instance
  //---------------------------
  latch_memory #(
    .NumWords  ( NumClass    ),
    .DataWidth ( HVDimension )
  ) i_latch_memory (
    .clk_i          ( clk_i           ),
    .rst_ni         ( rst_ni          ),
    // Write side
    .w_valid_i      ( w_valid_i       ),
    .w_ready_o      ( w_ready_o       ),
    .w_en_i         ( w_en_i          ),
    .w_addr_i       ( w_addr_i        ),
    .w_data_i       ( w_data_i        ),
    // Read request
    .r_req_valid_i  ( lm_r_req_valid  ),
    .r_req_ready_o  ( lm_r_req_ready  ),
    .r_addr_i       ( lm_r_addr       ),
    // Read response
    .r_resp_valid_o ( lm_r_resp_valid ),
    .r_resp_ready_i ( lm_r_resp_ready ),
    .r_resp_data_o  ( lm_r_resp_data  )
  );

  //---------------------------
  // bin_sim_search instance
  //---------------------------
  bin_sim_search #(
    .HVDimension ( HVDimension ),
    .DataWidth   ( DataWidth   )
  ) i_bin_sim_search (
    .clk_i                  ( clk_i                  ),
    .rst_ni                 ( rst_ni                 ),
    // Encode side
    .query_hv_i             ( query_hv_i             ),
    .am_start_i             ( am_start_i             ),
    .am_busy_o              ( am_busy_o              ),
    .am_stall_o             ( am_stall_o             ),
    // AM response (from MUX)
    .class_hv_i             ( lm_r_resp_data         ),
    .class_hv_valid_i       ( class_hv_resp_valid    ),
    .class_hv_read_o        ( class_hv_resp_ready    ),
    // AM request (to MUX)
    .class_hv_addr_o        ( class_hv_addr          ),
    .class_hv_req_valid_o   ( class_hv_req_valid     ),
    .class_hv_req_ready_i   ( class_hv_req_ready     ),
    // CSR side
    .am_num_class_i         ( am_num_class_i         ),
    .am_predict_valid_o     ( am_predict_valid_o     ),
    .am_predict_valid_clr_i ( am_predict_valid_clr_i ),
    // Prediction output
    .predict_o              ( predict_o              ),
    .predict_valid_o        ( predict_valid_o        ),
    .predict_ready_i        ( predict_ready_i        )
  );

endmodule
