// ===============================================================================
// Copyright 2024 KU Leuven
// Ryan Antonio <ryan.antonio@esat.kuleuven.be>
//
// Module:
//    Latch-based memory with synchronous write controller and valid-ready handshake
// Description:
//    A latch-based memory where the write path is guarded by a 3-cycle synchronous
//    controller to ensure safe latch timing.
//    Cycle 0 (IDLE)  : w_addr_i and w_data_i are captured into captured_addr and
//                      captured_w_data on a w_valid_i transaction.
//    Cycle 1 (WRITE) : reg_word_w_en is asserted from captured_addr, opening the
//                      target latch. reg_word_w_en is a registered signal to prevent
//                      any glitching from upstream combinational logic reaching the
//                      latch enables.
//    Cycle 2 (CLEAR) : reg_word_w_en is cleared (closing the latch), and
//                      captured_addr and captured_w_data are also cleared before
//                      the controller returns to IDLE.
//    The read path is synchronous and upon requests only.
// Parameters:
//    NumWords  : number of words in the memory (default 256)
//    DataWidth : width of each word in bits (default 32)
// IO ports:
//    clk_i     : clock input
//    rst_ni    : active-low reset input
//    w_valid_i   : upstream valid signal (initiates a write when high and ready)
//    w_ready_o   : downstream ready signal (low during WRITE and CLEAR cycles)
//    w_en_i    : write enable (1 for write, 0 for no-op, qualified by w_valid_i)
//    w_addr_i  : write address input
//    r_req_valid_i : read request valid input
//    r_req_ready_o : read request ready output (always high)
//    r_addr_i  : read address input
//    r_resp_valid_o : read response valid output (high for one cycle after accepting a read request)
//    r_resp_ready_i : read response ready input (response is accepted when high and r_resp_valid_o is high)
//    r_resp_data_o  : read data output
// ===============================================================================


module latch_memory #(
  parameter int unsigned NumWords  = 256,
  parameter int unsigned DataWidth = 32,
  // Don't touch parameters
  parameter int unsigned AddrWidth = $clog2(NumWords)
)(
  // Clock and reset
  input  logic                 clk_i,
  input  logic                 rst_ni,
  // Write inputs
  input  logic                 w_valid_i,
  output logic                 w_ready_o,
  input  logic                 w_en_i,
  input  logic [AddrWidth-1:0] w_addr_i,
  input  logic [DataWidth-1:0] w_data_i,
  // Read request input
  input  logic                 r_req_valid_i,
  output logic                 r_req_ready_o,
  input  logic [AddrWidth-1:0] r_addr_i,
  // Read response output
  output logic                 r_resp_valid_o,
  input  logic                 r_resp_ready_i,
  output logic [DataWidth-1:0] r_resp_data_o
);

  //---------------------------
  // Wires and regs
  //---------------------------
  logic [DataWidth-1:0] memory [NumWords];

  // Capture registers
  // Cycle 0 (IDLE): inputs are captured here on a valid transaction
  logic [AddrWidth-1:0] captured_addr;
  logic [DataWidth-1:0] captured_w_data;
  logic                 captured_w_en;

  // Registered per-word write enables
  // Asserted in WRITE, cleared in CLEAR — purely a register output,
  // no combinational logic between this and the latch enables
  logic [NumWords-1:0] reg_word_w_en;

  // Controller state
  typedef enum logic [1:0] {
    IDLE  = 2'b00,
    WRITE = 2'b01,
    CLEAR_WEN = 2'b10,
    CLEAR_CAPTURES = 2'b11
  } fsm_state_t;

  fsm_state_t ctrl_state;

  //---------------------------
  // Synchronous write controller
  //---------------------------
  always_ff @(posedge clk_i or negedge rst_ni) begin
    if (!rst_ni) begin
      // Capture registers
      captured_addr   <= '0;
      captured_w_data <= '0;
      captured_w_en   <= 1'b0;
      // All reg-word enables
      for (int i = 0; i < NumWords; i++) begin
        reg_word_w_en[i] <= 1'b0;
      end
      // Handshake
      w_ready_o         <= 1'b1;
      // State
      ctrl_state      <= IDLE;
      // Additional signal for read request ready (always ready)
      r_req_ready_o    <= 1'b1;
    end else begin
      case (ctrl_state)

        IDLE: begin
          // Cycle 0: capture inputs on a valid transaction
          if (w_valid_i) begin
            captured_addr   <= w_addr_i;
            captured_w_data <= w_data_i;
            captured_w_en   <= w_en_i;
            w_ready_o       <= 1'b0; // Not ready during WRITE and CLEAR cycles
            ctrl_state      <= WRITE;
            r_req_ready_o   <= 1'b0;
          end
        end

        WRITE: begin
          // Cycle 1: register the decoded word enable from captured_addr
          // reg_word_w_en is a clean flip-flop output — no glitch path to latches
          if (captured_w_en) begin
            reg_word_w_en[captured_addr] <= 1'b1;
          end
          ctrl_state <= CLEAR_WEN;
          r_req_ready_o    <= 1'b0;
        end

        CLEAR_WEN: begin
          // Cycle 2: clear reg_word_w_en to close the latch
          reg_word_w_en[captured_addr] <= 1'b0;
          captured_w_en   <= 1'b0;
          ctrl_state      <= CLEAR_CAPTURES;
          r_req_ready_o   <= 1'b0;
        end

        CLEAR_CAPTURES: begin
          // Cycle 3: clear captured address and data before returning to IDLE
          captured_addr   <= '0;
          captured_w_data <= '0;
          w_ready_o       <= 1'b1;
          r_req_ready_o   <= 1'b1;
          ctrl_state      <= IDLE;
        end

        default: begin
          // Capture registers
          captured_addr   <= '0;
          captured_w_data <= '0;
          captured_w_en   <= 1'b0;
          // All reg-word enables
          for (int i = 0; i < NumWords; i++) begin
            reg_word_w_en[i] <= 1'b0;
          end
          // Handshake
          w_ready_o        <= 1'b1;
          // State
          ctrl_state       <= IDLE;
          r_req_ready_o    <= 1'b1;
        end

      endcase
    end
  end

  //---------------------------
  // Latch array write logic
  //---------------------------
  // Each word has its own latch gated by reg_word_w_en[i].
  // reg_word_w_en is asserted in WRITE (after capture) and cleared in CLEAR,
  // giving a clean one-cycle window with no combinational glitch paths.
  generate
    for (genvar i = 0; i < NumWords; i++) begin : gen_latch_words
      always_latch begin
        if (reg_word_w_en[i]) begin
          memory[i] = captured_w_data;
        end
      end
    end
  endgenerate

  //---------------------------
  // Registered read logic
  //---------------------------
  always_ff @ (posedge clk_i or negedge rst_ni) begin
    if (!rst_ni) begin
      r_resp_valid_o <= 1'b0;
      r_resp_data_o       <= {DataWidth{1'b0}};
    end else begin
      // Assume that read_req_ready is always asserted
      if (r_req_valid_i) begin
        r_resp_valid_o <= 1'b1; // Valid response after accepting a read request
        r_resp_data_o <= memory[r_addr_i];
      end else if (r_resp_valid_o && r_resp_ready_i) begin
        r_resp_valid_o <= 1'b0; // Clear valid after response is accepted
        r_resp_data_o <= r_resp_data_o;
      end
    end
  end
endmodule
