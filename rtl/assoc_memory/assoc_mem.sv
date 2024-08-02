//---------------------------
// Copyright 2024 KU Leuven
// Ryan Antonio <ryan.antonio@esat.kuleuven.be>
//
// Module: Bundler Unit
// Description:
// Bi-directional bundler unit
// made per-bit position but with
// saturating counters
//---------------------------

module assoc_mem #(
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
  // AM side control
  input  logic [HVDimension-1:0] class_hv_i,
  input  logic                   class_hv_valid_i,
  output logic                   class_hv_ready_o,
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
  // Wires and logic
  //---------------------------
  logic [DataWidth-1:0] am_counter;
  logic [DataWidth-1:0] ham_dist_score;
  logic [DataWidth-1:0] curr_sim_score;
  logic [DataWidth-1:0] max_arg_idx;

  logic busy_reg;
  logic counter_done;
  logic class_hv_success;
  logic overwrite_sim_score;
  logic finished_predict;

  //---------------------------
  // Combinational logic
  //---------------------------
  assign counter_done        = (am_counter == (am_num_class_i-1)) ? 1'b1 : 1'b0;
  assign class_hv_success    = (class_hv_ready_o && class_hv_valid_i);
  assign overwrite_sim_score = (ham_dist_score <= curr_sim_score) ? 1'b1 : 1'b0;
  assign finished_predict    = (counter_done && class_hv_success) ? 1'b1 : 1'b0;

  // Class HV side is always ready when started
  // Same as busy register
  assign am_busy_o        = busy_reg;
  assign class_hv_ready_o = busy_reg;

  // Output CSR register for the max argument
  assign predict_o = max_arg_idx;

  // Stall happens when busy register is high
  // and when an am start signal is present
  assign am_stall_o = busy_reg && am_start_i;

  //---------------------------
  // AM counter control
  // 1. Priority given to finishing the count
  //    avoids getting stuck in an infinite loop
  //    Also, make sure it's a successful count though!
  // 2. Add am counter only when there's a success input
  //    and when the system is busy
  // 4. Otherwise, retain counter state
  //---------------------------
  always_ff @ (posedge clk_i  or negedge rst_ni) begin
    if (!rst_ni) begin
      am_counter <= {DataWidth{1'b0}};
    end else begin
      if (finished_predict) begin
        am_counter <= {DataWidth{1'b0}};
      end else if (busy_reg && class_hv_success) begin
        am_counter <= am_counter + 1;
      end else begin
        am_counter <= am_counter;
      end
    end
  end

  //---------------------------
  // Busy control
  // 1. Prioritize finishing the count when
  //    the counter is done and a successful transaction
  // 2. Start when not busy and start signal is
  //    present. Avoids restarting while busy.
  // 2. Retain state other wise
  //---------------------------
  always_ff @ (posedge clk_i  or negedge rst_ni) begin
    if (!rst_ni) begin
      busy_reg <= 1'b0;
    end else begin
      if (finished_predict) begin
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
    .HVDimension    ( HVDimension    ),
    .DataWidth      ( DataWidth      )
  ) i_ham_dist (
    // Inputs
    .A_i            ( query_hv_i     ),
    .B_i            ( class_hv_i     ),
    // Outputs
    .hamming_dist_o ( ham_dist_score )
  );

  //---------------------------
  // Similarity score tracker
  // 1. Only re-write when a new start begins
  // 2. Overwrite score when new hamming distance
  //    is less than the current score
  // 3. Otherwise, retain state
  //---------------------------
  always_ff @ (posedge clk_i  or negedge rst_ni) begin
    if (!rst_ni) begin
      curr_sim_score <= {DataWidth{1'b0}};
    end else begin
      if (!busy_reg && am_start_i) begin
        curr_sim_score <= {DataWidth{1'b1}};
      end else if (overwrite_sim_score & class_hv_success) begin
        curr_sim_score <= ham_dist_score;
      end else begin
        curr_sim_score <= curr_sim_score;
      end
    end
  end

  //---------------------------
  // Similarity index search
  //---------------------------
  always_ff @ (posedge clk_i  or negedge rst_ni) begin
    if (!rst_ni) begin
      max_arg_idx <= {DataWidth{1'b0}};
    end else begin
      if (!busy_reg && am_start_i) begin
        max_arg_idx <= {DataWidth{1'b0}};
      end else if (overwrite_sim_score & class_hv_success) begin
        max_arg_idx <= am_counter;
      end else begin
        max_arg_idx <= max_arg_idx;
      end
    end
  end

  //---------------------------
  // Valid-ready control for class HV
  //---------------------------
  always_ff @ (posedge clk_i  or negedge rst_ni) begin
    if (!rst_ni) begin
      predict_valid_o <= 1'b0;
    end else begin
      if (finished_predict) begin
        predict_valid_o <= 1'b1;
      end else if (predict_ready_i) begin
        predict_valid_o <= 1'b0;
      end else begin
        predict_valid_o <= predict_valid_o;
      end
    end
  end

  //---------------------------
  // Valid-ready control for CSR class HV
  //---------------------------
  always_ff @ (posedge clk_i  or negedge rst_ni) begin
    if (!rst_ni) begin
      am_predict_valid_o <= 1'b0;
    end else begin
      if (finished_predict) begin
        am_predict_valid_o <= 1'b1;
      end else if (am_predict_valid_clr_i) begin
        am_predict_valid_o <= 1'b0;
      end else begin
        am_predict_valid_o <= am_predict_valid_o;
      end
    end
  end



endmodule
