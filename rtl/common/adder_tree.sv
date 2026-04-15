//-------------------------
// Copyright 2024 KU Leuven
// Ryan Antonio <ryan.antonio@esat.kuleuven.be>
//
// Module: Adder Tree
//
// Description:
// This module implements an adder tree that sums a variable number of input values.
// It is a flexible one where the number of inputs is reconfigurable.
//
// Parameters:
// - NumInputs:    Number of input values to be summed
// - InDataWidth:  Bit width of each input value
// - OutDataWidth: Bit width of the output sum (calculated as InDataWidth + log2(NumInputs))
//                 Adding NumInput values can grow up to log2(NumInputs) bits in the worst case
//                 So we allocate extra bits to prevent overflow
//                 Example: if DataWidth=8 and NumInputs=16, then OutDataWidth=8 + 4 = 12
//                 bits to accommodate sums up to 2040 (255*8)
// - PaddingTwo:   Next power of two greater than or equal to NumInputs (used for tree structure)
//                 This pads power of two. If NumInputs is already a power of two, then PaddingTwo = NumInputs
//                 Else, if NumInputs=6, then PaddingTwo=8.
//                 This allows us to build a complete binary tree structure for the adder tree
// - NumStages:    Number of stages in the adder tree
//                 Calculated as log2(PaddingTwo) since we are building a binary tree
//                 For example, if PaddingTwo=8, then NumStages=3 (since 2^3=8)
// Inputs and Outputs:
// - data_i:       Array of input values to be summed (NumInputs elements, each InDataWidth bits wide)
// - adder_tree_data_o: Output of the adder tree (OutDataWidth bits wide)
//-------------------------

module adder_tree #(
  parameter int unsigned NumInputs    = 8,
  parameter int unsigned InDataWidth  = 8,
  // Don't touch parameters
  parameter int unsigned OutDataWidth = InDataWidth + $clog2(NumInputs),
  // next power of two (>= NumInputs)
  parameter int unsigned PaddingTwo   = 1 << $clog2(NumInputs),
  parameter int unsigned NumStages    = $clog2(PaddingTwo)
)(
  input  logic signed [ InDataWidth-1:0] data_i [NumInputs],
  output logic signed [OutDataWidth-1:0] adder_tree_data_o
);

  // +1 for input stage, [NumStages+1][PaddingTwo] to hold all stages of the tree
  /* verilator lint_off UNOPTFLAT */
  logic signed [OutDataWidth-1:0] adder_stages [NumStages+1][PaddingTwo];
  /* verilator lint_on UNOPTFLAT */

  genvar i, s, k;

  // Initial stages first
  for (i = 0; i < PaddingTwo; i++) begin : gen_input_stage
    if (i < NumInputs) begin: gen_input_assign
      // This one does sign extension
      assign adder_stages[0][i] =
        {{(OutDataWidth-InDataWidth){data_i[i][InDataWidth-1]}}, data_i[i]};
    end else begin: gen_input_pad
      // This one pads extra inputs with zeros
      assign adder_stages[0][i] = '0;
    end
  end

  // Reduction stages by pairs
  // Outer loop of stages
  for (s = 0; s < NumStages; s++) begin : gen_stage
    // Number of adders per stage
    // Note that each stage s, the number of valid nodes are PaddingTwo >> s,
    // but we only need to generate adders for half of them since each adder takes 2 inputs
    // Then next stage, it is halved again, so we can express the number of adders as PaddingTwo >> (s+1)
    for (k = 0; k < (PaddingTwo >> (s+1)); k++) begin : gen_adders
      // Example iteration would be:
      // adder_stages[1][0] = adder_stages[0][0] + adder_stages[0][1];
      // adder_stages[1][1] = adder_stages[0][2] + adder_stages[0][3];
      // adder_stages[1][2] = adder_stages[0][4] + adder_stages[0][5];
      // adder_stages[1][3] = adder_stages[0][6] + adder_stages[0][7];
      // Then the next stage would be:
      // adder_stages[2][0] = adder_stages[1][0] + adder_stages[1][1];
      // adder_stages[2][1] = adder_stages[1][2] + adder_stages[1][3];
      // Then the final stage would be:
      // adder_stages[3][0] = adder_stages[2][0] + adder_stages[2][1];
      assign adder_stages[s+1][k] = adder_stages[s][2*k] + adder_stages[s][2*k+1];
    end

    // Note, all other components are not used so they can be 'x or as '0
    // But we leave them unassigned as synthesis will optimize them away
  end

  // Final adder stage is the output
  assign adder_tree_data_o = adder_stages[NumStages][0];

endmodule
