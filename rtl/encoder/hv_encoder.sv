//---------------------------
// Copyright 2024 KU Leuven
// Ryan Antonio <ryan.antonio@esat.kuleuven.be>
//
// Module: Encoder
// Description:
// Main encoder module including glue logic
// for the registers, hypervector ALUs,
// and other useful units.
//---------------------------

module hv_encoder #(
  parameter int unsigned HVDimension    = 512,
  parameter int unsigned BundCountWidth = 8,
  parameter int unsigned BundMuxWidth   = 2,
  parameter int unsigned ALUMuxWidth    = 2,
  parameter int unsigned ALUMaxShiftAmt = 128,
  parameter int unsigned RegMuxWidth    = 2,
  parameter int unsigned QvMuxWidth     = 2,
  parameter int unsigned RegNum         = 4,
  // Don't touch!
  parameter int unsigned NumALUOps      = 4,
  parameter int unsigned ALUOpsWidth    = $clog2(NumALUOps     ),
  parameter int unsigned ShiftWidth     = $clog2(ALUMaxShiftAmt),
  parameter int unsigned RegAddrWidth   = $clog2(RegNum        )
)(
  // Clocks and reset
  input  logic                    clk_i,
  input  logic                    rst_ni,
  // Item memory inputs
  input  logic [ HVDimension-1:0] im_rd_a_i,
  input  logic [ HVDimension-1:0] im_rd_b_i,
  // Control ports for ALU
  input  logic [ ALUMuxWidth-1:0] alu_mux_a_i,
  input  logic [ ALUMuxWidth-1:0] alu_mux_b_i,
  input  logic [ ALUOpsWidth-1:0] alu_ops_i,
  input  logic [  ShiftWidth-1:0] alu_shift_amt_i,
  // Control ports for bundlers
  input  logic [BundMuxWidth-1:0] bund_mux_a_i,
  input  logic [BundMuxWidth-1:0] bund_mux_b_i,
  input  logic                    bund_valid_a_i,
  input  logic                    bund_valid_b_i,
  input  logic                    bund_clr_a_i,
  input  logic                    bund_clr_b_i,
  // Control ports for register ops
  input  logic [ RegMuxWidth-1:0] reg_mux_i,
  input  logic [RegAddrWidth-1:0] reg_rd_addr_a_i,
  input  logic [RegAddrWidth-1:0] reg_rd_addr_b_i,
  input  logic [RegAddrWidth-1:0] reg_wr_addr_i,
  input  logic                    reg_wr_en_i,
  // Control ports for query HV
  input  logic                    qhv_wen_i,
  input  logic                    qhv_clr_i,
  input  logic [  QvMuxWidth-1:0] qhv_mux_i,
  input  logic                    qhv_am_load_i,
  input  logic                    qhv_ready_i,
  output logic                    qhv_valid_o,
  output logic [ HVDimension-1:0] qhv_o,
  output logic                    qhv_stall_o
);

  //---------------------------
  // Wires
  //---------------------------
  logic [HVDimension-1:0] reg_wr_data;
  logic [HVDimension-1:0] reg_rd_data_a;
  logic [HVDimension-1:0] reg_rd_data_b;

  logic [HVDimension-1:0] alu_input_a;
  logic [HVDimension-1:0] alu_input_b;
  logic [HVDimension-1:0] alu_output;

  logic [HVDimension-1:0] bund_input_a;
  logic [HVDimension-1:0] bund_input_b;
  logic [HVDimension-1:0] bund_output_a;
  logic [HVDimension-1:0] bund_output_b;

  logic [HVDimension-1:0] qhv_input;
  logic [HVDimension-1:0] qhv_output;

  //---------------------------
  // HV register file MUX
  //---------------------------
  logic [3:0][HVDimension-1:0] reg_mux_in;

  assign reg_mux_in[0] = alu_output;
  assign reg_mux_in[1] = im_rd_a_i;
  assign reg_mux_in[2] = bund_output_a;
  assign reg_mux_in[3] = bund_output_b;

  mux #(
    .DataWidth  ( HVDimension ),
    .NumSel     ( 4           )
  ) i_reg_mux (
    .sel_i      ( reg_mux_i   ),
    .signal_i   ( reg_mux_in  ),
    .signal_o   ( reg_wr_data )
  );

  //---------------------------
  // HV register file
  //---------------------------
  reg_file_1w2r #(
    .DataWidth    ( HVDimension     ),
    .NumRegs      ( RegNum          )
  ) i_reg_file_1w2r (
    // Clocks and resets
    .clk_i        ( clk_i           ),
    .rst_ni       ( rst_ni          ),
    // Write port
    .clr_i        ( '0              ),
    .wr_addr_i    ( reg_wr_addr_i   ),
    .wr_data_i    ( reg_wr_data     ),
    .wr_en_i      ( reg_wr_en_i     ),
    // Read port A
    .rd_addr_a_i  ( reg_rd_addr_a_i ),
    .rd_data_a_o  ( reg_rd_data_a   ),
    // Read port B
    .rd_addr_b_i  ( reg_rd_addr_b_i ),
    .rd_data_b_o  ( reg_rd_data_b   )
  );

  //---------------------------
  // MUX-ing for ALU inputs
  //---------------------------
  logic [3:0][HVDimension-1:0] alu_mux_a_in;

  assign alu_mux_a_in[0] = im_rd_a_i;
  assign alu_mux_a_in[1] = reg_rd_data_a;
  assign alu_mux_a_in[2] = bund_output_a;
  assign alu_mux_a_in[3] = bund_output_b;

  mux #(
    .DataWidth  ( HVDimension  ),
    .NumSel     ( 4            )
  ) i_alu_mux_a (
    .sel_i      ( alu_mux_a_i  ),
    .signal_i   ( alu_mux_a_in ),
    .signal_o   ( alu_input_a  )
  );

  logic [3:0][HVDimension-1:0] alu_mux_b_in;

  assign alu_mux_b_in[0] = im_rd_b_i;
  assign alu_mux_b_in[1] = reg_rd_data_b;
  assign alu_mux_b_in[2] = bund_output_a;
  assign alu_mux_b_in[3] = bund_output_b;

  mux #(
    .DataWidth  ( HVDimension  ),
    .NumSel     ( 4            )
  ) i_alu_mux_b (
    .sel_i      ( alu_mux_b_i  ),
    .signal_i   ( alu_mux_b_in ),
    .signal_o   ( alu_input_b  )
  );

  //---------------------------
  // HV ALU unit
  //---------------------------
  hv_alu_pe #(
    .HVDimension  ( HVDimension     ),
    .NumOps       ( NumALUOps       ),
    .MaxShiftAmt  ( ALUMaxShiftAmt  )
  ) i_hv_alu_pe (
    // Inputs
    .A_i          ( alu_input_a     ),
    .B_i          ( alu_input_b     ),
    // Outputs
    .C_o          ( alu_output      ),
    // Control ports
    .op_i         ( alu_ops_i       ),
    .shift_amt_i  ( alu_shift_amt_i )
  );

  //---------------------------
  // MUX-ing for bundling units
  //---------------------------
  logic [3:0][HVDimension-1:0] bund_mux_a_in;

  assign bund_mux_a_in[0] = alu_output;
  assign bund_mux_a_in[1] = bund_output_b;
  assign bund_mux_a_in[2] = im_rd_a_i;
  assign bund_mux_a_in[3] = reg_rd_data_a;

  mux #(
    .DataWidth  ( HVDimension   ),
    .NumSel     ( 4             )
  ) i_bund_mux_a (
    .sel_i      ( bund_mux_a_i  ),
    .signal_i   ( bund_mux_a_in ),
    .signal_o   ( bund_input_a  )
  );

  logic [3:0][HVDimension-1:0] bund_mux_b_in;

  assign bund_mux_b_in[0] = alu_output;
  assign bund_mux_b_in[1] = bund_output_a;
  assign bund_mux_b_in[2] = im_rd_a_i;
  assign bund_mux_b_in[3] = reg_rd_data_a;

  mux #(
    .DataWidth  ( HVDimension   ),
    .NumSel     ( 4             )
  ) i_bund_mux_b (
    .sel_i      ( bund_mux_b_i  ),
    .signal_i   ( bund_mux_b_in ),
    .signal_o   ( bund_input_b  )
  );

  //---------------------------
  // Bundler unit A
  // One can use this as spatial unit
  //---------------------------
  bundler_set #(
    .HVDimension    ( HVDimension      ),
    .CounterWidth   ( BundCountWidth   )
  ) i_bundler_set_a (
    .clk_i          ( clk_i            ),
    .rst_ni         ( rst_ni           ),
    .hv_i           ( bund_input_a     ),
    .valid_i        ( bund_valid_a_i   ),
    .clr_i          ( bund_clr_a_i     ),
    .counter_o      (), //Unused for now
    .binarized_hv_o ( bund_output_a    )
  );

  //---------------------------
  // Bundler unit B
  // One can use this as temporal unit
  //---------------------------
  bundler_set #(
    .HVDimension    ( HVDimension      ),
    .CounterWidth   ( BundCountWidth   )
  ) i_bundler_set_b (
    .clk_i          ( clk_i            ),
    .rst_ni         ( rst_ni           ),
    .hv_i           ( bund_input_b     ),
    .valid_i        ( bund_valid_b_i   ),
    .clr_i          ( bund_clr_b_i     ),
    .counter_o      (), //Unused for now
    .binarized_hv_o ( bund_output_b    )
  );

  //---------------------------
  // Query HV MUX
  //---------------------------
  logic [3:0][HVDimension-1:0] qhv_mux_in;

  assign qhv_mux_in[0] = alu_output;
  assign qhv_mux_in[1] = reg_rd_data_a;
  assign qhv_mux_in[2] = bund_output_a;
  assign qhv_mux_in[3] = bund_output_b;

  mux #(
    .DataWidth  ( HVDimension ),
    .NumSel     ( 4           )
  ) i_qhv_mux (
    .sel_i      ( qhv_mux_i   ),
    .signal_i   ( qhv_mux_in  ),
    .signal_o   ( qhv_input   )
  );

  //---------------------------
  // Query HV register
  //---------------------------
  qhv #(
    .HVDimension   ( HVDimension   )
  ) i_qhv (
    // Clocks and reset
    .clk_i         ( clk_i         ),
    .rst_ni        ( rst_ni        ),
    // Control ports for query HV
    .qhv_i         ( qhv_input     ),
    .qhv_wen_i     ( qhv_wen_i     ),
    .qhv_clr_i     ( qhv_clr_i     ),
    .qhv_am_load_i ( qhv_am_load_i ),
    .qhv_o         ( qhv_o         ),
    .qhv_valid_o   ( qhv_valid_o   ),
    .qhv_ready_i   ( qhv_ready_i   ),
    .qhv_stall_o   ( qhv_stall_o   )
  );

endmodule
