//---------------------------
// Copyright 2024 KU Leuven
// Ryan Antonio <ryan.antonio@esat.kuleuven.be>
//
// Module: Testbench Write Memory
// Description:
// This module is used to simulate a
// continuous memory module
//
// It is being continuously written to
// and external control simply reads from it
//
// There is capability to overwrite the memory
// address to which the data is written to
//---------------------------

module tb_wr_memory # (
  parameter int unsigned DataWidth = 32,
  parameter int unsigned AddrWidth = 32,
  parameter int unsigned MemDepth  = 1024
)(
  // Clock and reset
  input  logic                    clk_i,
  input  logic                    rst_ni,
  // Enable signal
  input  logic                    en_i,
  // Read port
  input  logic [AddrWidth-1:0]    rd_addr_i,
  output logic [DataWidth-1:0]    rd_data_o,
  // Force address to be written
  input  logic [AddrWidth-1:0]    set_wr_addr_i,
  input  logic                    set_wr_en_i,
  // Accelerator access port
  output logic [AddrWidth-1:0]    wr_acc_addr_o,
  input  logic [DataWidth-1:0]    wr_acc_data_i,
  input  logic                    wr_acc_valid_i,
  output logic                    wr_acc_ready_o
);

  //---------------------------
  // Wires and logic
  //---------------------------
  logic [MemDepth-1:0][DataWidth-1:0] mem;

  logic wr_acc_success;

  assign wr_acc_success = wr_acc_valid_i & wr_acc_ready_o;

  //---------------------------
  // Automatic address counter
  //---------------------------
  always_ff @(posedge clk_i or negedge rst_ni) begin
    if (!rst_ni) begin
      wr_acc_addr_o <= '0;
    end else begin
      if (set_wr_en_i) begin
            wr_acc_addr_o <= set_wr_addr_i;
      end else if(en_i) begin
        if (wr_acc_success) begin
          wr_acc_addr_o <= wr_acc_addr_o + 1;
        end else begin
          wr_acc_addr_o <= wr_acc_addr_o;
        end
      end else begin
        wr_acc_addr_o <= wr_acc_addr_o;
      end
    end
  end

  //---------------------------
  // Memory update
  //---------------------------
  always_ff @(posedge clk_i or negedge rst_ni) begin
    if (!rst_ni) begin
      for (int i=0; i<MemDepth; i++) begin
        mem[i] <= 0;
      end
    end else begin
      if (en_i) begin
        if (wr_acc_success) begin
          mem[wr_acc_addr_o] <= wr_acc_data_i;
        end
      end
    end
  end

  //---------------------------
  // Memory read
  //---------------------------
  assign rd_data_o = mem[rd_addr_i];

  //---------------------------
  // Accelerator ready port
  //---------------------------
  assign wr_acc_ready_o = en_i;

endmodule
