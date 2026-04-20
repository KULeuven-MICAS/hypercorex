//---------------------------
// Copyright 2024 KU Leuven
// Ryan Antonio <ryan.antonio@esat.kuleuven.be>
//
// Module:
// Binary similarity search unit for associative memory
// Description:
// This module performs a binary similarity search between an input
// query hypervector and a stream of class hypervectors, computing the
// Hamming distance between them and keeping track of the class hypervector
// with the minimum Hamming distance (i.e., most similar) to the query.
//
// The module drives a read request interface toward a latch memory:
//   - class_hv_addr_o      : read address (counts 0 to am_num_class_i-1)
//   - class_hv_req_valid_o : asserted while requests are in flight
//   - class_hv_req_ready_i : backpressure from the latch memory
//
// The latch memory response feeds back through:
//   - class_hv_i           : read data (latch memory r_resp_data_o)
//   - class_hv_valid_i     : read response valid (latch memory r_resp_valid_o)
//   - class_hv_read_o      : response ready, sent back to latch memory r_resp_ready_i
//
// Parameters:
//    HVDimension : dimensionality of the hypervectors (default 512)
//    DataWidth   : width of the output prediction in bits (default 8)
// IO ports:
//    clk_i                  : clock input
//    rst_ni                 : active-low reset input
//    query_hv_i             : input query hypervector (binary vector of length HVDimension)
//    am_start_i             : signal to start the similarity search (active high)
//    am_busy_o              : signal indicating the unit is busy performing a search
//    am_stall_o             : signal to stall the upstream logic (high when busy and start is asserted)
//    class_hv_i             : input class hypervector data from latch memory response
//    class_hv_valid_i       : valid signal for the class hypervector response
//    class_hv_read_o        : ready signal back to latch memory (r_resp_ready_i)
//    class_hv_addr_o        : read address output to latch memory (r_addr_i)
//    class_hv_req_valid_o   : read request valid to latch memory (r_req_valid_i)
//    class_hv_req_ready_i   : read request ready from latch memory (r_req_ready_o)
//    am_num_class_i         : number of class hypervectors to compare against (input from CSR)
//    am_predict_valid_o     : signal indicating the output prediction is valid (CSR-facing)
//    am_predict_valid_clr_i : signal to clear the valid signal for the output prediction
//    predict_o              : output prediction (index of the most similar class hypervector)
//    predict_valid_o        : signal indicating the output prediction is valid (stream-facing)
//    predict_ready_i        : signal indicating the downstream logic is ready to accept the prediction
//---------------------------

