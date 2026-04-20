//---------------------------
// Copyright 2024 KU Leuven
// Ryan Antonio <ryan.antonio@esat.kuleuven.be>
//
// Module: vsax_id_level_top
// Description:
// Top-level wrapper for the ID-level encoder and the query hypervector register.
//
// Parameters:
// - HVDimension:        Dimensionality of the hypervectors used in the system
// - CsrRegWidth:        Bit width of the control and status registers (e.g. for number of classes in the AM)
// - SeedIm:            Seed for the item memory LFSR (linear feedback shift register)
// - ParallelInputsIm:   Number of parallel input ports to the item memory (must be even, as half are for ID and half for level)
// - NumTotIm:           Total number of hypervectors stored in the item memory
// - ParallelInputsEnc:  Number of parallel input ports to the encoder (must be half of ParallelInputsIm, as the encoder takes both ID and level hypervectors)
// - CounterWidthEnc:    Bit width of the internal counter in the encoder (and thus the output of the encoder)
//
// Inputs and Outputs:
// Clocks and reset:
// - clk_i:             Clock input for the entire system
// - rst_ni:            Active-low reset for the entire system
// Item memory ports:
// - im_rd_i:           Array of input addresses to read from the item memory (ParallelInputsIm elements, each of ImSelWidth bits)
// Encoder ports:
// - enc_valid_i:       Array of valid signals for the encoder inputs (ParallelInputsEnc elements)
// - enc_clr_i:         Synchronous clear signal for the encoder (resets the encoder's internal state on the next clock edge)
// Query hypervector register ports:
// - qhv_wen_i:         Write enable for the query hypervector register (when high, the output of the encoder is latched into the QHV register on the next clock edge)
// - qhv_clr_i:         Synchronous clear for the query hypervector register (resets the QHV register on the next clock edge)
// - qhv_am_load_i:     Signal to load the QHV into the associative memory for searching (used to indicate that the QHV is ready for a search)
// Associative memory ports:
// Write side (latch_memory):
// - w_valid_i:         Valid signal for writing to the associative memory (latch_memory)
// - w_ready_o:         Ready signal from the associative memory indicating it can accept a write (latch_memory)
// - w_en_i:            Write enable for the associative memory (latch_memory)
// - w_addr_i:          Address for writing to the associative memory (latch_memory)
// - w_data_i:          Data for writing to the associative memory (latch_memory, should be HVDimension bits wide)
// External read port:
// - external_read_sel_i: Select signal for the external read port of the associative memory (when high, the external read port is active instead of the search port)
// - ext_r_req_valid_i: Valid signal for the external read request to the associative memory
// - ext_r_req_ready_o: Ready signal from the associative memory indicating it can accept an external read request
// - ext_r_addr_i:      Address for the external read request to the associative memory
// - ext_r_resp_valid_o: Valid signal from the associative memory indicating that the external read response is valid
// - ext_r_resp_ready_i: Ready signal from the external reader indicating it can accept the external read response
// - ext_r_resp_data_o: Data from the associative memory in response to the external read request (should be HVDimension bits wide)
// Search control (bin_sim_search):
// - am_start_i:         Signal to start a search in the associative memory (bin_sim_search)
// - am_num_class_i:     Number of classes to consider in the associative memory search (bin_sim_search)
// - predict_o:          Output of the associative memory search, indicating the predicted class
// - predict_valid_o:    Valid signal indicating that the prediction output is valid
// - predict_ready_i:    Ready signal from the consumer of the prediction indicating it can accept
//---------------------------


