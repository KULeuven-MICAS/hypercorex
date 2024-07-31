//---------------------------
// Copyright 2024 KU Leuven
// Ryan Antonio <ryan.antonio@esat.kuleuven.be>
//
// Module: Testbench for Hypercorex
// Description:
// This module is the top-level testbench
// for the Hypercorex accelerator
//---------------------------

module tb_hypercorex # (
  //---------------------------
  // General Parameters
  //---------------------------
  parameter int unsigned HVDimension      = 512,
  //---------------------------
  // CSR Parameters
  //---------------------------
  parameter int unsigned CsrDataWidth     = 32,
  parameter int unsigned CsrAddrWidth     = 32,
  //---------------------------
  // Item Memory Parameters
  //---------------------------
  parameter int unsigned NumTotIm         = 1024,
  parameter int unsigned NumPerImBank     = 128,
  parameter int unsigned ImAddrWidth      = CsrDataWidth,
  parameter int unsigned SeedWidth        = CsrDataWidth,
  parameter int unsigned HoldFifoDepth    = 2,
  //---------------------------
  // Instruction Memory Parameters
  //---------------------------
  parameter int unsigned InstMemDepth     = 128,
  //---------------------------
  // HDC Encoder Parameters
  //---------------------------
  parameter int unsigned BundCountWidth   = 8,
  parameter int unsigned BundMuxWidth     = 2,
  parameter int unsigned ALUMuxWidth      = 2,
  parameter int unsigned ALUMaxShiftAmt   = 128,
  parameter int unsigned RegMuxWidth      = 2,
  parameter int unsigned QvMuxWidth       = 2,
  parameter int unsigned RegNum           = 4,
  //---------------------------
  // Don't touch!
  //---------------------------
  parameter int unsigned NumImSets        = NumTotIm/NumPerImBank,
  parameter int unsigned InstMemAddrWidth = $clog2(InstMemDepth),
  parameter int unsigned TbMemDepth       = 512,
  parameter int unsigned TbMemAddrWidth   = CsrAddrWidth
)(
  //---------------------------
  // Clocks and reset
  //---------------------------
  input  logic                    clk_i,
  input  logic                    rst_ni,
  //---------------------------
  // CSR RW control signals
  //---------------------------
  // Request
  input  logic [CsrDataWidth-1:0] csr_req_data_i,
  input  logic [CsrAddrWidth-1:0] csr_req_addr_i,
  input  logic                    csr_req_write_i,
  input  logic                    csr_req_valid_i,
  output logic                    csr_req_ready_o,
  // Response
  output logic [CsrDataWidth-1:0] csr_rsp_data_o,
  input  logic                    csr_rsp_ready_i,
  output logic                    csr_rsp_valid_o,
  //---------------------------
  // Memory module signals
  //---------------------------
  // Low or high dim mode
  input  logic                      highdim_mode_i,
  // Low dim signals
  input  logic [TbMemAddrWidth-1:0] im_a_lowdim_wr_addr_i,
  input  logic [  CsrDataWidth-1:0] im_a_lowdim_wr_data_i,
  input  logic                      im_a_lowdim_wr_en_i,
  input  logic [TbMemAddrWidth-1:0] im_a_lowdim_rd_addr_i,
  output logic [  CsrDataWidth-1:0] im_a_lowdim_rd_data_o,

  input  logic [TbMemAddrWidth-1:0] im_b_lowdim_wr_addr_i,
  input  logic [  CsrDataWidth-1:0] im_b_lowdim_wr_data_i,
  input  logic                      im_b_lowdim_wr_en_i,
  input  logic [TbMemAddrWidth-1:0] im_b_lowdim_rd_addr_i,
  output logic [  CsrDataWidth-1:0] im_b_lowdim_rd_data_o,
  // High dim signals
  input  logic [TbMemAddrWidth-1:0] im_a_highdim_wr_addr_i,
  input  logic [   HVDimension-1:0] im_a_highdim_wr_data_i,
  input  logic                      im_a_highdim_wr_en_i,
  input  logic [TbMemAddrWidth-1:0] im_a_highdim_rd_addr_i,
  output logic [   HVDimension-1:0] im_a_highdim_rd_data_o,

  input  logic [TbMemAddrWidth-1:0] im_b_highdim_wr_addr_i,
  input  logic [   HVDimension-1:0] im_b_highdim_wr_data_i,
  input  logic                      im_b_highdim_wr_en_i,
  input  logic [TbMemAddrWidth-1:0] im_b_highdim_rd_addr_i,
  output logic [   HVDimension-1:0] im_b_highdim_rd_data_o,

  // AM signals
  input  logic [TbMemAddrWidth-1:0] am_wr_addr_i,
  input  logic [   HVDimension-1:0] am_wr_data_i,
  input  logic                      am_wr_en_i,
  input  logic [TbMemAddrWidth-1:0] am_rd_addr_i,
  input  logic [TbMemAddrWidth-1:0] am_auto_loop_addr_i,
  output logic [   HVDimension-1:0] am_rd_data_o,
  // QHV signals
  input  logic [TbMemAddrWidth-1:0] qhv_rd_addr_i,
  output logic [   HVDimension-1:0] qhv_rd_data_o,
  // Enable signal for memory
  input  logic                      enable_mem_i
);

  //---------------------------
  // Wires and Logic
  //---------------------------
  logic [ ImAddrWidth-1:0] lowdim_a_data;
  logic [ HVDimension-1:0] highdim_a_data;
  logic                    im_a_data_valid;
  logic                    im_a_data_ready;

  logic [ ImAddrWidth-1:0] lowdim_b_data;
  logic [ HVDimension-1:0] highdim_b_data;
  logic                    im_b_data_valid;
  logic                    im_b_data_ready;

  logic                    qhv_ready;
  logic                    qhv_valid;
  logic [ HVDimension-1:0] qhv;

  logic [ HVDimension-1:0] class_hv;
  logic                    class_hv_valid;
  logic                    class_hv_ready;

  logic                    im_a_lowdim_valid;
  logic                    im_a_highdim_valid;
  logic                    im_a_valid;

  logic                    im_b_lowdim_valid;
  logic                    im_b_highdim_valid;
  logic                    im_b_valid;

  //---------------------------
  // Depending on Mode to Test
  //---------------------------
  assign im_a_data_valid = highdim_mode_i ? im_a_highdim_valid : im_a_lowdim_valid;
  assign im_b_data_valid = highdim_mode_i ? im_b_highdim_valid : im_b_lowdim_valid;

  //---------------------------
  // Memory Modules
  //---------------------------

  // Memory module for low dimensional memory IM A
  tb_rd_memory # (
    .DataWidth              ( CsrDataWidth          ),
    .AddrWidth              ( CsrAddrWidth          ),
    .MemDepth               ( TbMemDepth            )
  ) i_im_a_lowdim_memory (
    // Clock and reset
    .clk_i                  ( clk_i                 ),
    .rst_ni                 ( rst_ni                ),
    // Enable signal
    .en_i                   ( enable_mem_i          ),
    // Write port
    .wr_addr_i              ( im_a_lowdim_wr_addr_i ),
    .wr_data_i              ( im_a_lowdim_wr_data_i ),
    .wr_en_i                ( im_a_lowdim_wr_en_i   ),
    // Read port
    .rd_addr_i              ( im_a_lowdim_rd_addr_i ),
    .rd_data_o              ( im_a_lowdim_rd_data_o ),
    // Automatic loop mode
    .auto_loop_addr_i       ( '0                    ),
    .auto_loop_en_i         ( '0                    ),
    // Accelerator access port
    .rd_acc_addr_o          (                       ),
    .rd_acc_data_o          ( lowdim_a_data         ),
    .rd_acc_valid_o         ( im_a_lowdim_valid     ),
    .rd_acc_ready_i         ( im_a_data_ready       )
  );

  // Memory module for high dimensional memory IM B
  tb_rd_memory # (
    .DataWidth              ( HVDimension            ),
    .AddrWidth              ( CsrAddrWidth           ),
    .MemDepth               ( TbMemDepth             )
  ) i_im_a_highdim_memory (
    // Clock and reset
    .clk_i                  ( clk_i                  ),
    .rst_ni                 ( rst_ni                 ),
    // Enable signal
    .en_i                   ( enable_mem_i           ),
    // Write port
    .wr_addr_i              ( im_a_highdim_wr_addr_i ),
    .wr_data_i              ( im_a_highdim_wr_data_i ),
    .wr_en_i                ( im_a_highdim_wr_en_i   ),
    // Read port
    .rd_addr_i              ( im_a_highdim_rd_addr_i ),
    .rd_data_o              ( im_a_highdim_rd_data_o ),
    // Automatic loop mode
    .auto_loop_addr_i       ( '0                     ),
    .auto_loop_en_i         ( '0                     ),
    // Accelerator access port
    .rd_acc_addr_o          (                        ),
    .rd_acc_data_o          ( highdim_a_data         ),
    .rd_acc_valid_o         ( im_a_highdim_valid     ),
    .rd_acc_ready_i         ( im_a_data_ready        )
  );

  // Memory module for low dimensional memory IM B
  tb_rd_memory # (
    .DataWidth              ( CsrDataWidth          ),
    .AddrWidth              ( CsrAddrWidth          ),
    .MemDepth               ( TbMemDepth            )
  ) i_im_b_lowdim_memory (
    // Clock and reset
    .clk_i                  ( clk_i                 ),
    .rst_ni                 ( rst_ni                ),
    // Enable signal
    .en_i                   ( enable_mem_i          ),
    // Write port
    .wr_addr_i              ( im_b_lowdim_wr_addr_i ),
    .wr_data_i              ( im_b_lowdim_wr_data_i ),
    .wr_en_i                ( im_b_lowdim_wr_en_i   ),
    // Read port
    .rd_addr_i              ( im_b_lowdim_rd_addr_i ),
    .rd_data_o              ( im_b_lowdim_rd_data_o ),
    // Automatic loop mode
    .auto_loop_addr_i       ( '0                    ),
    .auto_loop_en_i         ( '0                    ),
    // Accelerator access port
    .rd_acc_addr_o          (                       ),
    .rd_acc_data_o          ( lowdim_b_data         ),
    .rd_acc_valid_o         ( im_b_lowdim_valid     ),
    .rd_acc_ready_i         ( im_b_data_ready       )
  );

  // Memory module for high dimensional memory IM B
  tb_rd_memory # (
    .DataWidth              ( HVDimension            ),
    .AddrWidth              ( CsrAddrWidth           ),
    .MemDepth               ( TbMemDepth             )
  ) i_im_b_highdim_memory (
    // Clock and reset
    .clk_i                  ( clk_i                  ),
    .rst_ni                 ( rst_ni                 ),
    // Enable signal
    .en_i                   ( enable_mem_i           ),
    // Write port
    .wr_addr_i              ( im_b_highdim_wr_addr_i ),
    .wr_data_i              ( im_b_highdim_wr_data_i ),
    .wr_en_i                ( im_b_highdim_wr_en_i   ),
    // Read port
    .rd_addr_i              ( im_b_highdim_rd_addr_i ),
    .rd_data_o              ( im_b_highdim_rd_data_o ),
    // Automatic loop mode
    .auto_loop_addr_i       ( '0                     ),
    .auto_loop_en_i         ( '0                     ),
    // Accelerator access port
    .rd_acc_addr_o          (                        ),
    .rd_acc_data_o          ( highdim_b_data         ),
    .rd_acc_valid_o         ( im_b_highdim_valid     ),
    .rd_acc_ready_i         ( im_b_data_ready        )
  );

  // Memory module for associative memory
  tb_rd_memory # (
    .DataWidth              ( HVDimension          ),
    .AddrWidth              ( CsrAddrWidth         ),
    .MemDepth               ( TbMemDepth           )
  ) i_am_memory (
    // Clock and reset
    .clk_i                  ( clk_i                ),
    .rst_ni                 ( rst_ni               ),
    // Enable signal
    .en_i                   ( enable_mem_i         ),
    // Write port
    .wr_addr_i              ( am_wr_addr_i         ),
    .wr_data_i              ( am_wr_data_i         ),
    .wr_en_i                ( am_wr_en_i           ),
    // Read port
    .rd_addr_i              ( am_rd_addr_i         ),
    .rd_data_o              ( am_rd_data_o         ),
    // Automatic loop mode
    .auto_loop_addr_i       ( am_auto_loop_addr_i  ),
    .auto_loop_en_i         ( 1'b1                 ),
    // Accelerator access port
    .rd_acc_addr_o          (                      ),
    .rd_acc_data_o          ( class_hv             ),
    .rd_acc_valid_o         ( class_hv_valid       ),
    .rd_acc_ready_i         ( class_hv_ready       )
  );

  //---------------------------
  // QHV write memory
  //---------------------------
  tb_wr_memory # (
    .DataWidth              ( HVDimension          ),
    .AddrWidth              ( CsrAddrWidth         ),
    .MemDepth               ( TbMemDepth           )
  ) i_qhv_memory (
    // Clock and reset
    .clk_i                  ( clk_i                ),
    .rst_ni                 ( rst_ni               ),
    // Enable signal
    .en_i                   ( enable_mem_i         ),
    // Read port
    .rd_addr_i              ( qhv_rd_addr_i        ),
    .rd_data_o              ( qhv_rd_data_o        ),
    // Force address to be written
    .set_wr_addr_i          ( '0                   ),
    .set_wr_en_i            ( '0                   ),
    // Accelerator access port
    .wr_acc_addr_o          (                      ),
    .wr_acc_data_i          ( qhv                  ),
    .wr_acc_valid_i         ( qhv_valid            ),
    .wr_acc_ready_o         ( qhv_ready            )
  );


endmodule
