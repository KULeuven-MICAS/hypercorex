//---------------------------
// Copyright 2024 KU Leuven
// Ryan Antonio <ryan.antonio@esat.kuleuven.be>
//
// Module: Automatic Address Counter
// Description:
// This is a simple automatic address counter.
// It's a simple address generator used for
// selecting the correct addresses in the item memory.
//
// This only increments every update input.
// Also has simple clear to restart the counter.
//---------------------------

module update_counter #(
  parameter int unsigned CounterWidth = 32
)(
  // Clocks and reset
  input  logic clk_i,
  input  logic rst_ni,
  // Inputs
  input  logic en_i,
  input  logic clr_i,
  input  logic update_i,
  // Outputs
  output logic [CounterWidth-1:0] addr_o
);

  //---------------------------
  // Wires
  //---------------------------
  logic [CounterWidth-1:0] addr_reg;

  //---------------------------
  // Counter
  //---------------------------
  always_ff @(posedge clk_i or negedge rst_ni) begin
    if (~rst_ni) begin
      addr_reg <= {CounterWidth{1'b0}};
    end else begin
      if (en_i) begin
        if(clr_i) begin
          addr_reg <= {CounterWidth{1'b0}};
        end else if(update_i) begin
          addr_reg <= addr_reg + 1;
        end else begin
          addr_reg <= addr_reg;
        end
      end else begin
        addr_reg <= {CounterWidth{1'b0}};
      end
    end
  end

  //---------------------------
  // Output
  //---------------------------
  assign addr_o = addr_reg;

endmodule
