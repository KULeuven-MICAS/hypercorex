//---------------------------
// Copyright 2024 KU Leuven
// Ryan Antonio <ryan.antonio@esat.kuleuven.be>
//
// Module: CSR Addressing Package
// Description:
// This module contains the list of CSR
// register and bit addresses
//
// We fix all register address to 32 bits
// but bit addresses to 5-bits
//---------------------------

// verilog_lint: waive-start parameter-name-style
package csr_addr_pkg;
  // CORE Settings
  localparam logic [31:0] CORE_SET_REG_ADDR               = 32'd0;
  localparam logic [ 4:0] CORE_SET_START_CORE_BIT_ADDR    = 5'd0;
  localparam logic [ 4:0] CORE_SET_BUSY_BIT_ADDR          = 5'd1;
  localparam logic [ 4:0] CORE_SET_SEQ_TEST_BIT_ADDR      = 5'd2;
  localparam logic [ 4:0] CORE_SET_IMA_MUX_BIT_ADDR       = 5'd3;
  localparam logic [ 4:0] CORE_SET_IMB_MUX_BIT_ADDR       = 5'd5;
  localparam logic [ 4:0] CORE_SET_CORE_CLR_BIT_ADDR      = 5'd6;
  localparam logic [ 4:0] CORE_SET_CORE_FIFO_CLR_BIT_ADDR = 5'd7;
  localparam logic [ 4:0] CORE_SET_CORE_REGS_CLR_BIT_ADDR = 5'd8;
  localparam logic [ 4:0] CORE_SET_CORE_DSLC_CLR_BIT_ADDR = 5'd9;

  // AM Settings
  localparam logic [31:0] AM_NUM_PREDICT_REG_ADDR         = 32'd1;
  localparam logic [31:0] AM_PREDICT_REG_ADDR             = 32'd2;
  localparam logic [ 4:0] AM_PREDICT_BIT_ADDR             = 5'd0;
  localparam logic [ 4:0] AM_PREDICT_VALID_BIT_ADDR       = 5'd8;

  // Instruction controls
  localparam logic [31:0] INST_CTRL_REG_ADDR              = 32'd3;
  localparam logic [ 4:0] INST_CTRL_WRITE_MODE_BIT_ADDR   = 5'd0;
  localparam logic [ 4:0] INST_CTRL_DBG_MODE_BIT_ADDR     = 5'd1;
  localparam logic [ 4:0] INST_CTRL_INST_CLR_BIT_ADDR     = 5'd2;

  localparam logic [31:0] INST_WRITE_ADDR_REG_ADDR        = 32'd4;
  localparam logic [31:0] INST_WRITE_DATA_REG_ADDR        = 32'd5;
  localparam logic [31:0] INST_RDDBG_ADDR_REG_ADDR        = 32'd6;
  localparam logic [31:0] INST_PC_ADDR_REG_ADDR           = 32'd7;
  localparam logic [31:0] INST_INST_AT_ADDR_ADDR_REG_ADDR = 32'd8;

  // Instruction loop control
  localparam logic [31:0] INST_LOOP_CTRL_REG_ADDR         = 32'd9;
  localparam logic [ 4:0] INST_LOOP_CTRL_MODE_BIT_ADDR    = 5'd0;
  localparam logic [ 4:0] INST_LOOP_CTRL_HVDIM_EXTEND_COUNT = 5'd2;

  localparam logic [31:0] INST_LOOP_JUMP_ADDR_REG_ADDR    = 32'd10;
  localparam logic [ 4:0] INST_LOOP_JUMP_ADDR1_BIT_ADDR   = 5'd0;
  localparam logic [ 4:0] INST_LOOP_JUMP_ADDR2_BIT_ADDR   = 5'd8;
  localparam logic [ 4:0] INST_LOOP_JUMP_ADDR3_BIT_ADDR   = 5'd16;

  localparam logic [31:0] INST_LOOP_END_ADDR_REG_ADDR     = 32'd11;
  localparam logic [ 4:0] INST_LOOP_END_ADDR1_BIT_ADDR    = 5'd0;
  localparam logic [ 4:0] INST_LOOP_END_ADDR2_BIT_ADDR    = 5'd8;
  localparam logic [ 4:0] INST_LOOP_END_ADDR3_BIT_ADDR    = 5'd16;

  localparam logic [31:0] INST_LOOP_COUNT_REG_ADDR        = 32'd12;
  localparam logic [ 4:0] INST_LOOP_COUNT_ADDR1_BIT_ADDR  = 5'd0;
  localparam logic [ 4:0] INST_LOOP_COUNT_ADDR2_BIT_ADDR  = 5'd8;
  localparam logic [ 4:0] INST_LOOP_COUNT_ADDR3_BIT_ADDR  = 5'd16;

  // Data slicer configurationsss
  localparam logic [31:0] DATA_SRC_CTRL_REG_ADDR          = 32'd13;
  localparam logic [ 4:0] DATA_SLICE_MODE_A_BIT_ADDR      = 5'd0;
  localparam logic [ 4:0] DATA_SLICE_MODE_B_BIT_ADDR      = 5'd2;
  localparam logic [ 4:0] DATA_SRC_SEL_BIT_ADDR           = 5'd4;
  localparam logic [31:0] DATA_SLICE_NUM_ELEM_A_REG_ADDR  = 32'd14;
  localparam logic [31:0] DATA_SLICE_NUM_ELEM_B_REG_ADDR  = 32'd15;
  localparam logic [31:0] DATA_SRC_AUTO_START_A_REG_ADDR  = 32'd16;
  localparam logic [31:0] DATA_SRC_AUTO_START_B_REG_ADDR  = 32'd17;
  localparam logic [31:0] DATA_SRC_AUTO_NUM_A_REG_ADDR    = 32'd18;
  localparam logic [31:0] DATA_SRC_AUTO_NUM_B_REG_ADDR    = 32'd19;

  // Observable general purpose register
  localparam logic [31:0] OBSERVABLE_REG_DATA             = 32'd20;

endpackage
// verilog_lint: waive-stop parameter-name-style
