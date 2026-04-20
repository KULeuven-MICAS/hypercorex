//---------------------------
// Copyright 2024 KU Leuven
// Ryan Antonio <ryan.antonio@esat.kuleuven.be>
//
// Module: vsax_id_level_top
// Description:
// Top-level wrapper for the ID-level encoder and the query hypervector register.
//
//---------------------------


module vsax_id_level_top #(
  // General parameters
  parameter int unsigned HVDimension        = 512,
  // Item memory specific
  parameter int unsigned SeedIm             = 32'hDEAD_BEEF,
  parameter int unsigned ParallelInputsIm   = 2,
  parameter int unsigned NumTotIm           = 1024,
  // Encoder specific
  parameter int unsigned ParallelInputsEnc  = ParallelInputsIm/2,
  parameter int unsigned CounterWidthEnc    = 8,
  // Assoc memory specific
  parameter int unsigned NumClassAm         = 32,
  parameter int unsigned DataWidthAm        = 8,
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
  input  logic [       AddrWidthAm-1:0] am_num_class_i,
  output logic [       DataWidthAm-1:0] predict_o,
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
    .DataWidth              ( DataWidthAm            ),
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
