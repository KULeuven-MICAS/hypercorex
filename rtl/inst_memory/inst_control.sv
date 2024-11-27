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
  parameter int unsigned RegAddrWidth       = 32,
  parameter int unsigned InstMemDepth       = 128,
  // Don't touch!
  parameter int unsigned LoopNumStates      = 4,
  parameter int unsigned InstLoopCountWidth = 10,
  parameter int unsigned LoopNumWidth       = $clog2(LoopNumStates),
  parameter int unsigned InstMemAddrWidth   = $clog2(InstMemDepth)
)(
  // Clocks and reset
  input  logic                        clk_i,
  input  logic                        rst_ni,
  // Control signals
  input  logic                        clr_i,
  input  logic                        start_i,
  input  logic                        stall_i,
  output logic                        enable_o,
  // Instruction update signals
  input  logic                        inst_pc_reset_i,
  input  logic                        inst_wr_mode_i,
  input  logic [InstMemAddrWidth-1:0] inst_wr_addr_i,
  input  logic                        inst_wr_addr_en_i,
  input  logic [RegAddrWidth-1:0]     inst_wr_data_i,
  input  logic                        inst_wr_data_en_i,
  output logic [InstMemAddrWidth-1:0] inst_pc_o,
  output logic [RegAddrWidth-1:0]     inst_rd_o,
  // CSR control for loop control
  input  logic [LoopNumWidth-1:0]     inst_loop_mode_i,
  input  logic [InstMemAddrWidth-1:0] inst_loop_jump_addr1_i,
  input  logic [InstMemAddrWidth-1:0] inst_loop_jump_addr2_i,
  input  logic [InstMemAddrWidth-1:0] inst_loop_jump_addr3_i,
  input  logic [InstMemAddrWidth-1:0] inst_loop_end_addr1_i,
  input  logic [InstMemAddrWidth-1:0] inst_loop_end_addr2_i,
  input  logic [InstMemAddrWidth-1:0] inst_loop_end_addr3_i,
  input  logic [InstLoopCountWidth-1:0] inst_loop_count_addr1_i,
  input  logic [InstLoopCountWidth-1:0] inst_loop_count_addr2_i,
  input  logic [InstLoopCountWidth-1:0] inst_loop_count_addr3_i,
  // Debug control signals
  input  logic                        dbg_en_i,
  input  logic [InstMemAddrWidth-1:0] dbg_addr_i
);

  //---------------------------
  // Wires and Logic
  //---------------------------
  logic [InstMemAddrWidth-1:0] program_counter;
  logic [InstMemAddrWidth-1:0] inst_rd_addr;

  logic                        inst_jump;
  logic [InstMemAddrWidth-1:0] inst_jump_addr;

  logic                        inst_loop_done;
  logic                        enable_core;

  //---------------------------
  // Direct Assignments
  //---------------------------
  // Make sure to expand to avoid synthesis errors
  assign inst_pc_o    = {{(RegAddrWidth-InstMemAddrWidth){1'b0}}, program_counter};
  assign inst_rd_addr = (dbg_en_i) ? dbg_addr_i[InstMemAddrWidth-1:0] : program_counter;
  assign enable_o     = enable_core;

  //---------------------------
  // Enable core register
  //---------------------------
  always_ff @ (posedge clk_i or negedge rst_ni) begin
    if (!rst_ni) begin
      enable_core <= 1'b0;
    end else begin
      if(start_i) begin
        enable_core <= 1'b1;
      end else if (inst_loop_done) begin
        enable_core <= 1'b0;
      end else begin
        enable_core <= enable_core;
      end
    end
  end


  //---------------------------
  // Instruction Loop Controller
  //---------------------------
  inst_loop_control # (
    // Don't touch parameter!
    .InstMemAddrWidth         (InstMemAddrWidth)
  ) i_inst_loop_control (
    // Clocks and reset
    .clk_i                    ( clk_i                                         ),
    .rst_ni                   ( rst_ni                                        ),
    // Control signals
    .clr_i                    ( clr_i                                         ),
    .en_i                     ( enable_core                                   ),
    .stall_i                  ( stall_i                                       ),
    .dbg_en_i                 ( dbg_en_i                                      ),
    // Program counter from inst control
    .inst_pc_i                ( program_counter                               ),
    // Loop control from CSR registers
    .inst_loop_mode_i         ( inst_loop_mode_i                              ),
    .inst_loop_jump_addr1_i   ( inst_loop_jump_addr1_i[InstMemAddrWidth-1:0]  ),
    .inst_loop_jump_addr2_i   ( inst_loop_jump_addr2_i[InstMemAddrWidth-1:0]  ),
    .inst_loop_jump_addr3_i   ( inst_loop_jump_addr3_i[InstMemAddrWidth-1:0]  ),
    .inst_loop_end_addr1_i    ( inst_loop_end_addr1_i[InstMemAddrWidth-1:0]   ),
    .inst_loop_end_addr2_i    ( inst_loop_end_addr2_i[InstMemAddrWidth-1:0]   ),
    .inst_loop_end_addr3_i    ( inst_loop_end_addr3_i[InstMemAddrWidth-1:0]   ),
    .inst_loop_count_addr1_i  ( inst_loop_count_addr1_i                       ),
    .inst_loop_count_addr2_i  ( inst_loop_count_addr2_i                       ),
    .inst_loop_count_addr3_i  ( inst_loop_count_addr3_i                       ),
    // Loop control signals
    .inst_jump_o              ( inst_jump                                     ),
    .inst_jump_addr_o         ( inst_jump_addr                                ),
    // Loop done signal
    .inst_loop_done_o         ( inst_loop_done                                )
  );

  //---------------------------
  // Program counter
  // Stall when stall is asserted
  // or when debug is asserted
  //---------------------------
  always_ff @ (posedge clk_i or negedge rst_ni) begin
    if (!rst_ni) begin
      program_counter <= {InstMemAddrWidth{1'b0}};
    end else begin

      // General clear
      if(clr_i || inst_pc_reset_i) begin
        program_counter <= {InstMemAddrWidth{1'b0}};

      // Instruction write mode
      end else if (inst_wr_mode_i) begin
        // Over-write program counter when we write
        // a new write address
        if (inst_wr_addr_en_i) begin
          // Make sure to slice to fit the program counter properly
          program_counter <= inst_wr_addr_i[InstMemAddrWidth-1:0];
        end else if (inst_wr_data_en_i) begin
          // Auto-increment program counter when we write new data
          program_counter <= program_counter + 1;
        end else begin
          program_counter <= program_counter;
        end

      // Normal operation mode
      end else if (enable_core && !stall_i && !dbg_en_i) begin

        // Allow instruction address jumping
        if (inst_jump) begin
          program_counter <= inst_jump_addr;
        end else begin
          program_counter <= program_counter + 1;
        end

      // Default stall
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
    .DataWidth  ( RegAddrWidth      ),
    .NumRegs    ( InstMemDepth      )
  ) i_inst_mem (
    // Clocks and resets
    .clk_i      ( clk_i             ),
    .rst_ni     ( rst_ni            ),
    // Write port
    .clr_i      ( clr_i             ),
    .wr_addr_i  ( program_counter   ),
    .wr_data_i  ( inst_wr_data_i    ),
    .wr_en_i    ( inst_wr_data_en_i ),
    // Read port A
    .rd_addr_i  ( inst_rd_addr      ),
    .rd_data_o  ( inst_rd_o         )
  );

endmodule
