//---------------------------
// Copyright 2024 KU Leuven
// Ryan Antonio <ryan.antonio@esat.kuleuven.be>
//
// Module: Bundler Unit
// Description:
// Bi-directional bundler unit
// made per-bit position but with
// saturating counters
//---------------------------

module bundler_unit #(
  parameter int unsigned CounterWidth = 8
)(
  input  logic clk_i,
  input  logic rst_ni,
  input  logic bit_i,
  input  logic valid_i,
  input  logic clr_i,
  output logic signed [CounterWidth-1:0] counter_o
);

  //---------------------------
  // Wires
  //---------------------------
  logic saturate_low;
  logic saturate_high;

  //---------------------------
  // Combinational Logic
  //---------------------------

  // Saturate low happens when counter == 10000...000
  assign saturate_low  = (counter_o == {1'b1,{(CounterWidth-1){1'b0}}}) ? 1'b1: 1'b0;

  // Saturate high happens when counter == 01111...111
  assign saturate_high = (counter_o == {1'b0,{(CounterWidth-1){1'b1}}}) ? 1'b1: 1'b0;

  always_ff @ (posedge clk_i or negedge rst_ni) begin
    // This is for asynchronous reset
    if(!rst_ni) begin
      counter_o <= {CounterWidth{1'b0}};
    end else begin

      // This is for synchronous reset
      if(clr_i) begin

        counter_o <= {CounterWidth{1'b0}};

      // This is for accumulating values
      end else if (valid_i) begin

        // If the bit is one we increment
        // but we need to saturate at max positive value
        if (bit_i) begin
          if (saturate_high) begin
            counter_o <= counter_o;
          end else begin
            counter_o <= counter_o + 1;
          end

        // If the bit is 0, we decrement
        // but we need to saturate at max negative
        end else begin
          if (saturate_low) begin
            counter_o <= counter_o;
          end else begin
            counter_o <= counter_o - 1;
          end
        end

      // Default is to maintain the values
      end else begin
        counter_o <= counter_o;
      end

    end
  end

endmodule
