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

module qhv #(
  parameter int unsigned HVDimension    = 512
)(
  // Clocks and reset
  input  logic clk_i,
  input  logic rst_ni,
  // Control ports for query HV
  input  logic [HVDimension-1:0] qhv_i,
  input  logic                   qhv_wen_i,
  input  logic                   qhv_clr_i,
  input  logic                   qhv_am_load_i,
  input  logic                   am_busy_i,
  output logic [HVDimension-1:0] qhv_o,
  output logic                   qhv_valid_o,
  input  logic                   qhv_ready_i,
  output logic                   qhv_stall_o
);

  //---------------------------
  // Query HV register
  //---------------------------
  always_ff @ (posedge clk_i or negedge rst_ni) begin
    if (!rst_ni) begin
      qhv_o <= {HVDimension{1'b0}};
    end else begin
      if (qhv_clr_i) begin
        qhv_o <= {HVDimension{1'b0}};
      // Only load or replace when AM is not busy
      end else if (qhv_wen_i && !am_busy_i) begin
        qhv_o <= qhv_i;
      end else begin
        qhv_o <= qhv_o;
      end
    end
  end

  //---------------------------
  // Control for the valid-ready signals
  //---------------------------
  logic  qhv_load_success;
  assign qhv_load_success = qhv_valid_o & qhv_ready_i;

  always_ff @ (posedge clk_i or negedge rst_ni) begin
    if (!rst_ni) begin
      qhv_valid_o <= 1'b0;
    end else begin
      if (qhv_clr_i) begin
        qhv_valid_o <= 1'b0;
      end else if (qhv_am_load_i) begin
        qhv_valid_o <= 1'b1;
      end else if (qhv_load_success) begin
        qhv_valid_o <= 1'b0;
      end else begin
        qhv_valid_o <= qhv_valid_o;
      end
    end
  end

  //---------------------------
  // QHV logic stall
  //---------------------------
  // Stall happens when query is still loaded
  // the valid signal indicates that previous write has not completed yet
  assign qhv_stall_o = (qhv_am_load_i && qhv_valid_o) ||
                       (am_busy_i && qhv_wen_i);

endmodule
