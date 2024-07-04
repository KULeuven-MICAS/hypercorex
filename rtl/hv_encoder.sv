//---------------------------
// Copyright 2024 KU Leuven
// Ryan Antonio <ryan.antonio@esat.kuleuven.be>
//
// Module: Encoder
// Description:
// Main encoder module including glue logic
// for the registers, hypervector ALUs, 
// and other useful units.
//---------------------------

module hv_encoder #(
  parameter int unsigned HVDimension    = 512,
  parameter int unsigned BundCountWidth = 8,
  parameter int unsigned BundMuxWidth    = 2,
  parameter int unsigned ALUMuxWidth    = 2,
  parameter int unsigned ALUOpsWidth    = 2,
  parameter int unsigned ALUMaxShiftAmt = 128,
  parameter int unsigned RegMuxWidth    = 2,
  parameter int unsigned QvMuxWidth     = 2,
  parameter int unsigned RegNum         = 4,
  // Don't touch!
  parameter int unsigned ShiftWidth     = $clog2(ALUMaxShiftAmt),
  parameter int unsigned RegAddrWidth   = $clog2(RegNum)
)(
  // Clocks and reset
  input  logic clk_i,
  input  logic rst_ni,
  // Item memory inputs
  input  logic [ HVDimension-1:0] im_rd_a_i,
  input  logic [ HVDimension-1:0] im_rd_b_i,
  // Control ports for ALU
  input  logic [ ALUMuxWidth-1:0] alu_mux_a_i,
  input  logic [ ALUMuxWidth-1:0] alu_mux_b_i,
  input  logic [ ALUOpsWidth-1:0] alu_ops_i,
  input  logic [  ShiftWidth-1:0] alu_shift_amt_i,
  // Control ports for bundlers
  input  logic [BundMuxWidth-1:0] bund_mux_a_i,
  input  logic [BundMuxWidth-1:0] bund_mux_b_i,
  input  logic                    bund_valid_a_i,
  input  logic                    bund_valid_b_i,
  input  logic                    bund_clr_a_i,
  input  logic                    bund_clr_b_i,
  // Control ports for register ops
  input  logic [ RegMuxWidth-1:0] reg_mux_i,
  input  logic [RegAddrWidth-1:0] reg_rd_addr_a_i,
  input  logic [RegAddrWidth-1:0] reg_rd_addr_b_i,
  input  logic [RegAddrWidth-1:0] reg_wr_addr_i,
  input  logic                    reg_wr_en_i,
  // Control ports for query HV
  input  logic                    qhv_clr_i,
  input  logic                    qhv_wen_i,
  input  logic [  QvMuxWidth-1:0] qhv_mux_i,
  output logic [ HVDimension-1:0] qhv_o
);

  //---------------------------
  // Some fixed local parameters
  //---------------------------
  parameter int unsigned NumALUOps   = 4;

  //---------------------------
  // Wires
  //---------------------------
  logic [HVDimension-1:0] reg_wr_data;
  logic [HVDimension-1:0] reg_rd_data_a;
  logic [HVDimension-1:0] reg_rd_data_b;

  logic [HVDimension-1:0] alu_input_a;
  logic [HVDimension-1:0] alu_input_b;
  logic [HVDimension-1:0] alu_output;

  logic [HVDimension-1:0] bund_input_a;
  logic [HVDimension-1:0] bund_input_b;
  logic [HVDimension-1:0] bund_output_a;
  logic [HVDimension-1:0] bund_output_b;

  logic [HVDimension-1:0] qhv_input;
  logic [HVDimension-1:0] qhv_output;

  //---------------------------
  // HV register file MUX
  //---------------------------
  always_comb begin
    case ( reg_mux_i )
      2'b01:   reg_wr_data = im_rd_a_i;
      2'b10:   reg_wr_data = bund_output_a;
      2'b11:   reg_wr_data = bund_output_b;
      default: reg_wr_data = alu_output;
    endcase

  end

  //---------------------------
  // HV register file
  //---------------------------
  reg_file_1w2r #(
    .DataWidth    ( HVDimension     ),
    .NumRegs      ( RegNum          )
  ) i_reg_file_1w2r (
    // Clocks and resets
    .clk_i        ( clk_i           ),
    .rst_ni       ( rst_ni          ),
    // Write port
    .wr_addr_i    ( reg_wr_addr_i   ),
    .wr_data_i    ( reg_wr_data     ),
    .wr_en_i      ( reg_wr_en_i       ),
    // Read port A
    .rd_addr_a_i  ( reg_rd_addr_a_i ),
    .rd_data_a_o  ( reg_rd_data_a   ),
    // Read port B
    .rd_addr_b_i  ( reg_rd_addr_b_i ),
    .rd_data_b_o  ( reg_rd_data_b   )
  );

  //---------------------------
  // MUX-ing for ALU inputs
  //---------------------------
  always_comb begin
    // For port A
    case ( alu_mux_a_i )
      2'b01:   alu_input_a = reg_rd_data_a;
      2'b10:   alu_input_a = bund_output_a;
      2'b11:   alu_input_a = bund_output_b;
      default: alu_input_a = im_rd_a_i;
    endcase

    // For port B
    case ( alu_mux_b_i )
      2'b01:   alu_input_b = reg_rd_data_b;
      2'b10:   alu_input_b = bund_output_a;
      2'b11:   alu_input_b = bund_output_b;
      default: alu_input_b = im_rd_b_i;
    endcase
  end

  //---------------------------
  // HV ALU unit
  //---------------------------
  hv_alu_pe #(
    .HVDimension  ( HVDimension     ),
    .NumOps       ( NumALUOps       ),
    .MaxShiftAmt  ( ALUMaxShiftAmt  )
  ) i_hv_alu_pe (
    // Inputs
    .A_i          ( alu_input_a     ),
    .B_i          ( alu_input_b     ),
    // Outputs
    .C_o          ( alu_output      ), 
    // Control ports
    .op_i         ( alu_ops_i       ),
    .shift_amt_i  ( alu_shift_amt_i )
  );

  //---------------------------
  // MUX-ing for bundling units
  //---------------------------
  always_comb begin
    // For bundler A
    case ( bund_mux_a_i )
      2'b01:   bund_input_a = bund_output_b;
      2'b10:   bund_input_a = im_rd_a_i;
      2'b11:   bund_input_a = reg_rd_data_a;
      default: bund_input_a = alu_output;
    endcase

    // For bundler B
    case ( bund_mux_b_i )
      2'b01:   bund_input_b = bund_output_a;
      2'b10:   bund_input_b = im_rd_a_i;
      2'b11:   bund_input_b = reg_rd_data_a;
      default: bund_input_b = alu_output;
    endcase
  end


  //---------------------------
  // Bundler unit A
  // One can use this as spatial unit
  //---------------------------
  bundler_set #(
    .HVDimension    ( HVDimension      ),
    .CounterWidth   ( BundCountWidth   )
  ) i_bundler_set_a (
    .clk_i          ( clk_i            ),
    .rst_ni         ( rst_ni           ),
    .hv_i           ( bund_input_a     ),
    .valid_i        ( bund_valid_a_i   ),
    .clr_i          ( bund_clr_a_i     ),
    .counter_o      (), //Unused for now
    .binarized_hv_o ( bund_output_a    )
  );

  //---------------------------
  // Bundler unit B
  // One can use this as temporal unit
  //---------------------------
  bundler_set #(
    .HVDimension    ( HVDimension      ),
    .CounterWidth   ( BundCountWidth   )
  ) i_bundler_set_b (
    .clk_i          ( clk_i            ),
    .rst_ni         ( rst_ni           ),
    .hv_i           ( bund_input_b     ),
    .valid_i        ( bund_valid_b_i   ),
    .clr_i          ( bund_clr_b_i     ),
    .counter_o      (), //Unused for now
    .binarized_hv_o ( bund_output_b    )
  );

  //---------------------------
  // Query HV MUX
  //---------------------------
  always_comb begin
    case(qhv_mux_i)
      2'b01:   qhv_input = reg_rd_data_a;
      2'b10:   qhv_input = bund_output_a;
      2'b11:   qhv_input = bund_output_b;
      default: qhv_input = alu_output;
    endcase

  end

  //---------------------------
  // Query HV register
  //---------------------------

  always_ff @ (posedge clk_i or negedge rst_ni) begin
    if (!rst_ni) begin
      qhv_o <= {HVDimension{1'b0}};
    end else begin
      if (qhv_clr_i) begin
        qhv_o <= {HVDimension{1'b0}};
      end else if ( qhv_wen_i ) begin
        qhv_o <= qhv_input;
      end else begin
        qhv_o <= qhv_o;
      end
    end
  end

endmodule
