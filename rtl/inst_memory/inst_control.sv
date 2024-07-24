//---------------------------
// Copyright 2024 KU Leuven
// Ryan Antonio <ryan.antonio@esat.kuleuven.be>
//
// Module: Instruction Control
// Description:
// This module handles the management or
// control of the instruction memory
//---------------------------

module inst_control # (
  parameter int unsigned RegAddrWidth     = 32,
  parameter int unsigned InstMemDepth     = 128,
  // Don't touch!
  parameter int unsigned InstMemAddrWidth = $clog2(InstMemDepth)
)(
  // Clocks and reset
  input  logic                    clk_i,
  input  logic                    rst_ni,
  // Control signals
  input  logic                    clr_i,
  input  logic                    en_i,
  input  logic                    stall_i,
  input  logic [RegAddrWidth-1:0] inst_wr_addr_i,
  input  logic [RegAddrWidth-1:0] inst_wr_data_i,
  input  logic                    inst_wr_en_i,
  output logic [RegAddrWidth-1:0] inst_pc_o,
  output logic [RegAddrWidth-1:0] inst_rd_o,
  // Debug control signals
  input  logic                    dbg_en_i,
  input  logic [RegAddrWidth-1:0] dbg_addr_i
);

  //---------------------------
  // Wires and Logic
  //---------------------------
  logic [InstMemAddrWidth-1:0] program_counter;
  logic [InstMemAddrWidth-1:0] inst_rd_addr;

  //---------------------------
  // Direct Assignments
  //---------------------------
  assign inst_pc_o    = program_counter;
  assign inst_rd_addr = (dbg_en_i) ? dbg_addr_i[InstMemAddrWidth-1:0] : program_counter;

  //---------------------------
  // Program counter
  // Stall when stall is asserted
  // or when debug is asserted
  //---------------------------
  always_ff @ (posedge clk_i or negedge rst_ni) begin
    if (!rst_ni) begin
      program_counter <= {InstMemAddrWidth{1'b0}};
    end else begin
      if(clr_i) begin
        program_counter <= {InstMemAddrWidth{1'b0}};
      end else if (en_i && !stall_i && !dbg_en_i) begin
        program_counter <= program_counter + 1;
      end else begin
        program_counter <= program_counter;
      end
    end
  end

  //---------------------------
  // Instruction memory
  // Use register for this but can
  // be replaced with an actual memory
  //---------------------------

  reg_file_1w1r #(
    .DataWidth  ( RegAddrWidth                         ),
    .NumRegs    ( InstMemDepth                         )
  ) i_inst_mem (
    // Clocks and resets
    .clk_i      ( clk_i                                ),
    .rst_ni     ( rst_ni                               ),
    // Write port
    .clr_i      ( clr_i                                ),
    .wr_addr_i  ( inst_wr_addr_i[InstMemAddrWidth-1:0] ),
    .wr_data_i  ( inst_wr_data_i                       ),
    .wr_en_i    ( inst_wr_en_i                         ),
    // Read port A
    .rd_addr_i  ( inst_rd_addr                         ),
    .rd_data_o  ( inst_rd_o                            )
  );

endmodule