module bin_sim_search #(
  parameter int unsigned HVDimension  = 512,
  parameter int unsigned DataWidth    = 8
)(
  // Clocks and reset
  input  logic clk_i,
  input  logic rst_ni,
  // Encode side control
  input  logic [HVDimension-1:0] query_hv_i,
  input  logic                   am_start_i,
  output logic                   am_busy_o,
  output logic                   am_stall_o,
  // AM response side (from latch memory r_resp_*)
  input  logic [HVDimension-1:0] class_hv_i,
  input  logic                   class_hv_valid_i,
  output logic                   class_hv_read_o,
  // AM request side (to latch memory r_req_* / r_addr_i)
  output logic [ DataWidth-1:0]  class_hv_addr_o,
  output logic                   class_hv_req_valid_o,
  input  logic                   class_hv_req_ready_i,
  // CSR output side
  input  logic [  DataWidth-1:0] am_num_class_i,
  output logic                   am_predict_valid_o,
  input  logic                   am_predict_valid_clr_i,
  // Low-dim prediction
  output logic [  DataWidth-1:0] predict_o,
  output logic                   predict_valid_o,
  input  logic                   predict_ready_i
);

  //---------------------------
  // Local parameters
  //---------------------------
  localparam int unsigned NumCompareRegs   = 32;
  localparam int unsigned CompareRegsWidth = 16;
  localparam int unsigned NumCompareWidth  = $clog2(NumCompareRegs);

  //---------------------------
  // Wires and logic
  //---------------------------

  // Response-side address counter (tracks which compare_reg slot to write)
  logic [ NumCompareWidth-1:0] am_counter_address;
  logic [CompareRegsWidth-1:0] ham_dist_score;
  logic [ NumCompareWidth-1:0] min_arg_idx;
  logic [ NumCompareWidth-1:0] min_arg_idx_reg;
  logic [CompareRegsWidth-1:0] min_arg_val;

  logic busy_reg;
  logic counter_done;
  logic class_hv_success;
  logic am_finished_set;

  logic [NumCompareRegs-1:0] [CompareRegsWidth-1:0] compare_regs;
  logic                       last_compare_reg_save;

  // Request-side counter: drives class_hv_addr_o and class_hv_req_valid_o
  logic [ DataWidth-1:0] class_hv_req_counter;
  logic                  class_hv_req_done;

  //---------------------------
  // Combinational logic
  //---------------------------

  // Response-side: counter_done and finished detection
  assign counter_done        = (am_counter_address >= (am_num_class_i-1)) ? 1'b1 : 1'b0;
  assign class_hv_success    = (class_hv_read_o && class_hv_valid_i);
  assign am_finished_set     = (counter_done && class_hv_success);

  // class_hv_read_o: this module is ready to accept a response whenever busy
  assign am_busy_o        = busy_reg;
  assign class_hv_read_o  = busy_reg;

  // Request-side outputs:
  //   Assert req_valid while busy and not all requests have been issued yet
  assign class_hv_req_valid_o = busy_reg && !class_hv_req_done;
  assign class_hv_addr_o      = class_hv_req_counter;

  // Output CSR register for the min-distance argument
  assign predict_o = min_arg_idx_reg;

  // Stall happens when busy and an am_start arrives
  assign am_stall_o = busy_reg && am_start_i;

  //---------------------------
  // Request-side counter
  // Drives class_hv_addr_o (0 .. am_num_class_i-1) toward latch memory.
  // Advances on each accepted request (req_valid && req_ready).
  // Resets on fresh start: !busy_reg && am_start_i
  //---------------------------
  always_ff @(posedge clk_i or negedge rst_ni) begin
    if (!rst_ni) begin
      class_hv_req_counter <= '0;
      class_hv_req_done    <= 1'b0;
    end else begin
      if (!busy_reg && am_start_i) begin
        class_hv_req_counter <= '0;
        class_hv_req_done    <= 1'b0;
      end else if (class_hv_req_valid_o && class_hv_req_ready_i) begin
        // Accepted request: advance or mark done
        if (class_hv_req_counter >= am_num_class_i - 1) begin
          class_hv_req_done <= 1'b1;
        end else begin
          class_hv_req_counter <= class_hv_req_counter + 1'b1;
        end
      end else begin
        class_hv_req_counter <= class_hv_req_counter;
        class_hv_req_done    <= class_hv_req_done;
      end
    end
  end

  //---------------------------
  // AM response counter control
  // Tracks which compare_reg slot to write per accepted class HV response.
  // 1. Priority given to finishing the count (avoids getting stuck)
  // 2. Increment on every successful response handshake while busy
  // 3. Retain state otherwise
  //---------------------------
  always_ff @(posedge clk_i or negedge rst_ni) begin
    if (!rst_ni) begin
      am_counter_address <= '0;
    end else begin
      if (am_finished_set) begin
        am_counter_address <= '0;
      end else if (busy_reg && class_hv_success) begin
        am_counter_address <= am_counter_address + 1;
      end else begin
        am_counter_address <= am_counter_address;
      end
    end
  end

  //---------------------------
  // Busy control
  // 1. Clear when the last response of the final pass is accepted
  // 2. Set when idle and am_start_i is asserted
  // 3. Retain otherwise
  //---------------------------
  always_ff @(posedge clk_i or negedge rst_ni) begin
    if (!rst_ni) begin
      busy_reg <= 1'b0;
    end else begin
      if (am_finished_set) begin
        busy_reg <= 1'b0;
      end else if (!busy_reg && am_start_i) begin
        busy_reg <= 1'b1;
      end else begin
        busy_reg <= busy_reg;
      end
    end
  end

  //---------------------------
  // Hamming distance unit
  // Fully combinational popcount
  //---------------------------
  ham_dist #(
    .HVDimension    ( HVDimension      ),
    .DataWidth      ( CompareRegsWidth )
  ) i_ham_dist (
    // Inputs
    .A_i            ( query_hv_i       ),
    .B_i            ( class_hv_i       ),
    // Outputs
    .hamming_dist_o ( ham_dist_score   )
  );

  //---------------------------
  // Compare register set control
  // Resets to all-1s on start; accumulates Hamming distance per class index.
  // Starting from all-1s allows overflow to wrap to 0 as the "best" score.
  //---------------------------
  always_ff @(posedge clk_i or negedge rst_ni) begin
    if (!rst_ni) begin
      for (int i = 0; i < NumCompareRegs; i++) begin
        compare_regs[i] <= {CompareRegsWidth{1'b1}};
      end
    end else begin
      if (!busy_reg && am_start_i) begin
        for (int i = 0; i < NumCompareRegs; i++) begin
          compare_regs[i] <= {CompareRegsWidth{1'b1}};
        end
      end else if (busy_reg && class_hv_success) begin
        // Starting from FFFF allows the overflow trick
        compare_regs[am_counter_address] <= compare_regs[am_counter_address] + ham_dist_score + 1;
      end else begin
        for (int i = 0; i < NumCompareRegs; i++) begin
          compare_regs[i] <= compare_regs[i];
        end
      end
    end
  end

  //---------------------------
  // Binary compare unit
  // Combinationally finds the minimum value and its index
  //---------------------------
  binary_compare #(
    .CompareRegsWidth ( CompareRegsWidth ),
    .NumCompareRegs   ( NumCompareRegs   )
  ) i_binary_compare (
    .compare_regs     ( compare_regs     ),
    .min_value_o      ( min_arg_val      ),
    .min_index_o      ( min_arg_idx      )
  );

  // Latch the winning index one cycle after the last response is committed
  always_ff @(posedge clk_i or negedge rst_ni) begin
    if (!rst_ni) begin
      min_arg_idx_reg <= '0;
    end else begin
      if (!busy_reg && am_start_i) begin
        min_arg_idx_reg <= '0;
      end else if (last_compare_reg_save) begin
        min_arg_idx_reg <= min_arg_idx;
      end else begin
        min_arg_idx_reg <= min_arg_idx_reg;
      end
    end
  end

  // One-cycle pulse after the last compare register is written
  // Used to capture min_arg_idx and set predict_valid outputs
  always_ff @(posedge clk_i or negedge rst_ni) begin
    if (!rst_ni) begin
      last_compare_reg_save <= 1'b0;
    end else begin
      if (!busy_reg && am_start_i || am_predict_valid_clr_i) begin
        last_compare_reg_save <= 1'b0;
      end else if (am_finished_set) begin
        last_compare_reg_save <= 1'b1;
      end else begin
        last_compare_reg_save <= 1'b0;
      end
    end
  end

  //---------------------------
  // Stream-facing predict valid-ready
  //---------------------------
  always_ff @(posedge clk_i or negedge rst_ni) begin
    if (!rst_ni) begin
      predict_valid_o <= 1'b0;
    end else begin
      if (am_predict_valid_clr_i) begin
        predict_valid_o <= 1'b0;
      end else if (last_compare_reg_save) begin
        predict_valid_o <= 1'b1;
      end else if (predict_ready_i) begin
        predict_valid_o <= 1'b0;
      end else begin
        predict_valid_o <= predict_valid_o;
      end
    end
  end

  //---------------------------
  // CSR-facing predict valid
  //---------------------------
  always_ff @(posedge clk_i or negedge rst_ni) begin
    if (!rst_ni) begin
      am_predict_valid_o <= 1'b0;
    end else begin
      if (am_predict_valid_clr_i) begin
        am_predict_valid_o <= 1'b0;
      end else if (last_compare_reg_save) begin
        am_predict_valid_o <= 1'b1;
      end else begin
        am_predict_valid_o <= am_predict_valid_o;
      end
    end
  end

endmodule
