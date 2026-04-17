// ===============================================================================
// Copyright 2024 KU Leuven
// Ryan Antonio <ryan.antonio@esat.kuleuven.be>
//
// Module:
//    Generic memory unit with byte-enable and configurable Latency
// Description:
//    A simple memory module that can be used for various purposes.
//   Supports byte-enable for writes and can be configured to have a read Latency.
// Parameters:
//    NumWords: number of words in the memory (default 256)
//    DataWidth: width of each word in bits (default 32)
//    ByteWidth: number of bytes in each word (default 4 for 32-bit words)
//    Latency: number of cycles for read Latency (default 1)
// IO ports:
//    clk_i: clock input
//    rst_ni: active-low reset input
//    req_i: request signal to trigger read/write operations
//    w_en_i: write enable signal (1 for write, 0 for read)
//    addr_i: address input for read/write operations
//    w_data_i: data input for write operations
//    b_en_i: byte enable input for write operations (1 bit per byte)
//    r_data_o: data output for read operations
// ===============================================================================


module sram_memory #(
  parameter int unsigned NumWords       = 256,
  parameter int unsigned DataWidth      = 32,
  parameter int unsigned ByteWidth      = 8,
  parameter int unsigned Latency        = 1,
  // Don't touch parameters
  parameter int unsigned AddrWidth      = $clog2(NumWords),
  parameter int unsigned AddrByteWidth  = DataWidth / ByteWidth
)(
  // Clock and reset
  input  logic                     clk_i,
  input  logic                     rst_ni,
  // Inputs
  input  logic                     req_i,
  input  logic                     w_en_i,
  input  logic [    AddrWidth-1:0] addr_i,
  input  logic [    DataWidth-1:0] w_data_i,
  input  logic [AddrByteWidth-1:0] b_en_i,
  // Outputs
  output logic [    DataWidth-1:0] r_data_o
);

  //---------------------------
  // Wires and regs
  //---------------------------
  logic [DataWidth-1:0] memory [NumWords];

  //---------------------------
  // Main memory logic
  //---------------------------
  // Writing to memory logic
  always_ff @(posedge clk_i or negedge rst_ni) begin
    if (!rst_ni) begin
      // Reset memory
      for (int i = 0; i < NumWords; i++) begin
        memory[i] <= {DataWidth{1'b0}};
      end
    end else if (req_i) begin
      if (w_en_i) begin
        // Write operation but with byte masking
        for (int i = 0; i < ByteWidth; i++) begin
          if (b_en_i[i]) begin
            memory[addr_i][(i*8)+:8] <= w_data_i[(i*8)+:8];
          end
        end
      end
    end
  end

  // Reading from memory logic
  if(Latency > 0) begin: gen_sram_memory_latency
    // Latency logic
    logic [DataWidth-1:0] r_data_reg;
    always_ff @(posedge clk_i or negedge rst_ni) begin
      if (!rst_ni) begin
        r_data_reg <= {DataWidth{1'b0}};
      end else if (req_i) begin
        r_data_reg <= memory[addr_i];
      end
    end
    assign r_data_o = r_data_reg;
  end else begin: gen_sram_memory_no_latency
    // No Latency logic
    assign r_data_o = memory[addr_i];
  end

endmodule
