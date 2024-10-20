//---------------------------
// Copyright 2024 KU Leuven
// Ryan Antonio <ryan.antonio@esat.kuleuven.be>
//
// Module: Instruction List Package
// Description:
// This module contains the list of instructions
// and the corresponding codes for decoding
//
// Instruction format is simple:
// ---------------------------------------------------------------
// | 21b func | 3b type | 2b shift_amt | 2b rs2 | 2b rs1 | 2b rd |
// ---------------------------------------------------------------
//---------------------------

// verilog_lint: waive-start parameter-name-style
package hypercorex_inst_pkg;
  // IM
  localparam logic [31:0] IMA_REG                 = 32'b??????????????????001_000_??_??_??_??;
  localparam logic [31:0] IMB_REG                 = 32'b??????????????????010_000_??_??_??_??;
  localparam logic [31:0] IMAB_BIND_REG           = 32'b??????????????????011_000_??_??_??_??;
  localparam logic [31:0] IMA_PERM_R_REG          = 32'b??????????????????100_000_??_??_??_??;
  localparam logic [31:0] IMA_PERM_L_REG          = 32'b??????????????????101_000_??_??_??_??;
  // IM-REG
  localparam logic [31:0] IMA_REGB_BIND_REG       = 32'b???????????????????01_001_??_??_??_??;
  localparam logic [31:0] IMB_REGA_BIND_REG       = 32'b???????????????????10_001_??_??_??_??;
  // IM-BUND
  localparam logic [31:0] IMA_BUNDA               = 32'b?????????????????0001_010_??_??_??_??;
  localparam logic [31:0] IMA_BUNDB               = 32'b?????????????????0010_010_??_??_??_??;
  localparam logic [31:0] IMAB_BIND_BUNDA         = 32'b?????????????????0011_010_??_??_??_??;
  localparam logic [31:0] IMAB_BIND_BUNDB         = 32'b?????????????????0100_010_??_??_??_??;
  localparam logic [31:0] IMA_PERM_R_BUNDA        = 32'b?????????????????0101_010_??_??_??_??;
  localparam logic [31:0] IMA_PERM_R_BUNDB        = 32'b?????????????????0110_010_??_??_??_??;
  localparam logic [31:0] IMA_PERM_L_BUNDA        = 32'b?????????????????0111_010_??_??_??_??;
  localparam logic [31:0] IMA_PERM_L_BUNDB        = 32'b?????????????????1000_010_??_??_??_??;
  // REG
  localparam logic [31:0] REGAB_BIND_REG          = 32'b??????????????????001_011_??_??_??_??;
  localparam logic [31:0] REGA_PERM_R_REG         = 32'b??????????????????010_011_??_??_??_??;
  localparam logic [31:0] REGA_PERM_L_REG         = 32'b??????????????????011_011_??_??_??_??;
  localparam logic [31:0] MV_REG                  = 32'b??????????????????100_011_??_??_??_??;
  // REG-BUND
  localparam logic [31:0] REGAB_BIND_BUNDA        = 32'b????????????????00001_100_??_??_??_??;
  localparam logic [31:0] REGAB_BIND_BUNDB        = 32'b????????????????00010_100_??_??_??_??;
  localparam logic [31:0] REGA_PERM_R_BUNDA       = 32'b????????????????00011_100_??_??_??_??;
  localparam logic [31:0] REGA_PERM_R_BUNDB       = 32'b????????????????00100_100_??_??_??_??;
  localparam logic [31:0] REGA_PERM_L_BUNDA       = 32'b????????????????00101_100_??_??_??_??;
  localparam logic [31:0] REGA_PERM_L_BUNDB       = 32'b????????????????00110_100_??_??_??_??;
  localparam logic [31:0] REGA_BUNDA_BIND_REG     = 32'b????????????????00111_100_??_??_??_??;
  localparam logic [31:0] REGA_BUNDB_BIND_REG     = 32'b????????????????01000_100_??_??_??_??;
  localparam logic [31:0] BUNDA_PERM_R_REG        = 32'b????????????????01001_100_??_??_??_??;
  localparam logic [31:0] BUNDB_PERM_R_REG        = 32'b????????????????01010_100_??_??_??_??;
  localparam logic [31:0] BUNDA_PERM_L_REG        = 32'b????????????????01011_100_??_??_??_??;
  localparam logic [31:0] BUNDB_PERM_L_REG        = 32'b????????????????01100_100_??_??_??_??;
  localparam logic [31:0] MV_BUNDA_REG            = 32'b????????????????01101_100_??_??_??_??;
  localparam logic [31:0] MV_BUNDB_REG            = 32'b????????????????01110_100_??_??_??_??;
  localparam logic [31:0] MV_REG_BUNDA            = 32'b????????????????01111_100_??_??_??_??;
  localparam logic [31:0] MV_REG_BUNDB            = 32'b????????????????10000_100_??_??_??_??;
  // BUND
  localparam logic [31:0] MV_BUNDA_BUNDB          = 32'b?????????????????0001_101_??_??_??_??;
  localparam logic [31:0] MV_BUNDB_BUNDA          = 32'b?????????????????0010_101_??_??_??_??;
  localparam logic [31:0] CLR_BUNDA               = 32'b?????????????????0011_101_??_??_??_??;
  localparam logic [31:0] CLR_BUNDB               = 32'b?????????????????0100_101_??_??_??_??;
  // QHV
  localparam logic [31:0] MV_REG_QHV              = 32'b?????????????????0001_110_??_??_??_??;
  localparam logic [31:0] MV_BUNDA_QHV            = 32'b?????????????????0010_110_??_??_??_??;
  localparam logic [31:0] MV_BUNDB_QHV            = 32'b?????????????????0011_110_??_??_??_??;
  localparam logic [31:0] CLR_QHV                 = 32'b?????????????????0100_110_??_??_??_??;
  // AM Search
  localparam logic [31:0] AM_SEARCH               = 32'b?????????????????0001_111_??_??_??_??;
  localparam logic [31:0] AM_LOAD                 = 32'b?????????????????0010_111_??_??_??_??;


endpackage
// verilog_lint: waive-stop parameter-name-style
