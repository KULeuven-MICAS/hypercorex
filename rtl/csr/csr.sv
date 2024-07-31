//---------------------------
// Copyright 2024 KU Leuven
// Ryan Antonio <ryan.antonio@esat.kuleuven.be>
//
// Module: CSR
// Description:
// This module handles the very custom CSR
// management for read and write operations
//
// Some general convention rules
// - RW are read and writable
// - RO are read-only and hence writes have no effect
// - WO are write-only and return 0 only
//---------------------------

module csr import csr_addr_pkg::*; #(
  parameter int unsigned NumTotIm         = 1024,
  parameter int unsigned NumPerImBank     = 128,
  parameter int unsigned CsrDataWidth     = 32,
  parameter int unsigned CsrAddrWidth     = 32,
  parameter int unsigned InstMemDepth     = 32,
  // Don't touch!
  parameter int unsigned NumImSets        = NumTotIm/NumPerImBank,
  // Total number of registers + N number if IM seeds
  parameter int unsigned NumRegs          = (14+NumImSets),
  parameter int unsigned InstMemAddrWidth = $clog2(InstMemDepth),
  parameter int unsigned RegBitAddrWidth  = $clog2(CsrAddrWidth)
)(
  //---------------------------
  // Clocks and reset
  //---------------------------
  input  logic                                      clk_i,
  input  logic                                      rst_ni,
  //---------------------------
  // CSR RW control signals
  //---------------------------
  // Request
  input  logic [    CsrDataWidth-1:0]               csr_req_data_i,
  input  logic [    CsrAddrWidth-1:0]               csr_req_addr_i,
  input  logic                                      csr_req_write_i,
  input  logic                                      csr_req_valid_i,
  output logic                                      csr_req_ready_o,
  // Response
  output logic [    CsrDataWidth-1:0]               csr_rsp_data_o,
  input  logic                                      csr_rsp_ready_i,
  output logic                                      csr_rsp_valid_o,
  //---------------------------
  // Output control signals
  //---------------------------
  // Core settings
  output logic                                      csr_start_o,
  input  logic                                      csr_busy_i,
  output logic                                      csr_seq_test_mode_o,
  output logic                  [1:0]               csr_port_a_cim_o,
  output logic                                      csr_port_b_cim_o,
  output logic                                      csr_clr_o,
  // AM settings
  output logic [    CsrDataWidth-1:0]               csr_am_num_pred_o,
  input  logic [    CsrDataWidth-1:0]               csr_am_pred_i,
  // Instruction control settings
  output logic                                      csr_inst_ctrl_write_mode_o,
  output logic                                      csr_inst_ctrl_dbg_o,
  output logic                                      csr_inst_ctrl_clr_o,
  output logic [InstMemAddrWidth-1:0]               csr_inst_wr_addr_o,
  output logic                                      csr_inst_wr_addr_en_o,
  output logic [    CsrDataWidth-1:0]               csr_inst_wr_data_o,
  output logic                                      csr_inst_wr_data_en_o,
  output logic [InstMemAddrWidth-1:0]               csr_inst_rddbg_addr_o,
  input  logic [InstMemAddrWidth-1:0]               csr_inst_pc_i,
  input  logic [    CsrDataWidth-1:0]               csr_inst_at_addr_i,
  // Instruction loop control
  output logic                  [1:0]               csr_inst_loop_mode_o,
  output logic [InstMemAddrWidth-1:0]               csr_loop_jump_addr1_o,
  output logic [InstMemAddrWidth-1:0]               csr_loop_jump_addr2_o,
  output logic [InstMemAddrWidth-1:0]               csr_loop_jump_addr3_o,
  output logic [InstMemAddrWidth-1:0]               csr_loop_end_addr1_o,
  output logic [InstMemAddrWidth-1:0]               csr_loop_end_addr2_o,
  output logic [InstMemAddrWidth-1:0]               csr_loop_end_addr3_o,
  output logic [InstMemAddrWidth-1:0]               csr_loop_count_addr1_o,
  output logic [InstMemAddrWidth-1:0]               csr_loop_count_addr2_o,
  output logic [InstMemAddrWidth-1:0]               csr_loop_count_addr3_o,
  // IM Seeds
  output logic [CsrDataWidth-1:0]                   csr_cim_seed_o,
  output logic [   NumImSets-1:0][CsrDataWidth-1:0] csr_im_seed_o
);

  //---------------------------
  // Wires and logic
  //---------------------------

  // Register set
  logic [NumRegs-1:0][CsrDataWidth-1:0] csr_set;

  // For CSR control
  logic csr_req_success;
  logic csr_rsp_success;

  logic csr_write_req;
  logic csr_read_req;

  // Wiring
  logic [CsrDataWidth-1:0] csr_rd_data;

  //---------------------------
  // Always ready to get
  // NOTE: Might change later on!
  //---------------------------
  assign csr_req_success = csr_req_valid_i &  csr_req_ready_o;
  assign csr_rsp_success = csr_rsp_valid_o &  csr_rsp_ready_i;

  assign csr_write_req   = csr_req_success &  csr_req_write_i;
  assign csr_read_req    = csr_req_success & !csr_req_write_i;

  assign csr_req_ready_o = 1'b1;

  //---------------------------
  // Main CSR set
  //---------------------------
  always_ff @ (posedge clk_i or negedge rst_ni) begin
    if (!rst_ni) begin
      for (int i = 0; i < NumRegs; i++) begin
        csr_set[i] <= {CsrDataWidth{1'b0}};
      end
    end else begin
      if (csr_write_req) begin
        csr_set[csr_req_addr_i] <= csr_req_data_i;
      end else begin
        csr_set <= csr_set;
      end
    end
  end

  //---------------------------
  // Read logic
  //---------------------------
  always_comb begin
    case(csr_req_addr_i)
      CORE_SET_REG_ADDR: begin
        csr_rd_data = {
                                                                 // verilog_lint: waive-start line-length
                                       {(CsrDataWidth-5){1'b0}}, // [31:5] -- Unused
                                                           1'b0, //    [6] WO Core clear (generates pulse)
        csr_set[CORE_SET_REG_ADDR][  CORE_SET_IMB_MUX_BIT_ADDR], //    [5] RW IMB MUX
        csr_set[CORE_SET_REG_ADDR][4:CORE_SET_IMA_MUX_BIT_ADDR], //    [4:3] RW IMA MUX
        csr_set[CORE_SET_REG_ADDR][ CORE_SET_SEQ_TEST_BIT_ADDR], //    [2] RW Sequential test
                                                     csr_busy_i, //    [1] RO Busy
                                                           1'b0  //    [0] WO Start Core (generates pulse)
                                                                // verilog_lint: waive-stop line-length
        };
      end
      AM_NUM_PREDICT_REG_ADDR: begin
        csr_rd_data = csr_set[AM_NUM_PREDICT_REG_ADDR];
      end
      AM_PREDICT_REG_ADDR: begin
        csr_rd_data = csr_am_pred_i;
      end
      INST_CTRL_REG_ADDR: begin
        csr_rd_data = {
                                                                      // verilog_lint: waive-start line-length
                                            {(CsrDataWidth-3){1'b0}}, // [31:3] -- Unused
                                                                1'b0, //    [2] WO Instruction clear
          csr_set[INST_CTRL_REG_ADDR][  INST_CTRL_DBG_MODE_BIT_ADDR], //    [1] RW Instruction debug mode
          csr_set[INST_CTRL_REG_ADDR][INST_CTRL_WRITE_MODE_BIT_ADDR]  //    [0] RW Instruction write mode
                                                                      // verilog_lint: waive-stop line-length

        };
      end
      INST_WRITE_ADDR_REG_ADDR,
      INST_WRITE_DATA_REG_ADDR: begin
        csr_rd_data = {CsrDataWidth{1'b0}};
      end
      INST_RDDBG_ADDR_REG_ADDR: begin
        csr_rd_data = csr_set[INST_RDDBG_ADDR_REG_ADDR];
      end
      INST_PC_ADDR_REG_ADDR: begin
        csr_rd_data = csr_inst_pc_i;
      end
      INST_INST_AT_ADDR_ADDR_REG_ADDR: begin
        csr_rd_data = csr_inst_at_addr_i;
      end
      INST_LOOP_CTRL_REG_ADDR: begin
        csr_rd_data = {
                       {(CsrDataWidth-2){1'b0}}, // [31:2] -- Unused
          csr_set[INST_LOOP_CTRL_REG_ADDR][1:0]  //  [1:0] RW Instruction loop mode
        };
      end
      INST_LOOP_JUMP_ADDR_REG_ADDR,
      INST_LOOP_END_ADDR_REG_ADDR,
      INST_LOOP_COUNT_REG_ADDR: begin
        csr_rd_data = {
                                                  {(CsrDataWidth-2){1'b0}}, // [31:22] -- Unused
          csr_set[csr_req_addr_i][3*InstMemAddrWidth-1:2*InstMemAddrWidth], //   [7:0] RW Loop addr3
          csr_set[csr_req_addr_i][2*InstMemAddrWidth-1:  InstMemAddrWidth], //   [7:0] RW Loop addr2
          csr_set[csr_req_addr_i][  InstMemAddrWidth-1:                 0]  //   [7:0] RW Loop addr1
        };
      end
      CIM_SEED_REG_ADDR: begin
        csr_rd_data = csr_set[CIM_SEED_REG_ADDR];
      end
      default: begin
        // Check the variable length seed IM here
        if((csr_req_addr_i >= IM_BASE_SEED_REG_ADDR) &&
           (csr_req_addr_i < (IM_BASE_SEED_REG_ADDR + NumImSets))) begin
          csr_rd_data = csr_set[csr_req_addr_i];
        end else begin
          csr_rd_data = {CsrDataWidth{1'b0}};
        end
      end

    endcase
  end

  //---------------------------
  // Read control logic
  //---------------------------
  always_ff @ (posedge clk_i or negedge rst_ni) begin
    if (!rst_ni) begin
      csr_rsp_data_o  <= {CsrDataWidth{1'b0}};
      csr_rsp_valid_o <= 1'b0;
    end else begin
      if (csr_read_req) begin
        csr_rsp_data_o  <= csr_rd_data;
        csr_rsp_valid_o <= 1'b1;
      end else if (csr_rsp_success) begin
        csr_rsp_data_o  <= {CsrDataWidth{1'b0}};
        csr_rsp_valid_o <= 1'b0;
      end else begin
        csr_rsp_data_o  <= csr_rsp_data_o;
        csr_rsp_valid_o <= csr_rsp_valid_o;
      end
    end
  end

  //---------------------------
  // Control signals logic
  //---------------------------
  always_comb begin

    //---------------------------
    // Core settings
    //---------------------------
    csr_start_o                = csr_write_req &&
                                (csr_req_addr_i == CORE_SET_REG_ADDR) &&
                                 csr_req_data_i[CORE_SET_START_CORE_BIT_ADDR];
    csr_clr_o                  = csr_write_req &&
                                (csr_req_addr_i == CORE_SET_REG_ADDR) &&
                                 csr_req_data_i[CORE_SET_CORE_CLR_BIT_ADDR];
    csr_seq_test_mode_o        = csr_set[CORE_SET_REG_ADDR][ CORE_SET_SEQ_TEST_BIT_ADDR];
    csr_port_b_cim_o           = csr_set[CORE_SET_REG_ADDR][  CORE_SET_IMB_MUX_BIT_ADDR];
    csr_port_a_cim_o           = csr_set[CORE_SET_REG_ADDR][4:CORE_SET_IMA_MUX_BIT_ADDR];

    //---------------------------
    // AM settings
    //---------------------------
    csr_am_num_pred_o          = csr_set[AM_NUM_PREDICT_REG_ADDR];
    //---------------------------
    // Instruction control settings
    //---------------------------
    csr_inst_ctrl_write_mode_o = csr_set[INST_CTRL_REG_ADDR][INST_CTRL_WRITE_MODE_BIT_ADDR];
    csr_inst_ctrl_dbg_o        = csr_set[INST_CTRL_REG_ADDR][  INST_CTRL_DBG_MODE_BIT_ADDR];
    csr_inst_ctrl_clr_o        =  csr_write_req &&
                                 (csr_req_addr_i == INST_CTRL_REG_ADDR) &&
                                  csr_req_data_i[INST_CTRL_INST_CLR_BIT_ADDR];
    csr_inst_wr_addr_o         = csr_req_data_i[InstMemAddrWidth-1:0];
    csr_inst_wr_addr_en_o      = csr_write_req && (csr_req_addr_i == INST_WRITE_ADDR_REG_ADDR);
    csr_inst_wr_data_o         = csr_req_data_i;
    csr_inst_wr_data_en_o      = csr_write_req && (csr_req_addr_i == INST_WRITE_DATA_REG_ADDR);
    csr_inst_rddbg_addr_o      = csr_set[INST_RDDBG_ADDR_REG_ADDR];
    //---------------------------
    // Instruction loop control
    //---------------------------
    // verilog_lint: waive-start line-length
    csr_inst_loop_mode_o       = csr_set[INST_LOOP_CTRL_REG_ADDR][1:0];
    csr_loop_jump_addr1_o      = csr_set[INST_LOOP_JUMP_ADDR_REG_ADDR][  InstMemAddrWidth-1:                 0];
    csr_loop_jump_addr2_o      = csr_set[INST_LOOP_JUMP_ADDR_REG_ADDR][2*InstMemAddrWidth-1:  InstMemAddrWidth];
    csr_loop_jump_addr3_o      = csr_set[INST_LOOP_JUMP_ADDR_REG_ADDR][3*InstMemAddrWidth-1:2*InstMemAddrWidth];

    csr_loop_end_addr1_o       = csr_set[INST_LOOP_END_ADDR_REG_ADDR][  InstMemAddrWidth-1:                 0];
    csr_loop_end_addr2_o       = csr_set[INST_LOOP_END_ADDR_REG_ADDR][2*InstMemAddrWidth-1:  InstMemAddrWidth];
    csr_loop_end_addr3_o       = csr_set[INST_LOOP_END_ADDR_REG_ADDR][3*InstMemAddrWidth-1:2*InstMemAddrWidth];

    csr_loop_count_addr1_o     = csr_set[INST_LOOP_COUNT_REG_ADDR][  InstMemAddrWidth-1:                 0];
    csr_loop_count_addr2_o     = csr_set[INST_LOOP_COUNT_REG_ADDR][2*InstMemAddrWidth-1:  InstMemAddrWidth];
    csr_loop_count_addr3_o     = csr_set[INST_LOOP_COUNT_REG_ADDR][3*InstMemAddrWidth-1:2*InstMemAddrWidth];
    // verilog_lint: waive-stop line-length
    //---------------------------
    // IM Seeds
    //---------------------------
    csr_cim_seed_o             = csr_set[CIM_SEED_REG_ADDR];
    for (int i = 0; i < NumImSets; i++) begin
      csr_im_seed_o[i]         = csr_set[IM_BASE_SEED_REG_ADDR+i];
    end

  end


endmodule
