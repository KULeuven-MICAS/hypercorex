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
  parameter int unsigned InstLoopCountWidth = 10,
  parameter int unsigned LoopNumStates = 4,
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
  input  logic [InstMemAddrWidth-1:0]  inst_loop_jump_addr1_i,
  input  logic [InstMemAddrWidth-1:0]  inst_loop_jump_addr2_i,
  input  logic [InstMemAddrWidth-1:0]  inst_loop_jump_addr3_i,
  input  logic [InstMemAddrWidth-1:0]  inst_loop_end_addr1_i,
  input  logic [InstMemAddrWidth-1:0]  inst_loop_end_addr2_i,
  input  logic [InstMemAddrWidth-1:0]  inst_loop_end_addr3_i,
  input  logic [InstLoopCountWidth-1:0]  inst_loop_count_addr1_i,
  input  logic [InstLoopCountWidth-1:0]  inst_loop_count_addr2_i,
  input  logic [InstLoopCountWidth-1:0]  inst_loop_count_addr3_i,
  // Loop control signals
  output logic                         inst_jump_o,
  output logic [InstMemAddrWidth-1:0]  inst_jump_addr_o,
  // Status signal
  output logic                         inst_loop_done_o
);

  //---------------------------
  // Local parameters
  //---------------------------
  localparam int unsigned LOOP_DISABLE = 2'b00;
  localparam int unsigned LOOP_1D      = 2'b01;
  localparam int unsigned LOOP_2D      = 2'b10;
  localparam int unsigned LOOP_3D      = 2'b11;

  //---------------------------
  // Logic and wires
  //---------------------------
  logic [InstLoopCountWidth-1:0] loop1_count, loop2_count, loop3_count;

  logic loop1_hit_end_addr, loop2_hit_end_addr, loop3_hit_end_addr;
  logic loop1_bound_end, loop2_bound_end, loop3_bound_end;

  //---------------------------
  // Assignments
  //---------------------------
  assign loop1_hit_end_addr = (inst_pc_i == inst_loop_end_addr1_i);
  assign loop2_hit_end_addr = (inst_pc_i == inst_loop_end_addr2_i);
  assign loop3_hit_end_addr = (inst_pc_i == inst_loop_end_addr3_i);

  assign loop1_bound_end =  (loop1_count == (inst_loop_count_addr1_i-1));
  assign loop2_bound_end =  (loop2_count == (inst_loop_count_addr2_i-1));
  assign loop3_bound_end =  (loop3_count == (inst_loop_count_addr3_i-1));

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

    end else begin

      if (clr_i) begin

        loop1_count <= {InstMemAddrWidth{1'b0}};
        loop2_count <= {InstMemAddrWidth{1'b0}};
        loop3_count <= {InstMemAddrWidth{1'b0}};

      end else if (en_i && !stall_i && !dbg_en_i) begin

        // Loop 1D is always present in 1D, 2D, and 3D modes
        if (inst_loop_mode_i != LOOP_DISABLE) begin
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
        if (inst_loop_mode_i == LOOP_2D || inst_loop_mode_i == LOOP_3D) begin
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
        if (inst_loop_mode_i == LOOP_3D) begin
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

      end else begin

        loop1_count <= loop1_count;
        loop2_count <= loop2_count;
        loop3_count <= loop3_count;

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
        LOOP_1D: begin
          inst_jump_o      = loop1_hit_end_addr && !loop1_bound_end;
          inst_jump_addr_o = inst_loop_jump_addr1_i;
          inst_loop_done_o = loop1_bound_end && loop1_hit_end_addr;
        end

        LOOP_2D: begin
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
        LOOP_3D: begin
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
      endcase
  end



endmodule
