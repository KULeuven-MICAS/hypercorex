//---------------------------
// Copyright 2024 KU Leuven
// Ryan Antonio <ryan.antonio@esat.kuleuven.be>
//
// Module: Instruction Decode
// Description:
// This module is an instruction decoder
// The parameters should match the
// hv encoder module.
//
// Take note that this is very specific
// hence some slices are fixed according
// to how we code it.
//
// Instruction format is simple:
// -------------------------------------------------------------
// | 21b func | 3b type | 2b shift_amt | 2b rb | 2b ra | 2b rd |
// -------------------------------------------------------------
//---------------------------

module inst_decode import hypercorex_inst_pkg::*; #(
  parameter int unsigned InstWidth      = 32,
  parameter int unsigned ALUMuxWidth    = 2,
  parameter int unsigned ALUMaxShiftAmt = 128,
  parameter int unsigned BundMuxWidth   = 2,
  parameter int unsigned RegMuxWidth    = 2,
  parameter int unsigned QvMuxWidth     = 2,
  parameter int unsigned RegNum         = 4,
  // Don't touch!
  parameter int unsigned NumALUOps      = 8,
  parameter int unsigned ALUOpsWidth    = $clog2(NumALUOps     ),
  parameter int unsigned ShiftWidth     = $clog2(ALUMaxShiftAmt),
  parameter int unsigned RegAddrWidth   = $clog2(RegNum        )
)(
  // Input instruction
  input  logic [   InstWidth-1:0] inst_code_i,
  input  logic                    enable_i,
  // Control ports for IM
  output logic                    im_a_pop_o,
  output logic                    im_b_pop_o,
  // Control ports for ALU
  output logic [ ALUMuxWidth-1:0] alu_mux_a_o,
  output logic [ ALUMuxWidth-1:0] alu_mux_b_o,
  output logic [ ALUOpsWidth-1:0] alu_ops_o,
  output logic [  ShiftWidth-1:0] alu_shift_amt_o,
  // Control ports for bundlers
  output logic [BundMuxWidth-1:0] bund_mux_a_o,
  output logic [BundMuxWidth-1:0] bund_mux_b_o,
  output logic                    bund_valid_a_o,
  output logic                    bund_valid_b_o,
  output logic                    bund_clr_a_o,
  output logic                    bund_clr_b_o,
  // Control ports for register ops
  output logic [ RegMuxWidth-1:0] reg_mux_o,
  output logic [RegAddrWidth-1:0] reg_rd_addr_a_o,
  output logic [RegAddrWidth-1:0] reg_rd_addr_b_o,
  output logic [RegAddrWidth-1:0] reg_wr_addr_o,
  output logic                    reg_wr_en_o,
  // Control ports for query HV
  output logic                    qhv_clr_o,
  output logic                    qhv_wen_o,
  output logic [  QvMuxWidth-1:0] qhv_mux_o,
  // Control port for the AM
  output logic                    am_search_o,
  output logic                    am_load_o
);

  //---------------------------
  // Wiring
  //---------------------------
  logic [InstWidth-1:0] inst_code;


  //---------------------------
  // Assignments
  //---------------------------
  assign reg_rd_addr_b_o = inst_code[1:0];
  assign reg_rd_addr_a_o = inst_code[3:2];
  assign reg_wr_addr_o   = inst_code[5:4];
  assign alu_shift_amt_o = inst_code[7:6];

  // For disabling the control signals if not yet used
  assign inst_code = (enable_i) ? inst_code_i : {InstWidth{1'b0}};

  //---------------------------
  // Main instruction decoder
  // the order of signals matches
  // that of the order above
  //---------------------------
  always_comb begin

    // Contorl ports for IM
    im_a_pop_o = '0;
    im_b_pop_o = '0;

    // Control ports for ALU
    alu_mux_a_o     = '0;
    alu_mux_b_o     = '0;
    alu_ops_o       = '0;

    // Control ports for bundlers
    bund_mux_a_o   = '0;
    bund_mux_b_o   = '0;
    bund_valid_a_o = '0;
    bund_valid_b_o = '0;
    bund_clr_a_o   = '0;
    bund_clr_b_o   = '0;

    // Control ports for register ops
    reg_mux_o       = '0;
    reg_wr_en_o     = '0;

    // Control ports for query HV
    qhv_clr_o = '0;
    qhv_wen_o = '0;
    qhv_mux_o = '0;

    // Control port for AM search
    am_search_o = '0;
    am_load_o   = '0;

    unique casez (inst_code)
      // Default for when unknown instructions come in
      default: begin
        // Contorl ports for IM
        im_a_pop_o = '0;
        im_b_pop_o = '0;

        // Control ports for ALU
        alu_mux_a_o     = '0;
        alu_mux_b_o     = '0;
        alu_ops_o       = '0;

        // Control ports for bundlers
        bund_mux_a_o   = '0;
        bund_mux_b_o   = '0;
        bund_valid_a_o = '0;
        bund_valid_b_o = '0;
        bund_clr_a_o   = '0;
        bund_clr_b_o   = '0;

        // Control ports for register ops
        reg_mux_o       = '0;
        reg_wr_en_o     = '0;

        // Control ports for query HV
        qhv_clr_o = '0;
        qhv_wen_o = '0;
        qhv_mux_o = '0;

        // Control port for AM search
        am_search_o = '0;
        am_load_o   = '0;
      end
      //---------------------------
      // IM
      //---------------------------
      IMA_REG: begin
        im_a_pop_o  = 1'b1;
        alu_mux_a_o = 2'b00;
        reg_mux_o   = 2'b00;
        reg_wr_en_o = 1'b1;
        alu_ops_o   = 3'b001;
      end
      IMB_REG: begin
        im_b_pop_o  = 1'b1;
        alu_mux_b_o = 2'b00;
        reg_mux_o   = 2'b00;
        reg_wr_en_o = 1'b1;
        alu_ops_o   = 3'b010;
      end
      IMAB_BIND_REG: begin
        im_a_pop_o  = 1'b1;
        im_b_pop_o  = 1'b1;
        alu_mux_a_o = 2'b00;
        alu_mux_b_o = 2'b00;
        reg_mux_o   = 2'b00;
        reg_wr_en_o = 1'b1;
        alu_ops_o   = 3'b000;
      end
      IMA_PERM_REG: begin
        im_a_pop_o  = 1'b1;
        alu_mux_a_o = 2'b00;
        reg_mux_o   = 2'b00;
        reg_wr_en_o = 1'b1;
        alu_ops_o   = 3'b011;
      end
      //---------------------------
      // IM-REG
      //---------------------------
      IMA_REGB_BIND_REG: begin
        im_a_pop_o  = 1'b1;
        alu_mux_a_o = 2'b00;
        alu_mux_b_o = 2'b01;
        reg_mux_o   = 2'b00;
        reg_wr_en_o = 1'b1;
        alu_ops_o   = 3'b000;
      end
      IMB_REGA_BIND_REG: begin
        im_b_pop_o  = 1'b1;
        alu_mux_a_o = 2'b01;
        alu_mux_b_o = 2'b00;
        reg_mux_o   = 2'b00;
        reg_wr_en_o = 1'b1;
        alu_ops_o   = 3'b000;
      end
      //---------------------------
      // IM-BUND
      //---------------------------
      IMA_BUNDA: begin
        im_a_pop_o     = 1'b1;
        bund_mux_a_o   = 2'b10;
        bund_valid_a_o = 1'b1;
      end
      IMA_BUNDB: begin
        im_a_pop_o     = 1'b1;
        bund_mux_b_o   = 2'b10;
        bund_valid_b_o = 1'b1;
      end
      IMAB_BIND_BUNDA: begin
        im_a_pop_o     = 1'b1;
        im_b_pop_o     = 1'b1;
        alu_mux_a_o    = 2'b00;
        alu_mux_b_o    = 2'b00;
        bund_mux_a_o   = 2'b00;
        bund_valid_a_o = 1'b1;
        alu_ops_o   = 3'b000;
      end
      IMAB_BIND_BUNDB: begin
        im_a_pop_o     = 1'b1;
        im_b_pop_o     = 1'b1;
        alu_mux_a_o    = 2'b00;
        alu_mux_b_o    = 2'b00;
        bund_mux_b_o   = 2'b00;
        bund_valid_b_o = 1'b1;
        alu_ops_o      = 3'b000;
      end
      IMA_PERM_BUNDA: begin
        im_a_pop_o     = 1'b1;
        alu_mux_a_o    = 2'b00;
        bund_mux_a_o   = 2'b00;
        bund_valid_a_o = 1'b1;
        alu_ops_o      = 3'b011;
      end
      IMA_PERM_BUNDB: begin
        im_a_pop_o     = 1'b1;
        alu_mux_a_o    = 2'b00;
        bund_mux_b_o   = 2'b00;
        bund_valid_b_o = 1'b1;
        alu_ops_o      = 3'b011;
      end
      //---------------------------
      // REG
      //---------------------------
      REGAB_BIND_REG: begin
        alu_mux_a_o = 2'b01;
        alu_mux_b_o = 2'b01;
        reg_mux_o   = 2'b00;
        reg_wr_en_o = 1'b1;
        alu_ops_o   = 3'b000;
      end
      REGA_PERM_REG: begin
        alu_mux_a_o = 2'b01;
        reg_mux_o   = 2'b00;
        reg_wr_en_o = 1'b1;
        alu_ops_o   = 3'b011;
      end
      MV_REG: begin
        alu_mux_a_o = 2'b01;
        reg_mux_o   = 2'b00;
        reg_wr_en_o = 1'b1;
        alu_ops_o   = 3'b001;
      end
      //---------------------------
      // REG-BUND
      //---------------------------
      REGAB_BIND_BUNDA: begin
        alu_mux_a_o    = 2'b01;
        alu_mux_b_o    = 2'b01;
        bund_mux_a_o   = 2'b00;
        bund_valid_a_o = 1'b1;
        alu_ops_o      = 3'b000;
      end
      REGAB_BIND_BUNDB: begin
        alu_mux_a_o    = 2'b01;
        alu_mux_b_o    = 2'b01;
        bund_mux_b_o   = 2'b00;
        bund_valid_b_o = 1'b1;
        alu_ops_o      = 3'b000;
      end
      REGA_PERM_BUNDA: begin
        alu_mux_a_o    = 2'b01;
        bund_mux_a_o   = 2'b00;
        bund_valid_a_o = 1'b1;
        alu_ops_o      = 3'b011;
      end
      REGA_PERM_BUNDB: begin
        alu_mux_a_o    = 2'b01;
        bund_mux_b_o   = 2'b00;
        bund_valid_b_o = 1'b1;
        alu_ops_o      = 3'b011;
      end
      REGA_BUNDA_BIND_REG: begin
        alu_mux_a_o = 2'b01;
        alu_mux_b_o = 2'b10;
        reg_mux_o   = 2'b00;
        reg_wr_en_o = 1'b1;
        alu_ops_o   = 3'b000;
      end
      REGA_BUNDB_BIND_REG: begin
        alu_mux_a_o = 2'b01;
        alu_mux_b_o = 2'b11;
        reg_mux_o   = 2'b00;
        reg_wr_en_o = 1'b1;
        alu_ops_o   = 3'b000;
      end
      BUNDA_PERM_REG: begin
        alu_mux_a_o = 2'b10;
        reg_mux_o   = 2'b00;
        reg_wr_en_o = 1'b1;
        alu_ops_o   = 3'b011;
      end
      BUNDB_PERM_REG: begin
        alu_mux_a_o = 2'b11;
        reg_mux_o   = 2'b00;
        reg_wr_en_o = 1'b1;
        alu_ops_o   = 3'b011;
      end
      MV_BUNDA_REG: begin
        reg_mux_o   = 2'b10;
        reg_wr_en_o = 1'b1;
      end
      MV_BUNDB_REG: begin
        reg_mux_o   = 2'b11;
        reg_wr_en_o = 1'b1;
      end
      MV_REG_BUNDA: begin
        bund_mux_a_o   = 2'b11;
        bund_valid_a_o = 1'b1;
      end
      MV_REG_BUNDB: begin
        bund_mux_b_o   = 2'b11;
        bund_valid_b_o = 1'b1;
      end
      //---------------------------
      // REG-BUND
      //---------------------------
      MV_BUNDA_BUNDB: begin
        bund_mux_b_o   = 2'b01;
        bund_valid_b_o = 1'b1;
      end
      MV_BUNDB_BUNDA: begin
        bund_mux_a_o   = 2'b01;
        bund_valid_a_o = 1'b1;
      end
      CLR_BUNDA: begin
        bund_clr_a_o   = 1'b1;
      end
      CLR_BUNDB: begin
        bund_clr_b_o   = 1'b1;
      end
      //---------------------------
      // QHV
      //---------------------------
      MV_REG_QHV: begin
        qhv_mux_o   = 2'b01;
        qhv_wen_o   = 1'b1;
      end
      MV_BUNDA_QHV: begin
        qhv_mux_o   = 2'b10;
        qhv_wen_o   = 1'b1;
      end
      MV_BUNDB_QHV: begin
        qhv_mux_o   = 2'b11;
        qhv_wen_o   = 1'b1;
      end
      CLR_QHV: begin
        qhv_clr_o   = 1'b1;
      end
      //---------------------------
      // AM Modules
      //---------------------------
      AM_SEARCH: begin
        am_search_o  = 1'b1;
      end
      AM_LOAD: begin
        am_load_o  = 1'b1;
      end
    endcase
  end


endmodule
