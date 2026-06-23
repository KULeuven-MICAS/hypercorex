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

//---------------------------
// Define appropriate clock frequency in here
// MODIFY ME: Tune it to what you wil use for post-synthesis
//---------------------------
`define TCLK 5

//---------------------------
// Main testbench module
//---------------------------
module tb_vsax_id_level_top;

  //---------------------------
  // Parameters
  //---------------------------
  // General parameters
  parameter int unsigned HVDimension        = 512;
  parameter int unsigned CsrRegWidth        = 8;
  // Item memory specific
  parameter int unsigned SeedIm             = 32'd42;
  parameter int unsigned ParallelInputsIm   = 2;
  parameter int unsigned NumTotIm           = 1024;
  // Encoder specific
  parameter int unsigned ParallelInputsEnc  = ParallelInputsIm/2;
  parameter int unsigned CounterWidthEnc    = 8;
  // Assoc memory specific
  parameter int unsigned NumClassAm         = 10;
  // Don't touch!
  parameter int unsigned ImSelWidth         = $clog2(NumTotIm);
  parameter int unsigned AddrWidthAm        = $clog2(NumClassAm);

  // Input data parameter
  parameter int unsigned ImageWidth         = 28;
  parameter int unsigned ImageHeight        = 28;
  parameter int unsigned NumPixels          = ImageWidth * ImageHeight;
  parameter int unsigned NumInputItems      = 10;

  //---------------------------
  // Signal declarations
  //---------------------------
  // Clocks and reset
  logic                          clk_i;
  logic                          rst_ni;
  // Item-memory iports
  logic [ParallelInputsIm-1:0][       ImSelWidth-1:0]  im_rd_i;
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

  // Internal state enabler
  logic internal_state;

  //---------------------------
  // Importing data and pre-trained class AMs
  //---------------------------
  // Importing input data
  logic [         NumPixels-1:0] temp_input_data [NumInputItems];
  initial $readmemb("./questa/vsim_data/mnist_input.txt", temp_input_data);

  // Reverse the bit order of each input item to match the expected format.
  // A bit mandatory because python's LSB is MSB in verilog.
  logic [         NumPixels-1:0] input_data [NumInputItems];
  initial begin
    for (int i = 0; i < NumInputItems; i++) begin
      for (int j = 0; j < NumPixels; j++) begin
        input_data[i][j] = temp_input_data[i][NumPixels - 1 - j];
      end
    end
  end

  // Importing pre-trained class AM
  logic [       HVDimension-1:0] class_am_data [NumClassAm];
  initial $readmemb("./questa/vsim_data/mnist_am_512.txt", class_am_data);

  //---------------------------
  // General tasks for automation
  //---------------------------
  // Load class AM
  task automatic load_class_am();
    for (int i = 0; i < NumClassAm; i++) begin
      w_valid_i <= '1;
      w_en_i <= '1;
      w_addr_i <= i;
      w_data_i <= class_am_data[i];
      @(posedge clk_i);
      @(posedge w_ready_o);
    end
    w_valid_i <= '0;
    w_en_i <= '0;
  endtask

  // Task to check the loaded class AM
  task automatic check_class_am();
    external_read_sel_i <= '1; // Select the external read port to read from AM
    for (int i = 0; i < NumClassAm; i++) begin
      // Load class AM into QHV
      ext_r_addr_i <= i;
      ext_r_req_valid_i <= '1;
      @(posedge clk_i);
      #1ps;
      assert(ext_r_resp_data_o == class_am_data[i]) else
        $fatal("Class AM - index %0d: expected %b, got %b", i, class_am_data[i], ext_r_resp_data_o);
    end
    ext_r_req_valid_i <= '0;
    ext_r_addr_i <= '0;
    external_read_sel_i <= '0;
  endtask

  // Task to apply input data to the DUT
  // The first half of the parallel inputs is for the ID which is the index
  // The second half is for the pixel data
  // However we input on a per-pixel basis
  // This is only applicable for the ID-level encoding
  task automatic apply_input_data(input logic [NumInputItems-1:0] item_index);
    for (int i = 0; i < NumPixels; i = i + ParallelInputsEnc) begin
      // Apply the item index on the first half of the parallel inputs
      for (int j = 0; j < ParallelInputsEnc; j++) begin
        im_rd_i[j] <= i + j + 2;
        im_rd_i[ParallelInputsEnc + j] <= input_data[item_index][i + j];
      end
      // Assert enc_valid for one cycle to indicate new data is available
      enc_valid_i <= '1;
      @(posedge clk_i);
      enc_valid_i <= '0;
    end
  endtask

  // Task to save to QHV
  task automatic save_qhv();
      // Assert qhv_wen for one cycle to save the current QHV
      qhv_wen_i <= '1;
      @(posedge clk_i);
      qhv_wen_i <= '0;
  endtask

  // Start AM search
  task automatic start_am_search();
    am_start_i <= '1;
    @(posedge clk_i);
    am_start_i <= '0;
  endtask

  // Clear encode
  task automatic clear_enc_qhv();
    enc_clr_i <= '1;
    qhv_clr_i <= '1;
    @(posedge clk_i);
    enc_clr_i <= '0;
    qhv_clr_i <= '0;
  endtask

  //---------------------------
  // Instantiate the DUT
  //---------------------------
`ifdef TARGET_SYNTHESIS
  vsax_id_level_top i_vsax_id_level_top (
`else
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
`endif
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

  //---------------------------
  // Simulation proper
  //---------------------------
  // Forever clock
  initial begin
    clk_i = 0;
    forever #`TCLK clk_i = ~clk_i;
  end

  // VCD dump checker only applicable for post-syn sims
`ifdef TARGET_SYNTHESIS
  initial begin
    @(posedge internal_state);
    $display("[%0t] VCD ON", $time);
    $dumpfile("./vcd_saif/vsax_id_level_top.vcd");
    $dumpvars(0, tb_vsax_id_level_top.i_vsax_id_level_top);
    @(negedge internal_state);
    $display("[%0t] VCD OFF", $time);
    $dumpoff;
    $dumpflush;
  end
`endif

  // Main stimuli
  initial begin
    // Initialize inputs and reset
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
    ext_r_resp_ready_i  = '1; // Assume always ready
    am_start_i          = '0;
    am_num_class_i      = NumClassAm;
    predict_ready_i     = '1; // Assume always ready
    internal_state      = '0; // Initialize to 0
    @(posedge clk_i);
    rst_ni = '1;
    @(posedge clk_i);

    // Load and verify class AM first
    load_class_am();
    check_class_am();

    // Start of VCD dump for post-synthesis sims
    internal_state = '1;

    // Main test loop: apply each input item, save QHV, start AM search, and check prediction
    for (int i = 0; i < NumInputItems; i++) begin
      $display("Applying input item %0d", i);
      // Apply input data for the current item
      apply_input_data(i);
      // Save the resulting QHV after encoding
      save_qhv();
      // Start the associative memory search
      start_am_search();
      // Wait for the prediction to be valid
      @(posedge predict_valid_o);
      //Print the predicted class for debugging
      $display("Predicted class for item %0d: %0d", i, predict_o);
      @(posedge clk_i);
      // Clear the encoder and QHV for the next item
      clear_enc_qhv();
    end

    // End of VCD dump for post-synthesis sims
    internal_state = '0;

    // Trailing clock cycles for sim purposes only
    for(int i=0; i<10; i++) @(posedge clk_i);
    $finish;
  end

endmodule
