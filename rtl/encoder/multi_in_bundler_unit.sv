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
  parameter int unsigned NumInputs = 4
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
  localparam int unsigned OutAdderTreeDataWidth = SmallDataWidth + $clog2(NumInputs);

  //---------------------------
  // Wires and registers
  //---------------------------
  logic signed [SmallDataWidth-1:0] bit_increment   [NumInputs];
  logic signed [SmallDataWidth-1:0] valid_increment [NumInputs];

  logic signed [OutAdderTreeDataWidth-1:0] adder_tree;
  // Counter intermediate value before saturation logic is applied
  // Therefore we need extra overflow bit
  logic signed [CounterWidth:0] counter_intermediate;

  logic signed [CounterWidth-1:0] max_val;
  logic signed [CounterWidth-1:0] min_val;

  logic any_valid;

  logic signed [CounterWidth-1:0] counter_next;

  //---------------------------
  // Combinational logic
  //---------------------------
  // Muxing for selecting appropriate increment/decrement value
  always_comb begin
    for (int i = 0; i < NumInputs; i++) begin
      bit_increment[i] = bit_i[i] ? -1 : +1;
    end

    for (int i = 0; i < NumInputs; i++) begin
      valid_increment[i] = valid_i[i] ? bit_increment[i] : 0;
    end
  end

  // Adder tree instance
  adder_tree #(
    .NumInputs          ( NumInputs       ),
    .InDataWidth        ( SmallDataWidth  )
  ) i_adder_tree (
    .data_i             ( valid_increment ),
    .adder_tree_data_o  ( adder_tree      )
  );

  // Counter intermediate value is the current counter plus the adder tree output
  assign counter_intermediate = counter_o + adder_tree;

  // Maximum positive value for signed counter
  assign max_val = {1'b0, {(CounterWidth-1){1'b1}}};
  // Minimum negative value for signed counter
  assign min_val = {1'b1, {(CounterWidth-1){1'b0}}};

  // Check if any input is valid
  assign any_valid = |valid_i;

  // Check for saturation conditions
  // This is technically a decoder/mux only
  always_comb begin
    if (clr_i) begin
      counter_next = 0;
    end else if (any_valid) begin
      if (counter_intermediate > max_val) begin
        counter_next = max_val;
      end else if (counter_intermediate < min_val) begin
        counter_next = min_val;
      end else begin
        // Take the valid bits, ignoring the overflow bit
        counter_next = counter_intermediate[CounterWidth-1:0];
      end
    end else begin
      // No valid inputs, keep the counter unchanged
      counter_next = counter_o;
    end
  end

  //---------------------------
  // Main counter register
  //---------------------------
  always_ff @ (posedge clk_i or negedge rst_ni) begin
    if(!rst_ni) begin
      counter_o <= {CounterWidth{1'b0}};
    end else begin
      counter_o <= counter_next;
    end
  end

endmodule
