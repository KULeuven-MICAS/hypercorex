//---------------------------
// Copyright 2024 KU Leuven
// Ryan Antonio <ryan.antonio@esat.kuleuven.be>
//
// Module: tb_vsax_id_level_top
// Description:
// Testbench for the vsax_id_level_top module. This testbench is designed to
// verify the functionality of the vsax_id_level_top module by applying a series
// of test vectors and checking the outputs against expected results.
//---------------------------

`define TCLK 1

module tb_vsax_id_level_top #(
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
);

  // Clocks and reset
  logic                          clk_i;
  logic                          rst_ni;
  // Item-memory iports
  logic [       ImSelWidth-1:0]  im_rd_i [ParallelInputsIm];
  // Encoding ports
  logic [ParallelInputsEnc-1:0]  enc_valid_i;
  logic                          enc_clr_i;
  // Query hypervector register ports
  logic                          qhv_wen_i;
  logic                          qhv_clr_i;
  logic                          qhv_am_load_i;
  // Associative memory ports
  // Write side (latch_memory)
  logic                          w_valid_i;
  logic                          w_ready_o;
  logic                          w_en_i;
  logic [       AddrWidthAm-1:0] w_addr_i;
  logic [       HVDimension-1:0] w_data_i;
  // External read port
  logic                          external_read_sel_i;
  logic                          ext_r_req_valid_i;
  logic                          ext_r_req_ready_o;
  logic [       AddrWidthAm-1:0] ext_r_addr_i;
  logic                          ext_r_resp_valid_o;
  logic                          ext_r_resp_ready_i;
  logic [       HVDimension-1:0] ext_r_resp_data_o;
  // Search control
  logic                          am_start_i;
  logic [       CsrRegWidth-1:0] am_num_class_i;
  logic [       CsrRegWidth-1:0] predict_o;
  logic                          predict_valid_o;
  logic                          predict_ready_i;

  // Instantiate the DUT
  vsax_id_level_top #(
    .HVDimension          ( HVDimension         ),
    .CsrRegWidth          ( CsrRegWidth         ),
    .SeedIm               ( SeedIm              ),
    .ParallelInputsIm     ( ParallelInputsIm    ),
    .NumTotIm             ( NumTotIm            ),
    .ParallelInputsEnc    ( ParallelInputsEnc   ),
    .CounterWidthEnc      ( CounterWidthEnc     ),
    .NumClassAm           ( NumClassAm          )
  ) i_vsax_id_level_top (
    .clk_i                ( clk_i               ),
    .rst_ni               ( rst_ni              ),
    .im_rd_i              ( im_rd_i             ),
    .enc_valid_i          ( enc_valid_i         ),
    .enc_clr_i            ( enc_clr_i           ),
    .qhv_wen_i            ( qhv_wen_i           ),
    .qhv_clr_i            ( qhv_clr_i           ),
    .qhv_am_load_i        ( qhv_am_load_i       ),
    .w_valid_i            ( w_valid_i           ),
    .w_ready_o            ( w_ready_o           ),
    .w_en_i               ( w_en_i              ),
    .w_addr_i             ( w_addr_i            ),
    .w_data_i             ( w_data_i            ),
    .external_read_sel_i  ( external_read_sel_i ),
    .ext_r_req_valid_i    ( ext_r_req_valid_i   ),
    .ext_r_req_ready_o    ( ext_r_req_ready_o   ),
    .ext_r_addr_i         ( ext_r_addr_i        ),
    .ext_r_resp_valid_o   ( ext_r_resp_valid_o  ),
    .ext_r_resp_ready_i   ( ext_r_resp_ready_i  ),
    .ext_r_resp_data_o    ( ext_r_resp_data_o   ),
    .am_start_i           ( am_start_i          ),
    .am_num_class_i       ( am_num_class_i      ),
    .predict_o            ( predict_o           ),
    .predict_valid_o      ( predict_valid_o     ),
    .predict_ready_i      ( predict_ready_i     )
  );

  // Forever clock
  initial begin
    clk_i = 0;
    forever #`TCLK clk_i = ~clk_i;
  end

  initial begin
    // Initialize inputs
    rst_ni              = '0;
    for (int i = 0; i < ParallelInputsIm; i++)
      im_rd_i[i]        = '0;
    enc_valid_i         = '0;
    enc_clr_i           = '0;
    qhv_wen_i           = '0;
    qhv_clr_i           = '0;
    qhv_am_load_i       = '0;
    w_valid_i           = '0;
    w_en_i              = '0;
    w_addr_i            = '0;
    w_data_i            = '0;
    external_read_sel_i = '0;
    ext_r_req_valid_i   = '0;
    ext_r_addr_i        = '0;
    ext_r_resp_ready_i  = '0;
    am_start_i          = '0;
    am_num_class_i      = '0;
    predict_ready_i     = '0;
    @(posedge clk_i);
    rst_ni = '1;
    @(posedge clk_i);

    // Trailing clock cycles
    for(int i=0; i<10; i++) @(posedge clk_i);
    $finish;
  end
endmodule
