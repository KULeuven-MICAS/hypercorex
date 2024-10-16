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
  parameter int unsigned CsrDataWidth = 32
)(
  // Clocks and reset
  input  logic                    clk_i,
  input  logic                    rst_ni,
  // Inputs
  input  logic                    en_i,
  input  logic                    clr_i,
  input  logic                    start_i,
  input  logic [CsrDataWidth-1:0] max_count_i,
  input  logic [CsrDataWidth-1:0] start_count_i,
  // Outputs
  output logic [CsrDataWidth-1:0] addr_o,
  output logic                    addr_valid_o,
  input  logic                    addr_ready_i
);

  //---------------------------
  // Wires
  //---------------------------
  logic [CsrDataWidth-1:0] addr_reg;

  logic max_count_hit;
  logic max_count_success;

  logic addr_success;

  //---------------------------
  // Combinational Logic
  //---------------------------
  assign addr_success = addr_valid_o & addr_ready_i;
  assign max_count_hit = addr_reg == (max_count_i + start_count_i)-1;
  assign max_count_success = max_count_hit & addr_success;

  //---------------------------
  // Counter
  //---------------------------
  always_ff @(posedge clk_i or negedge rst_ni) begin
    if (!rst_ni) begin
      addr_reg <= {CsrDataWidth{1'b0}};
    end else begin
      if (en_i) begin
        if(clr_i || max_count_success || start_i) begin
          addr_reg <= start_count_i;
        end else if(addr_success) begin
          addr_reg <= addr_reg + 1;
        end else begin
          addr_reg <= addr_reg;
        end
      end else begin
        addr_reg <= {CsrDataWidth{1'b0}};
      end
    end
  end

  //---------------------------
  // Output
  //---------------------------
  assign addr_o       = addr_reg;
  assign addr_valid_o = en_i;

endmodule
