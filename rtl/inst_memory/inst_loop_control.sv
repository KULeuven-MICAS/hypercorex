//---------------------------
// Copyright 2024 KU Leuven
// Ryan Antonio <ryan.antonio@esat.kuleuven.be>
//
// Module: Instruction Loop Control
// Description:
// This module handles the instruction loop
// counting and logic
//---------------------------

module inst_loop_control # (
  parameter int unsigned InstMemAddrWidth = 32,
  // Don't touch
  parameter int unsigned InstLoopCountWidth = 16,
  parameter int unsigned LoopNumStates = 7,
  parameter int unsigned LoopNumWidth  = $clog2(LoopNumStates)
)(
  // Clocks and reset
  input  logic                         clk_i,
  input  logic                         rst_ni,
  // Control signals
  input  logic                         clr_i,
  input  logic                         en_i,
  input  logic                         stall_i,
  input  logic                         dbg_en_i,
  // Program counter from inst control
  input  logic [InstMemAddrWidth-1:0]  inst_pc_i,
  // Loop control from CSR registers
  input  logic [    LoopNumWidth-1:0]  inst_loop_mode_i,
  // Jump addresses
  input  logic [InstMemAddrWidth-1:0]  inst_loop_jump_addr1_i,
  input  logic [InstMemAddrWidth-1:0]  inst_loop_jump_addr2_i,
  input  logic [InstMemAddrWidth-1:0]  inst_loop_jump_addr3_i,
  input  logic [InstMemAddrWidth-1:0]  inst_loop_jump_addr4_i,
  // Loop end addresses
  input  logic [InstMemAddrWidth-1:0]  inst_loop_end_addr1_i,
  input  logic [InstMemAddrWidth-1:0]  inst_loop_end_addr2_i,
  input  logic [InstMemAddrWidth-1:0]  inst_loop_end_addr3_i,
  input  logic [InstMemAddrWidth-1:0]  inst_loop_end_addr4_i,
  // Loop counts
  input  logic [InstLoopCountWidth-1:0]  inst_loop_count_addr1_i,
  input  logic [InstLoopCountWidth-1:0]  inst_loop_count_addr2_i,
  input  logic [InstLoopCountWidth-1:0]  inst_loop_count_addr3_i,
  input  logic [InstLoopCountWidth-1:0]  inst_loop_count_addr4_i,
  // Loop control signals
  output logic                         inst_jump_o,
  output logic [InstMemAddrWidth-1:0]  inst_jump_addr_o,
  // Status signal
  output logic                         inst_loop_done_o
);

  //---------------------------
  // Local parameters
  //---------------------------
  localparam int unsigned LoopDisable  = 3'b000;
  localparam int unsigned Loop1D       = 3'b001;
  localparam int unsigned Loop2D       = 3'b010;
  localparam int unsigned Loop3D       = 3'b011;
  localparam int unsigned Loop4D       = 3'b100;

  //---------------------------
  // Logic and wires
  //---------------------------
  logic [InstLoopCountWidth-1:0] loop1_count, loop2_count, loop3_count, loop4_count;

  logic loop1_hit_end_addr, loop2_hit_end_addr, loop3_hit_end_addr, loop4_hit_end_addr;
  logic loop1_bound_end, loop2_bound_end, loop3_bound_end, loop4_bound_end;

  //---------------------------
  // Assignments
  //---------------------------
  assign loop1_hit_end_addr = (inst_pc_i == inst_loop_end_addr1_i);
  assign loop2_hit_end_addr = (inst_pc_i == inst_loop_end_addr2_i);
  assign loop3_hit_end_addr = (inst_pc_i == inst_loop_end_addr3_i);
  assign loop4_hit_end_addr = (inst_pc_i == inst_loop_end_addr4_i);

  assign loop1_bound_end =  (loop1_count == (inst_loop_count_addr1_i-1));
  assign loop2_bound_end =  (loop2_count == (inst_loop_count_addr2_i-1));
  assign loop3_bound_end =  (loop3_count == (inst_loop_count_addr3_i-1));
  assign loop4_bound_end =  (loop4_count == (inst_loop_count_addr4_i-1));

  //---------------------------
  // Main counters
  //
  // Each counter increments if it hits an end address
  // otherwise it stays but also resets when it hits an
  // address and when it hits a loop count bound
  //---------------------------
  always_ff @ (posedge clk_i or negedge rst_ni) begin

    if (!rst_ni) begin

      loop1_count <= {InstMemAddrWidth{1'b0}};
      loop2_count <= {InstMemAddrWidth{1'b0}};
      loop3_count <= {InstMemAddrWidth{1'b0}};
      loop4_count <= {InstMemAddrWidth{1'b0}};

    end else begin

      if (clr_i) begin

        loop1_count <= {InstMemAddrWidth{1'b0}};
        loop2_count <= {InstMemAddrWidth{1'b0}};
        loop3_count <= {InstMemAddrWidth{1'b0}};
        loop4_count <= {InstMemAddrWidth{1'b0}};

      end else if (en_i && !stall_i && !dbg_en_i) begin

        // Loop 1D is always present in 1D, 2D, and 3D modes
        if (inst_loop_mode_i != LoopDisable) begin
          if (loop1_hit_end_addr && loop1_bound_end) begin
            loop1_count <= {InstMemAddrWidth{1'b0}};
          end else if (loop1_hit_end_addr) begin
            loop1_count <= loop1_count + 1;
          end else begin
            loop1_count <= loop1_count;
          end
        end else begin
          loop1_count <= {InstMemAddrWidth{1'b0}};
        end

        // Loop 2D is only present in 2D and 3D modes
        if (inst_loop_mode_i == Loop2D ||
            inst_loop_mode_i == Loop3D ||
            inst_loop_mode_i == Loop4D ) begin
          if (loop2_hit_end_addr && loop2_bound_end) begin
            loop2_count <= {InstMemAddrWidth{1'b0}};
          end else if (loop2_hit_end_addr) begin
            loop2_count <= loop2_count + 1;
          end else begin
            loop2_count <= loop2_count;
          end
        end else begin
          loop2_count <= {InstMemAddrWidth{1'b0}};
        end

        // Loop 3D is only present in 3D mode
        if (inst_loop_mode_i == Loop3D || inst_loop_mode_i == Loop4D) begin
          if (loop3_hit_end_addr && loop3_bound_end) begin
            loop3_count <= {InstMemAddrWidth{1'b0}};
          end else if (loop3_hit_end_addr) begin
            loop3_count <= loop3_count + 1;
          end else begin
            loop3_count <= loop3_count;
          end
        end else begin
          loop3_count <= {InstMemAddrWidth{1'b0}};
        end

        // Loop 4D is only present in 4D mode
        if (inst_loop_mode_i == Loop4D) begin
          if (loop4_hit_end_addr && loop4_bound_end) begin
            loop4_count <= {InstMemAddrWidth{1'b0}};
          end else if (loop4_hit_end_addr) begin
            loop4_count <= loop4_count + 1;
          end else begin
            loop4_count <= loop4_count;
          end
        end else begin
          loop4_count <= {InstMemAddrWidth{1'b0}};
        end

      end else begin

        loop1_count <= loop1_count;
        loop2_count <= loop2_count;
        loop3_count <= loop3_count;
        loop4_count <= loop4_count;

      end
    end
  end

  //---------------------------
  // Output assignment
  //---------------------------

  // This handles when the output loop is completed
  always_comb begin
      case(inst_loop_mode_i)
        default: begin
          inst_loop_done_o = 1'b0;
          inst_jump_o      = 1'b0;
          inst_jump_addr_o = {InstMemAddrWidth{1'b0}};
        end
        Loop1D: begin
          inst_jump_o      = loop1_hit_end_addr && !loop1_bound_end;
          inst_jump_addr_o = inst_loop_jump_addr1_i;
          inst_loop_done_o = loop1_bound_end && loop1_hit_end_addr;
        end

        Loop2D: begin
          inst_jump_o      = (loop1_hit_end_addr && !loop1_bound_end) ||
                             (loop2_hit_end_addr && !loop2_bound_end);

          if (loop1_hit_end_addr && !loop1_bound_end) begin
            inst_jump_addr_o = inst_loop_jump_addr1_i;
          end else if (loop2_hit_end_addr && !loop2_bound_end) begin
            inst_jump_addr_o = inst_loop_jump_addr2_i;
          end else begin
            inst_jump_addr_o = {InstMemAddrWidth{1'b0}};
          end

          inst_loop_done_o = loop2_bound_end && loop2_hit_end_addr;
        end
        Loop3D: begin
          inst_jump_o      = (loop1_hit_end_addr && !loop1_bound_end) ||
                             (loop2_hit_end_addr && !loop2_bound_end) ||
                             (loop3_hit_end_addr && !loop3_bound_end);

          if (loop1_hit_end_addr && !loop1_bound_end) begin
            inst_jump_addr_o = inst_loop_jump_addr1_i;
          end else if (loop2_hit_end_addr && !loop2_bound_end) begin
            inst_jump_addr_o = inst_loop_jump_addr2_i;
          end else if (loop3_hit_end_addr && !loop3_bound_end) begin
            inst_jump_addr_o = inst_loop_jump_addr3_i;
          end else begin
            inst_jump_addr_o = {InstMemAddrWidth{1'b0}};
          end

          inst_loop_done_o = loop3_bound_end && loop3_hit_end_addr;
        end
        Loop4D: begin
          inst_jump_o      = (loop1_hit_end_addr && !loop1_bound_end) ||
                             (loop2_hit_end_addr && !loop2_bound_end) ||
                             (loop3_hit_end_addr && !loop3_bound_end) ||
                             (loop4_hit_end_addr && !loop4_bound_end);

          if (loop1_hit_end_addr && !loop1_bound_end) begin
            inst_jump_addr_o = inst_loop_jump_addr1_i;
          end else if (loop2_hit_end_addr && !loop2_bound_end) begin
            inst_jump_addr_o = inst_loop_jump_addr2_i;
          end else if (loop3_hit_end_addr && !loop3_bound_end) begin
            inst_jump_addr_o = inst_loop_jump_addr3_i;
          end else if (loop4_hit_end_addr && !loop4_bound_end) begin
            inst_jump_addr_o = inst_loop_jump_addr4_i;
          end else begin
            inst_jump_addr_o = {InstMemAddrWidth{1'b0}};
          end

          inst_loop_done_o = loop4_bound_end && loop4_hit_end_addr;
        end
      endcase
  end



endmodule