module vsax_id_level_top #(
  // General parameters
  parameter int unsigned HVDimension        = 512,
  parameter int unsigned CsrRegWidth        = 8,
  // Item memory specific
  parameter int unsigned SeedIm             = 32'hDEAD_BEEF,
  parameter int unsigned ParallelInputsIm   = 2,
  parameter int unsigned NumTotIm           = 1024,
  // Encoder specific
  parameter int unsigned ParallelInputsEnc  = ParallelInputsIm/2,
  parameter int unsigned CounterWidthEnc    = 8,
  // Assoc memory specific
  parameter int unsigned NumClassAm         = 32,
  // Don't touch!
  parameter int unsigned ImSelWidth         = $clog2(NumTotIm),
  parameter int unsigned AddrWidthAm        = $clog2(NumClassAm)
)(
  // Clocks and reset
  input  logic                          clk_i,
  input  logic                          rst_ni,
  // Item-memory iports
  input  logic [       ImSelWidth-1:0]  im_rd_i [ParallelInputsIm],
  // Encoding ports
  input  logic [ParallelInputsEnc-1:0]  enc_valid_i,
  input  logic                          enc_clr_i,
  // Query hypervector register ports
  input  logic                          qhv_wen_i,
  input  logic                          qhv_clr_i,
  input  logic                          qhv_am_load_i,
  // Associative memory ports
  // Write side (latch_memory)
  input  logic                          w_valid_i,
  output logic                          w_ready_o,
  input  logic                          w_en_i,
  input  logic [       AddrWidthAm-1:0] w_addr_i,
  input  logic [HVDimension-1:0]        w_data_i,
  // External read port
  input  logic                          external_read_sel_i,
  input  logic                          ext_r_req_valid_i,
  output logic                          ext_r_req_ready_o,
  input  logic [       AddrWidthAm-1:0] ext_r_addr_i,
  output logic                          ext_r_resp_valid_o,
  input  logic                          ext_r_resp_ready_i,
  output logic [HVDimension-1:0]        ext_r_resp_data_o,
  // Search control (bin_sim_search)
  input  logic                          am_start_i,
  input  logic [       CsrRegWidth-1:0] am_num_class_i,
  output logic [       CsrRegWidth-1:0] predict_o,
  output logic                          predict_valid_o,
  input  logic                          predict_ready_i
);


  //---------------------------
  // Wires and Logic
  //---------------------------
  logic [HVDimension-1:0] im_rdata  [ ParallelInputsIm];
  logic [HVDimension-1:0] hv_id     [ParallelInputsEnc];
  logic [HVDimension-1:0] hv_level  [ParallelInputsEnc];
  logic [HVDimension-1:0] hv_bin_encoded;
  logic [HVDimension-1:0] qhv;
  logic am_busy;


  //---------------------------
  // Projection - Item Memory
  //---------------------------
  rom_lfsr_item_memory #(
    .HVDimension  ( HVDimension       ),
    .NumTotIm     ( NumTotIm          ),
    .Seed         ( SeedIm            ),
    .NumPorts     ( ParallelInputsIm  )
  ) i_rom_lfsr_item_memory (
    .im_sel_i     ( im_rd_i           ),
    .im_rdata_o   ( im_rdata          )
  );

  // Re-mapping of inputs and outputs
  // First-half is for ID hypervectors
  // Second-half is for level hypervectors
  always_comb begin
    for (int i = 0; i < ParallelInputsIm/2; i++) begin
      hv_id[i]    = im_rdata[i];
      hv_level[i] = im_rdata[i + ParallelInputsIm/2];
    end
  end

  //---------------------------
  // Encoding Unit
  //---------------------------
  id_level_encoder #(
    .HVDimension      ( HVDimension       ),
    .NumInputs        ( ParallelInputsEnc ),
    .CounterWidth     ( CounterWidthEnc   )
  ) i_id_level_encoder (
    // Clocks and reset
    .clk_i            ( clk_i             ),
    .rst_ni           ( rst_ni            ),
    // Other input logic
    .clr_i            ( enc_clr_i         ),
    // Inputs
    .valid_i          ( enc_valid_i       ),
    .hv_id_i          ( hv_id             ),
    .hv_level_i       ( hv_level          ),
    // Outputs
    .hv_encoded_o     (                   ), // unused
    .hv_bin_encoded_o ( hv_bin_encoded    )
  );

  //---------------------------
  // Query Hypervector Register
  //---------------------------
  // This functions just like a temporary hold buffer
  qhv #(
    .HVDimension    ( HVDimension    )
  ) i_qhv (
    // Clocks and reset
    .clk_i          ( clk_i          ),
    .rst_ni         ( rst_ni         ),
    // Control ports for query HV
    .qhv_i          ( hv_bin_encoded ),
    .qhv_wen_i      ( qhv_wen_i      ),
    .qhv_clr_i      ( qhv_clr_i      ),
    .qhv_am_load_i  ( qhv_am_load_i  ),
    .am_busy_i      ( am_busy         ),
    .qhv_o          ( qhv            ),
    .qhv_valid_o    (                ), // unused
    .qhv_ready_i    ( 1'b1           ), // always ready
    .qhv_stall_o    (                )  // unused
  );

  //---------------------------
  // Associative Memory Unit
  //---------------------------
  assoc_mem_top #(
    .HVDimension            ( HVDimension            ),
    .NumClass               ( NumClassAm             ),
    .DataWidth              ( CsrRegWidth            )
  ) i_assoc_mem_top (
    // Clocks and reset
    .clk_i                  ( clk_i                  ),
    .rst_ni                 ( rst_ni                 ),
    // Write side (latch_memory)
    .w_valid_i              ( w_valid_i              ),
    .w_ready_o              ( w_ready_o              ),
    .w_en_i                 ( w_en_i                 ),
    .w_addr_i               ( w_addr_i               ),
    .w_data_i               ( w_data_i               ),
    // External read port
    .external_read_sel_i    ( external_read_sel_i    ),
    .ext_r_req_valid_i      ( ext_r_req_valid_i      ),
    .ext_r_req_ready_o      ( ext_r_req_ready_o      ),
    .ext_r_addr_i           ( ext_r_addr_i           ),
    .ext_r_resp_valid_o     ( ext_r_resp_valid_o     ),
    .ext_r_resp_ready_i     ( ext_r_resp_ready_i     ),
    .ext_r_resp_data_o      ( ext_r_resp_data_o      ),
    // Search control (bin_sim_search)
    .query_hv_i             ( qhv                    ),
    .am_start_i             ( am_start_i             ),
    .am_busy_o              ( am_busy                ),
    .am_stall_o             (                        ), // unused
    .am_num_class_i         ( am_num_class_i         ),
    .am_predict_valid_o     (                        ), // unused
    .am_predict_valid_clr_i (                        ), // unused
    .predict_o              ( predict_o              ),
    .predict_valid_o        ( predict_valid_o        ),
    .predict_ready_i        ( predict_ready_i        )
  );

endmodule
