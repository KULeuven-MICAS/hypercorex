//---------------------------
// Copyright 2024 KU Leuven
// Ryan Antonio <ryan.antonio@esat.kuleuven.be>
//
// Module: Testbench Read Memory
// Description:
// This module is used to simulate a
// continuous memory module
//
// Externally we can read and write
// to the memory but the ports connected
// to the core are read only
//
// The access to the accelerator is auto
// incremented every time
//---------------------------

module tb_rd_memory # (
  parameter int unsigned DataWidth = 32,
  parameter int unsigned AddrWidth = 32,
  parameter int unsigned MemDepth  = 1024
)(
  // Clock and reset
  input  logic                    clk_i,
  input  logic                    rst_ni,
  // Enable signal
  input  logic                    en_i,
  // Write port
  input  logic [AddrWidth-1:0]    wr_addr_i,
  input  logic [DataWidth-1:0]    wr_data_i,
  input  logic                    wr_en_i,
  // Read port
  input  logic [AddrWidth-1:0]    rd_addr_i,
  output logic [DataWidth-1:0]    rd_data_o,
  // Automatic loop mode
  input  logic [AddrWidth-1:0]    auto_loop_addr_i,
  input  logic                    auto_loop_en_i,
  // Accelerator access port
  output logic [AddrWidth-1:0]    rd_acc_addr_o,
  output logic [DataWidth-1:0]    rd_acc_data_o,
  output logic                    rd_acc_valid_o,
  input  logic                    rd_acc_ready_i
);

  //---------------------------
  // Wires and logic
  //---------------------------
  logic [MemDepth-1:0][DataWidth-1:0] mem;

  //---------------------------
  // Memory update
  //---------------------------
  always_ff @(posedge clk_i or negedge rst_ni) begin
    if (!rst_ni) begin
      for (int i=0; i<MemDepth; i++) begin
        mem[i] <= 0;
      end
    end else begin
      if (wr_en_i) begin
        mem[wr_addr_i] <= wr_data_i;
      end
    end
  end

  //---------------------------
  // Memory read
  //---------------------------
  assign rd_data_o = mem[rd_addr_i];

  //---------------------------
  // Accelerator access
  //---------------------------
  logic [AddrWidth-1:0] acc_addr;
  logic acc_success;

  assign acc_success = rd_acc_valid_o && rd_acc_ready_i ;

  logic auto_loop_end;

  assign auto_loop_end = auto_loop_addr_i == acc_addr - 1;

  //---------------------------
  // Automated address counter
  //---------------------------
  always_ff @(posedge clk_i or negedge rst_ni) begin
    if (!rst_ni) begin
      acc_addr <= 0;
    end else begin
      if (en_i) begin
        // If auto loop is enabled and the end address is reached
        // reset the counter to 0 else increment the counter
        if (auto_loop_end && auto_loop_en_i) begin
          acc_addr <= '0;
        // Update counter for every successful transaction
        end else if (acc_success) begin
            acc_addr <= acc_addr + 1;
        end else begin
          acc_addr <= acc_addr;
        end
      end else begin
        acc_addr <= 0;
      end
    end
  end

  // Output data will always be valid
  // in this synthetic memory read module
  // since contentions will never happend
  always_comb begin

    if (en_i) begin
      rd_acc_valid_o = 1;
    end else begin
      rd_acc_valid_o = 0;
    end

    rd_acc_data_o = mem[acc_addr];

  end

  //---------------------------
  // Output assignments
  //---------------------------
  assign rd_acc_addr_o   = acc_addr;

endmodule
