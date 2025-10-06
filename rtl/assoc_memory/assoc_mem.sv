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
  parameter int unsigned DataWidth    = 8,
  // Don't touch!
  parameter int unsigned ExtCounterWidth = 5
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
  // Dimension expansion control
  input  logic                   extend_enable_i,
  input  logic [            4:0] extend_count_i,
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
  logic [ NumCompareWidth-1:0] am_counter_address;
  logic [CompareRegsWidth-1:0] ham_dist_score;
  logic [ NumCompareWidth-1:0] min_arg_idx;
  logic [ NumCompareWidth-1:0] min_arg_idx_reg;
  logic [CompareRegsWidth-1:0] min_arg_val;

  logic busy_reg;
  logic counter_done;
  logic class_hv_success;
  logic am_finished_set;

  logic [ExtCounterWidth-1:0] am_ext_counter;
  logic                       am_ext_counter_end;
  logic                       am_extend_finish;

  logic [NumCompareRegs-1:0] [CompareRegsWidth-1:0] compare_regs;
  logic                       last_compare_reg_save;

  //---------------------------
  // Combinational logic
  //---------------------------
  assign counter_done        = (am_counter_address >= (am_num_class_i-1)) ? 1'b1 : 1'b0;
  assign class_hv_success    = (class_hv_ready_o && class_hv_valid_i);
  assign am_finished_set     = (counter_done && class_hv_success);
  assign am_ext_counter_end  = (am_ext_counter >= extend_count_i-1);
  assign am_extend_finish    = (am_ext_counter_end && am_finished_set);

  // Class HV side is always ready when started
  // Same as busy register
  assign am_busy_o        = busy_reg;
  assign class_hv_ready_o = busy_reg;

  // Output CSR register for the max argument
  assign predict_o = min_arg_idx_reg;

  // Stall happens when busy register is high
  // and when an am start signal is present
  assign am_stall_o = busy_reg && am_start_i;

  //---------------------------
  // Dimensional expansion
  //---------------------------
  always_ff @(posedge clk_i or negedge rst_ni) begin
    if (!rst_ni) begin
      am_ext_counter <= '0;
    end else begin
      if (extend_enable_i) begin
        if ((am_ext_counter >= extend_count_i) && am_start_i) begin
          am_ext_counter <= '0;
        end else if (am_finished_set) begin
          am_ext_counter <= am_ext_counter + 1'b1;
        end else begin
          am_ext_counter <= am_ext_counter;
        end
      end else begin
        am_ext_counter <= '0;
      end
    end
  end

  //---------------------------
  // AM counter control
  // 1. Priority given to finishing the count
  //    avoids getting stuck in an infinite loop
  //    Also, make sure it's a successful count though!
  //    Also make sure that the AM extender is enabled
  //    if we are to reset the count for every am extension end
  // 2. Add am counter only when there's a success input
  //    and when the system is busy
  // 3. Otherwise, retain counter state
  //---------------------------
  always_ff @ (posedge clk_i  or negedge rst_ni) begin
    if (!rst_ni) begin
      am_counter_address <= {DataWidth{1'b0}};
    end else begin
      if (am_finished_set) begin
        am_counter_address <= {DataWidth{1'b0}};
      end else if (busy_reg && class_hv_success) begin
        am_counter_address <= am_counter_address + 1;
      end else begin
        am_counter_address <= am_counter_address;
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
      if (am_finished_set) begin
        busy_reg <= 1'b0;
      end else if (!busy_reg && am_start_i) begin
        busy_reg <= 1'b1;
      end else begin
        busy_reg <= busy_reg;
      end
    end
  end
// (!extend_enable_i && am_finished_set) ||
//           ( extend_enable_i && am_ext_counter_end && am_finished_set)
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
  //---------------------------
  always_ff @ (posedge clk_i  or negedge rst_ni) begin
    if (!rst_ni) begin
      for (int i = 0; i < NumCompareRegs; i++) begin
        compare_regs[i] <= {CompareRegsWidth{1'b1}};
      end
    end else begin
      if (!extend_enable_i && !busy_reg && am_start_i) begin
        for (int i = 0; i < NumCompareRegs; i++) begin
          compare_regs[i] <= {CompareRegsWidth{1'b1}};
        end
      end else if (extend_enable_i && !busy_reg && am_ext_counter_end && am_start_i) begin
        for (int i = 0; i < NumCompareRegs; i++) begin
          compare_regs[i] <= {CompareRegsWidth{1'b1}};
        end
      end else if (busy_reg && class_hv_success) begin
        // Starting from the FFFF state allows usu to "overflow"
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
  //---------------------------
  binary_compare #(
    .CompareRegsWidth ( CompareRegsWidth ),
    .NumCompareRegs   ( NumCompareRegs   )
  ) i_binary_compare (
    .compare_regs     ( compare_regs     ),
    .min_value_o      ( min_arg_val      ),
    .min_index_o      ( min_arg_idx      )
  );

  always_ff @ (posedge clk_i  or negedge rst_ni) begin
    if (!rst_ni) begin
      min_arg_idx_reg <= {NumCompareWidth{1'b0}};
    end else begin
      if (!busy_reg && am_start_i ) begin
        min_arg_idx_reg <= {NumCompareWidth{1'b0}};
      end else if (last_compare_reg_save) begin
        min_arg_idx_reg <= min_arg_idx;
      end else begin
        min_arg_idx_reg <= min_arg_idx_reg;
      end
    end
  end

  // A cycle delay since the registers are saved separately
  always_ff @ (posedge clk_i  or negedge rst_ni) begin
    if (!rst_ni) begin
      last_compare_reg_save <= 1'b0;
    end else begin
      if (!busy_reg && am_start_i || am_predict_valid_clr_i) begin
        last_compare_reg_save <= 1'b0;
      end else if ((!extend_enable_i && am_finished_set) ||
                   ( extend_enable_i && am_extend_finish)) begin
        last_compare_reg_save <= 1'b1;
      end else begin
        last_compare_reg_save <= 1'b0;
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
  // Valid-ready control for CSR class HV
  //---------------------------
  always_ff @ (posedge clk_i  or negedge rst_ni) begin
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
