//---------------------------
// Copyright 2024 KU Leuven
// Ryan Antonio <ryan.antonio@esat.kuleuven.be>
//
// Module: Multi-In Bundler Unit
// Description:
// A multi-input bi-directional bundler unit made with saturating counters.
//
// Parameters:
// - CounterWidth: Bit width of the internal counter (and output)
// - NumInputs:   Number of input bits to be bundled (each can contribute +1 or -1 to the counter)
//
// Inputs and Outputs:
// - clk_i:       Clock input for the counter register
// - rst_ni:      Active-low reset for the counter register
// - clr_i:       Synchronous clear for the counter (resets to zero on next clock edge)
// - bit_i:       Array of input bits (NumInputs elements) that contribute to the counter
// - valid_i:     Array of valid signals (NumInputs elements) indicating which input bits are valid for this cycle
// - counter_o:   Output of the counter (CounterWidth bits wide), which is the bundled result of the input bits
//---------------------------

module multi_in_bundler_unit #(
  parameter int unsigned CounterWidth = 8,
  parameter int unsigned NumInputs = 4,
)(
  input  logic                           clk_i,
  input  logic                           rst_ni,
  input  logic                           clr_i,
  input  logic        [   NumInputs-1:0] bit_i,
  input  logic        [   NumInputs-1:0] valid_i,
  output logic signed [CounterWidth-1:0] counter_o
);

  //---------------------------
  // Internal Parameters
  //---------------------------
  localparam int unsigned SmallDataWidth = 2;

  //---------------------------
  // Wires
  //---------------------------
  logic saturate_low;
  logic saturate_high;
  logic signed [CounterWidth-1:0] counter_next;
  logic signed [CounterWidth-1:0] counter_sum;

  

  logic signed [CounterWidth-1:0] max_val;
  logic signed [CounterWidth-1:0] min_val;

  // Maximum positive value for signed counter
  assign max_val = {1'b0, {(CounterWidth-1){1'b1}}}; 
  // Minimum negative value for signed counter
  assign min_val = {1'b1, {(CounterWidth-1){1'b0}}}; 

  //---------------------------
  // Combinational Logic
  //---------------------------

  // Saturate low happens when counter == 10000...000
  assign saturate_low  = (counter_o == {1'b1,{(CounterWidth-1){1'b0}}}) ? 1'b1: 1'b0;

  // Saturate high happens when counter == 01111...111
  assign saturate_high = (counter_o == {1'b0,{(CounterWidth-1){1'b1}}}) ? 1'b1: 1'b0;

  // Counter next state logic
  always_comb begin
    // Default: counter_next comes from counter_o
    counter_next = counter_o;
    counter_sum  = counter_o;

    // Accumulate contributions from each input with per-step saturation.
    // Saturation is checked against counter_sum (not counter_o) so that
    // clamping stays correct across multiple iterations of the loop.
    for (int i = 0; i < NumInputs; i++) begin
      if (valid_i[i]) begin
        if (bit_i[i]) begin
          // +1: clamp at high saturation bound
          counter_sum = (counter_sum == $signed({1'b0, {(CounterWidth-1){1'b1}}})) ?
                        counter_sum : counter_sum + 1;
        end else begin
          // -1: clamp at low saturation bound
          counter_sum = (counter_sum == $signed({1'b1, {(CounterWidth-1){1'b0}}})) ?
                        counter_sum : counter_sum - 1;
        end
      end
    end

    // Update counter_next if any valid input is high
    if (|valid_i) begin
      counter_next = counter_sum;
    end
  end

  // Main counter register
  always_ff @ (posedge clk_i or negedge rst_ni) begin
    if(!rst_ni) begin
      counter_o <= {CounterWidth{1'b0}};
    end else begin
      counter_o <= counter_next;
    end
  end

endmodule
