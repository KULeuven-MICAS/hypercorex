//---------------------------
// Copyright 2024 KU Leuven
// Ryan Antonio <ryan.antonio@esat.kuleuven.be>
//
// Module: Hypercorex Top Module
// Description:
// This is the top module of the hypercorex
// programmable HDC accelerator
//
// It consists of all the sub-blocks and you
// will only see module instantiation
// and connections in this module
//---------------------------

module hypercorex_top # (
  //---------------------------
  // General Parameters
  //---------------------------
  parameter int unsigned HVDimension      = 512,
    //---------------------------
  // CSR Parameters
  //---------------------------
  parameter int unsigned CsrDataWidth     = 32,
  parameter int unsigned CsrAddrWidth     = 32,
  //---------------------------
  // Item Memory Parameters
  //---------------------------
  parameter int unsigned NumTotIm         = 1024,
  parameter int unsigned NumPerImBank     = 128,
  parameter int unsigned ImAddrWidth      = $clog2(NumTotIm),
  parameter int unsigned SeedWidth        = CsrDataWidth,
  parameter int unsigned HoldFifoDepth    = 2,
  //---------------------------
  // Instruction Memory Parameters
  //---------------------------
  parameter int unsigned InstMemDepth     = 128,
  //---------------------------
  // HDC Encoder Parameters
  //---------------------------
  parameter int unsigned BundCountWidth   = 8,
  parameter int unsigned BundMuxWidth     = 2,
  parameter int unsigned ALUMuxWidth      = 2,
  parameter int unsigned ALUMaxShiftAmt   = 128,
  parameter int unsigned RegMuxWidth      = 2,
  parameter int unsigned QvMuxWidth       = 2,
  parameter int unsigned RegNum           = 4,
  //---------------------------
  // Don't touch!
  //---------------------------
  parameter int unsigned NumALUOps        = 4,
  parameter int unsigned ALUOpsWidth      = $clog2(NumALUOps     ),
  parameter int unsigned ShiftWidth       = $clog2(ALUMaxShiftAmt),
  parameter int unsigned RegAddrWidth     = $clog2(RegNum        ),
  parameter int unsigned NumImSets        = NumTotIm/NumPerImBank,
  parameter int unsigned InstMemAddrWidth = $clog2(InstMemDepth  )
)(
  //---------------------------
  // Clocks and reset
  //---------------------------
  input  logic                    clk_i,
  input  logic                    rst_ni,
  //---------------------------
  // CSR RW control signals
  //---------------------------
  // Request
  input  logic [CsrDataWidth-1:0] csr_req_data_i,
  input  logic [CsrAddrWidth-1:0] csr_req_addr_i,
  input  logic                    csr_req_write_i,
  input  logic                    csr_req_valid_i,
  output logic                    csr_req_ready_o,
  // Response
  output logic [CsrDataWidth-1:0] csr_rsp_data_o,
  input  logic                    csr_rsp_ready_i,
  output logic                    csr_rsp_valid_o,
  //---------------------------
  // IM ports
  //---------------------------
  input  logic [ ImAddrWidth-1:0] lowdim_a_data_i,
  input  logic                    lowdim_a_valid_i,
  output logic                    lowdim_a_ready_o,
  input  logic [ HVDimension-1:0] highdim_a_data_i,
  input  logic                    highdim_a_valid_i,
  output logic                    highdim_a_ready_o,
  input  logic [ ImAddrWidth-1:0] lowdim_b_data_i,
  input  logic                    lowdim_b_valid_i,
  output logic                    lowdim_b_ready_o,
  input  logic [ HVDimension-1:0] highdim_b_data_i,
  input  logic                    highdim_b_valid_i,
  output logic                    highdim_b_ready_o,
  //---------------------------
  // QHV ports
  //---------------------------
  input  logic                    qhv_ready_i,
  output logic                    qhv_valid_o,
  output logic [ HVDimension-1:0] qhv_o,
  //---------------------------
  // AM ports
  //---------------------------
  input  logic [ HVDimension-1:0] class_hv_i,
  input  logic                    class_hv_valid_i,
  output logic                    class_hv_ready_o,
  //---------------------------
  // Low-dim prediction
  //---------------------------
  output logic [CsrDataWidth-1:0] predict_o,
  output logic                    predict_valid_o,
  input  logic                    predict_ready_i
);

  //---------------------------
  // Locally Configured Seeds
  //---------------------------
  logic      [SeedWidth-1:0] CiMBaseSeed;
  logic [7:0][SeedWidth-1:0] OrthoIMSeeds;

  assign CiMBaseSeed     = 32'd621635317;
  assign OrthoIMSeeds[0] = 32'd1103779247;
  assign OrthoIMSeeds[1] = 32'd2391206478;
  assign OrthoIMSeeds[2] = 32'd3074675908;
  assign OrthoIMSeeds[3] = 32'd2850820469;
  assign OrthoIMSeeds[4] = 32'd811160829;
  assign OrthoIMSeeds[5] = 32'd4032445525;
  assign OrthoIMSeeds[6] = 32'd2525737372;
  assign OrthoIMSeeds[7] = 32'd2535149661;

  //---------------------------
  // CSR Control Signals
  //---------------------------
  // Core settings
  logic                                          start;
  logic                                          seq_test_mode;
  logic                  [1:0]                   port_a_cim;
  logic                                          port_b_cim;
  logic                                          clr;
  // AM settings
  logic [    CsrDataWidth-1:0]                   am_num_pred;
  logic                                          am_pred_valid;
  logic                                          am_pred_valid_clr;
  // Instruction control settings
  logic                                          inst_ctrl_write_mode;
  logic                                          inst_ctrl_dbg;
  logic                                          inst_ctrl_clr;
  logic [InstMemAddrWidth-1:0]                   inst_wr_addr;
  logic                                          inst_wr_addr_en;
  logic [    CsrDataWidth-1:0]                   inst_wr_data;
  logic                                          inst_wr_data_en;
  logic [InstMemAddrWidth-1:0]                   inst_rddbg_addr;
  logic [InstMemAddrWidth-1:0]                   inst_pc;
  logic [    CsrDataWidth-1:0]                   inst_at_addr;
  // Instruction loop control
  logic                  [1:0]                   inst_loop_mode;
  logic [InstMemAddrWidth-1:0]                   loop_jump_addr1;
  logic [InstMemAddrWidth-1:0]                   loop_jump_addr2;
  logic [InstMemAddrWidth-1:0]                   loop_jump_addr3;
  logic [InstMemAddrWidth-1:0]                   loop_end_addr1;
  logic [InstMemAddrWidth-1:0]                   loop_end_addr2;
  logic [InstMemAddrWidth-1:0]                   loop_end_addr3;
  logic [InstMemAddrWidth-1:0]                   loop_count_addr1;
  logic [InstMemAddrWidth-1:0]                   loop_count_addr2;
  logic [InstMemAddrWidth-1:0]                   loop_count_addr3;

  //---------------------------
  // Item Memory <-> Encoder Signals
  //---------------------------
  logic [HVDimension-1:0] im_a;
  logic [HVDimension-1:0] im_b;

  //---------------------------
  // Instruction <-> Encoder Signals
  //---------------------------
  // Control ports for IM
  logic                    im_a_pop;
  logic                    im_b_pop;
  // Control ports for ALU
  logic [ ALUMuxWidth-1:0] alu_mux_a;
  logic [ ALUMuxWidth-1:0] alu_mux_b;
  logic [ ALUOpsWidth-1:0] alu_ops;
  logic [  ShiftWidth-1:0] alu_shift_amt;
  // Control ports for bundlers
  logic [BundMuxWidth-1:0] bund_mux_a;
  logic [BundMuxWidth-1:0] bund_mux_b;
  logic                    bund_valid_a;
  logic                    bund_valid_b;
  logic                    bund_clr_a;
  logic                    bund_clr_b;
  // Control ports for register ops
  logic [ RegMuxWidth-1:0] reg_mux;
  logic [RegAddrWidth-1:0] reg_rd_addr_a;
  logic [RegAddrWidth-1:0] reg_rd_addr_b;
  logic [RegAddrWidth-1:0] reg_wr_addr;
  logic                    reg_wr_en;
  // Control ports for query HV
  logic                    qhv_clr;
  logic                    qhv_wen;
  logic [  QvMuxWidth-1:0] qhv_mux;
  // Control port for the AM
  logic                    am_search;
  logic                    am_load;

  //---------------------------
  // Stall Signal
  //---------------------------
  logic stall;
  logic im_stall;
  logic am_stall;
  logic qhv_stall;

  assign stall = im_stall || qhv_stall || am_stall;

  //---------------------------
  // Enable Signal
  //---------------------------
  logic enable;

  //---------------------------
  // QHV Signals
  //---------------------------
  logic [HVDimension-1:0] qhv;

  assign qhv_o = qhv;

  //---------------------------
  // Busy Signal
  //---------------------------
  logic busy;
  logic am_busy;
  logic encoder_busy;

  assign encoder_busy = enable;
  assign busy = encoder_busy || am_busy;

  //---------------------------
  // Valid-ready Control
  //---------------------------
  logic im_a_data_valid;
  logic im_b_data_valid;

  logic im_a_data_ready;
  logic im_b_data_ready;

  assign im_a_data_valid   = port_a_cim[1] ? highdim_a_valid_i : lowdim_a_valid_i;
  assign im_b_data_valid   = port_b_cim    ? highdim_b_valid_i : lowdim_b_valid_i;

  assign lowdim_a_ready_o  = port_a_cim[1] ?  1'b0 : im_a_data_ready;
  assign highdim_a_ready_o = port_a_cim[1] ? im_a_data_ready : 1'b0;

  assign lowdim_b_ready_o  = port_b_cim    ?  1'b0 : im_b_data_ready;
  assign highdim_b_ready_o = port_b_cim    ? im_b_data_ready : 1'b0;

  //---------------------------
  // CSR registers and control
  //---------------------------
  csr #(
    .NumTotIm                   ( NumTotIm              ),
    .NumPerImBank               ( NumPerImBank          ),
    .CsrDataWidth               ( CsrDataWidth          ),
    .CsrAddrWidth               ( CsrAddrWidth          ),
    .InstMemDepth               ( InstMemDepth          )
  ) i_csr (
    //---------------------------
    // Clocks and reset
    //---------------------------
    .clk_i                      ( clk_i                 ),
    .rst_ni                     ( rst_ni                ),
    //---------------------------
    // CSR RW control signals
    //---------------------------
    // Request
    .csr_req_data_i             ( csr_req_data_i        ),
    .csr_req_addr_i             ( csr_req_addr_i        ),
    .csr_req_write_i            ( csr_req_write_i       ),
    .csr_req_valid_i            ( csr_req_valid_i       ),
    .csr_req_ready_o            ( csr_req_ready_o       ),
    // Response
    .csr_rsp_data_o             ( csr_rsp_data_o        ),
    .csr_rsp_ready_i            ( csr_rsp_ready_i       ),
    .csr_rsp_valid_o            ( csr_rsp_valid_o       ),
    //---------------------------
    // Output control signals
    //---------------------------
    // Core settings
    .csr_start_o                ( start                 ),
    .csr_busy_i                 ( busy                  ),
    .csr_seq_test_mode_o        ( seq_test_mode         ),
    .csr_port_a_cim_o           ( port_a_cim            ),
    .csr_port_b_cim_o           ( port_b_cim            ),
    .csr_clr_o                  ( clr                   ),
    // AM settings
    .csr_am_num_pred_o          ( am_num_pred           ),
    .csr_am_pred_i              ( predict_o             ),
    .csr_am_pred_valid_i        ( am_pred_valid         ),
    .csr_am_pred_valid_clr_o    ( am_pred_valid_clr     ),
    // Instruction control settings
    .csr_inst_ctrl_write_mode_o ( inst_ctrl_write_mode  ),
    .csr_inst_ctrl_dbg_o        ( inst_ctrl_dbg         ),
    .csr_inst_ctrl_clr_o        ( inst_ctrl_clr         ),
    .csr_inst_wr_addr_o         ( inst_wr_addr          ),
    .csr_inst_wr_addr_en_o      ( inst_wr_addr_en       ),
    .csr_inst_wr_data_o         ( inst_wr_data          ),
    .csr_inst_wr_data_en_o      ( inst_wr_data_en       ),
    .csr_inst_rddbg_addr_o      ( inst_rddbg_addr       ),
    .csr_inst_pc_i              ( inst_pc               ),
    .csr_inst_at_addr_i         ( inst_at_addr          ),
    // Instruction loop control
    .csr_inst_loop_mode_o       ( inst_loop_mode        ),
    .csr_loop_jump_addr1_o      ( loop_jump_addr1       ),
    .csr_loop_jump_addr2_o      ( loop_jump_addr2       ),
    .csr_loop_jump_addr3_o      ( loop_jump_addr3       ),
    .csr_loop_end_addr1_o       ( loop_end_addr1        ),
    .csr_loop_end_addr2_o       ( loop_end_addr2        ),
    .csr_loop_end_addr3_o       ( loop_end_addr3        ),
    .csr_loop_count_addr1_o     ( loop_count_addr1      ),
    .csr_loop_count_addr2_o     ( loop_count_addr2      ),
    .csr_loop_count_addr3_o     ( loop_count_addr3      )
  );


  //---------------------------
  // Instruction Control
  //---------------------------
  inst_control # (
    .RegAddrWidth               ( CsrDataWidth          ),
    .InstMemDepth               ( InstMemDepth          )
  ) i_inst_control (
    //---------------------------
    // Clocks and reset
    //---------------------------
    .clk_i                      ( clk_i                ),
    .rst_ni                     ( rst_ni               ),
    //---------------------------
    // Control signals
    //---------------------------
    .clr_i                      ( clr                  ),
    .start_i                    ( start                ),
    .stall_i                    ( stall                ),
    .enable_o                   ( enable               ),
    //---------------------------
    // Instruction update signals
    //---------------------------
    .inst_pc_reset_i            ( inst_ctrl_clr || clr ),
    .inst_wr_mode_i             ( inst_ctrl_write_mode ),
    .inst_wr_addr_i             ( inst_wr_addr         ),
    .inst_wr_addr_en_i          ( inst_wr_addr_en      ),
    .inst_wr_data_i             ( inst_wr_data         ),
    .inst_wr_data_en_i          ( inst_wr_data_en      ),
    .inst_pc_o                  ( inst_pc              ),
    .inst_rd_o                  ( inst_at_addr         ),
    //---------------------------
    // CSR control for loop control
    //---------------------------
    .inst_loop_mode_i           ( inst_loop_mode       ),
    .inst_loop_jump_addr1_i     ( loop_jump_addr1      ),
    .inst_loop_jump_addr2_i     ( loop_jump_addr2      ),
    .inst_loop_jump_addr3_i     ( loop_jump_addr3      ),
    .inst_loop_end_addr1_i      ( loop_end_addr1       ),
    .inst_loop_end_addr2_i      ( loop_end_addr2       ),
    .inst_loop_end_addr3_i      ( loop_end_addr3       ),
    .inst_loop_count_addr1_i    ( loop_count_addr1     ),
    .inst_loop_count_addr2_i    ( loop_count_addr2     ),
    .inst_loop_count_addr3_i    ( loop_count_addr3     ),
    //---------------------------
    // Debug control signals
    //---------------------------
    .dbg_en_i                   ( inst_ctrl_dbg        ),
    .dbg_addr_i                 ( inst_rddbg_addr      )
  );

  //---------------------------
  // Instruction Decoder
  //---------------------------
  inst_decode #(
    .InstWidth                  ( CsrDataWidth         ),
    .ALUMuxWidth                ( ALUMuxWidth          ),
    .ALUMaxShiftAmt             ( ALUMaxShiftAmt       ),
    .BundMuxWidth               ( BundMuxWidth         ),
    .RegMuxWidth                ( RegMuxWidth          ),
    .QvMuxWidth                 ( QvMuxWidth           ),
    .RegNum                     ( RegNum               )
  ) i_inst_decode (
    // Input instruction
    .inst_code_i                ( inst_at_addr         ),
    .enable_i                   ( enable               ),
    // Control ports for IM
    .im_a_pop_o                 ( im_a_pop             ),
    .im_b_pop_o                 ( im_b_pop             ),
    // Control ports for ALU
    .alu_mux_a_o                ( alu_mux_a            ),
    .alu_mux_b_o                ( alu_mux_b            ),
    .alu_ops_o                  ( alu_ops              ),
    .alu_shift_amt_o            ( alu_shift_amt        ),
    // Control ports for bundlers
    .bund_mux_a_o               ( bund_mux_a           ),
    .bund_mux_b_o               ( bund_mux_b           ),
    .bund_valid_a_o             ( bund_valid_a         ),
    .bund_valid_b_o             ( bund_valid_b         ),
    .bund_clr_a_o               ( bund_clr_a           ),
    .bund_clr_b_o               ( bund_clr_b           ),
    // Control ports for register ops
    .reg_mux_o                  ( reg_mux              ),
    .reg_rd_addr_a_o            ( reg_rd_addr_a        ),
    .reg_rd_addr_b_o            ( reg_rd_addr_b        ),
    .reg_wr_addr_o              ( reg_wr_addr          ),
    .reg_wr_en_o                ( reg_wr_en            ),
    // Control ports for query HV
    .qhv_clr_o                  ( qhv_clr              ),
    .qhv_wen_o                  ( qhv_wen              ),
    .qhv_mux_o                  ( qhv_mux              ),
    // Control port for the AM
    .am_search_o                ( am_search            ),
    .am_load_o                  ( am_load              )
  );

  //---------------------------
  // Item Memory Top
  //---------------------------
  item_memory_top #(
    .HVDimension                ( HVDimension          ),
    .NumTotIm                   ( NumTotIm             ),
    .NumPerImBank               ( NumPerImBank         ),
    .SeedWidth                  ( SeedWidth            ),
    .HoldFifoDepth              ( HoldFifoDepth        )
  ) i_item_memory_top (
    //---------------------------
    // Clock and resets
    //---------------------------
    .clk_i                      ( clk_i                ),
    .rst_ni                     ( rst_ni               ),
    //---------------------------
    // Configurations from CSR
    //---------------------------
    .port_a_cim_i               ( port_a_cim           ),
    .port_b_cim_i               ( port_b_cim           ),
    .cim_seed_hv_i              ( CiMBaseSeed          ),
    .im_seed_hv_i               ( OrthoIMSeeds[NumImSets-1:0] ),
    .clr_i                      ( clr                  ),
    .enable_i                   ( enable               ),
    .stall_o                    ( im_stall             ),
    //---------------------------
    // Inputs from the fetcher side
    //---------------------------
    .lowdim_a_data_i            ( lowdim_a_data_i      ),
    .highdim_a_data_i           ( highdim_a_data_i     ),
    .im_a_data_valid_i          ( im_a_data_valid      ),
    .im_a_data_ready_o          ( im_a_data_ready      ),
    .lowdim_b_data_i            ( lowdim_b_data_i      ),
    .highdim_b_data_i           ( highdim_b_data_i     ),
    .im_b_data_valid_i          ( im_b_data_valid      ),
    .im_b_data_ready_o          ( im_b_data_ready      ),
    //---------------------------
    // Outputs towards the encoder
    //---------------------------
    .im_a_o                     ( im_a                 ),
    .im_a_pop_i                 ( im_a_pop             ),
    .im_b_o                     ( im_b                 ),
    .im_b_pop_i                 ( im_b_pop             )
  );

  //---------------------------
  // HDC Encoder
  //---------------------------
  hv_encoder #(
    .HVDimension                ( HVDimension          ),
    .BundCountWidth             ( BundCountWidth       ),
    .BundMuxWidth               ( BundMuxWidth         ),
    .ALUMuxWidth                ( ALUMuxWidth          ),
    .ALUMaxShiftAmt             ( ALUMaxShiftAmt       ),
    .RegMuxWidth                ( RegMuxWidth          ),
    .QvMuxWidth                 ( QvMuxWidth           ),
    .RegNum                     ( RegNum               )
  ) i_hv_encoder (
    //---------------------------
    // Clocks and reset
    //---------------------------
    .clk_i                      ( clk_i                ),
    .rst_ni                     ( rst_ni               ),
    //---------------------------
    // Item memory inputs
    //---------------------------
    .im_rd_a_i                  ( im_a                 ),
    .im_rd_b_i                  ( im_b                 ),
    // Control ports for ALU
    .alu_mux_a_i                ( alu_mux_a            ),
    .alu_mux_b_i                ( alu_mux_b            ),
    .alu_ops_i                  ( alu_ops              ),
    .alu_shift_amt_i            ( alu_shift_amt        ),
    // Control ports for bundlers
    .bund_mux_a_i               ( bund_mux_a           ),
    .bund_mux_b_i               ( bund_mux_b           ),
    .bund_valid_a_i             ( bund_valid_a         ),
    .bund_valid_b_i             ( bund_valid_b         ),
    .bund_clr_a_i               ( bund_clr_a           ),
    .bund_clr_b_i               ( bund_clr_b           ),
    // Control ports for register ops
    .reg_mux_i                  ( reg_mux              ),
    .reg_rd_addr_a_i            ( reg_rd_addr_a        ),
    .reg_rd_addr_b_i            ( reg_rd_addr_b        ),
    .reg_wr_addr_i              ( reg_wr_addr          ),
    .reg_wr_en_i                ( reg_wr_en            ),
    // Control ports for query HV
    .qhv_wen_i                  ( qhv_wen              ),
    .qhv_clr_i                  ( qhv_clr              ),
    .qhv_mux_i                  ( qhv_mux              ),
    .qhv_am_load_i              ( am_load              ),
    .qhv_ready_i                ( qhv_ready_i          ),
    .qhv_valid_o                ( qhv_valid_o          ),
    .qhv_o                      ( qhv                  ),
    .qhv_stall_o                ( qhv_stall            )
  );

  //---------------------------
  // AM Module
  //---------------------------
  assoc_mem #(
    .HVDimension                ( HVDimension          ),
    .DataWidth                  ( CsrDataWidth         )
  ) i_assoc_mem (
    // Clocks and reset
    .clk_i                      ( clk_i                ),
    .rst_ni                     ( rst_ni               ),
    // Encode side control
    .query_hv_i                 ( qhv                  ),
    .am_start_i                 ( am_search            ),
    .am_busy_o                  ( am_busy              ),
    .am_stall_o                 ( am_stall             ),
    // AM side control
    .class_hv_i                 ( class_hv_i           ),
    .class_hv_valid_i           ( class_hv_valid_i     ),
    .class_hv_ready_o           ( class_hv_ready_o     ),
    // CSR output side
    .am_num_class_i             ( am_num_pred          ),
    .am_predict_valid_o         ( am_pred_valid        ),
    .am_predict_valid_clr_i     ( am_pred_valid_clr    ),
    // Low-dim prediction
    .predict_o                  ( predict_o            ),
    .predict_valid_o            ( predict_valid_o      ),
    .predict_ready_i            ( predict_ready_i      )
  );

endmodule
