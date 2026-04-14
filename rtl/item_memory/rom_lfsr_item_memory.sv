// ===============================================================================
// Copyright 2024 KU Leuven
// Ryan Antonio <ryan.antonio@esat.kuleuven.be>
//
// Module:
//    ROM Item Memory
// Description:
//    Generates all item memory hypervectors entirely within
//    SystemVerilog using a Galois LFSR.
//
// Parameters:
//    HVDimension: dimensionality of the hypervectors (default 512)
//    NumTotIm: total number of items in the memory (default 1024)
//    Seed: base seed for the LFSR (default 32'hDEAD_BEEF)
//    NumPorts: number of parallel read ports (default 2)
//    ImSelWidth: width of the item select input (derived from NumTotIm)
// IO ports:
//    im_sel_i: item select input (NumPorts x ImSelWidth)
//    im_rdata_o: item memory read data output (NumPorts x HVDimension)
// ===============================================================================

module rom_lfsr_item_memory #(
  parameter  int unsigned HVDimension = 512,
  parameter  int unsigned NumTotIm    = 1024,
  parameter  logic [31:0] Seed        = 32'hDEAD_BEEF,
  parameter  int unsigned NumPorts    = 2,
  // Don't touch
  parameter  int unsigned ImSelWidth  = $clog2(NumTotIm)
)(
  // Inputs
  input  logic [ ImSelWidth-1:0]  im_sel_i   [NumPorts],
  // Outputs
  output logic [HVDimension-1:0] im_rdata_o [NumPorts]
);

  // ===============================================================================
  // 32-bit Galois LFSR primitives
  // Taps: x^32 + x^31 + x^29 + x + 1  (maximal-length)
  // ===============================================================================

  // Advance the LFSR by one step
  function automatic logic [31:0] lfsr_next(input logic [31:0] state);
    logic feedback;
    feedback  = state[0];
    lfsr_next = {1'b0, state[31:1]};          // shift right
    if (feedback)
      lfsr_next ^= 32'hB4BC_D35C;             // apply taps
  endfunction

  // Mix an index into the base seed so every item
  // starts from a unique, well-dispersed LFSR state.
  // Uses a Knuth multiplicative hash step.
  function automatic logic [31:0] item_seed(
    input logic [31:0] base_seed,
    input int unsigned idx
  );
    item_seed = base_seed ^ (32'(idx) * 32'h9E37_79B9);
    // Warm up the LFSR so the seed bits are well mixed
    for (int k = 0; k < 32; k++)
      item_seed = lfsr_next(item_seed);
  endfunction

  // Generate one full HVDimension-wide hypervector
  // by clocking the LFSR HVDimension times and taking LSB
  function automatic logic [HVDimension-1:0] gen_hv(
    input logic [31:0] base_seed,
    input int unsigned idx
  );
    logic [31:0] state;
    state = item_seed(base_seed, idx);
    for (int i = 0; i < HVDimension; i++) begin
      gen_hv[i] = state[0];
      state     = lfsr_next(state);
    end
  endfunction

  //---------------------------
  // Item memory array
  // All RHS expressions are compile-time constants, so
  // synthesis infers a true ROM and evaluates gen_hv()
  // during elaboration — identical to a hand-coded table.
  //---------------------------

  logic [HVDimension-1:0] item_memory [NumTotIm];

  generate
    for (genvar i = 0; i < NumTotIm; i++) begin : gen_item_mem
      assign item_memory[i] = gen_hv(Seed, unsigned'(i));
    end
  endgenerate

  //---------------------------
  // Read output ports
  //---------------------------
  always_comb begin
    for (int i = 0; i < NumPorts; i++) begin
      im_rdata_o[i] = item_memory[im_sel_i[i]];
    end
  end

endmodule
