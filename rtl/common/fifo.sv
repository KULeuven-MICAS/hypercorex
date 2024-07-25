//---------------------------
// Copyright 2024 KU Leuven
// Ryan Antonio <ryan.antonio@esat.kuleuven.be>
//
// Module: FIFO Module
// Description:
// Basic common FIFO utility module
// This is a derivative of the original FIFO
// made from the PULP common cells
//---------------------------

module fifo #(
  parameter bit          FallThrough   = 1'b0,
  parameter int unsigned DataWidth     = 32,
  parameter int unsigned FifoDepth     = 8,
  // Touch this only if you plan
  // to change the data type to be used
  parameter type dtype                 = logic [DataWidth-1:0],
  // Don't touch!
  parameter int unsigned FifoAddrWidth = (FifoDepth > 1) ? $clog2(FifoDepth) : 1
)(
  // Clocks and reset
  input  logic  clk_i,
  input  logic  rst_ni,
  // Software synchronous clear
  input  logic  clr_i,
  // Status flags
  output logic  full_o,
  output logic  empty_o,
  // Note that this counter state is index 1
  output logic  [FifoAddrWidth:0] counter_state_o,
  // Input push
  input  dtype  data_i,
  input  logic  push_i,
  // Output pop
  output dtype  data_o,
  input  logic  pop_i
);

  //---------------------------
  // Local parameter
  //---------------------------

  // Pointers to the read and write sections of the queue
  logic [FifoAddrWidth-1:0] read_pointer_n, read_pointer_q;
  logic [FifoAddrWidth-1:0] write_pointer_n, write_pointer_q;

  // keep a counter to keep track of the current queue status
  // this integer will be truncated by the synthesis tool
  logic [FifoAddrWidth:0] status_cnt_n, status_cnt_q;

  // Main FIFO component
  dtype [FifoDepth-1:0] mem_n, mem_q;

  //---------------------------
  // Some useful logic and
  // assignments for status flags
  //---------------------------
  assign counter_state_o = status_cnt_q[FifoAddrWidth:0];

  if (FifoDepth == 0) begin : gen_pass_through
      assign empty_o = ~push_i;
      assign full_o  = ~pop_i;
  end else begin : gen_fifo
      assign full_o  = (status_cnt_q == FifoDepth);
      assign empty_o = (status_cnt_q == 0) & ~(FallThrough & push_i);
  end

  // Read and write combinational logic
  always_comb begin : read_write_comb

      // Default assignments
      read_pointer_n  = read_pointer_q;
      write_pointer_n = write_pointer_q;
      status_cnt_n    = status_cnt_q;
      data_o          = (FifoDepth == 0) ? data_i : mem_q[read_pointer_q];
      mem_n           = mem_q;

      //---------------------------
      // Push logic
      //---------------------------

      // Can push as long as queue is not full
      // Handling incoming data must come
      // from the outside and not in here
      if (push_i && ~full_o) begin

          // Push the data onto the queue
          mem_n[write_pointer_q] = data_i;

          // Increment the write counter
          // this is dead code when FifoDepth is a power of two
          if (write_pointer_q == FifoDepth-1)
              write_pointer_n = '0;
          else
              write_pointer_n = write_pointer_q + 1;

          // Increment the overall counter
          status_cnt_n= status_cnt_q + 1;
      end

      //---------------------------
      // Pop logic
      //---------------------------

      // Can pop as long as queue is not empty
      // Handling incoming data must come
      // from the outside and not in here
      if (pop_i && ~empty_o) begin

          // Read from the queue is a default assignment
          // but increment the read pointer when success
          if (read_pointer_n == FifoDepth-1)
              read_pointer_n = '0;
          else
              read_pointer_n = read_pointer_q + 1;

          // Decerement the overall counter
          status_cnt_n   = status_cnt_q - 1;
      end

      // Keep the count pointer for simultaneous push and pop
      // and as long as it's neither full nor empty
      if (push_i && pop_i &&  ~full_o && ~empty_o)
          status_cnt_n   = status_cnt_q;

      // FIFO is in pass through mode -> do not change the pointers
      if (FallThrough && (status_cnt_q == 0) && push_i) begin
          data_o = data_i;
          if (pop_i) begin
              status_cnt_n = status_cnt_q;
              read_pointer_n = read_pointer_q;
              write_pointer_n = write_pointer_q;
          end
      end
  end

  //---------------------------
  // State updates
  //---------------------------
  always_ff @(posedge clk_i or negedge rst_ni) begin
      if(~rst_ni) begin
          read_pointer_q  <= '0;
          write_pointer_q <= '0;
          status_cnt_q    <= '0;
      end else begin
          if (clr_i) begin
              read_pointer_q  <= '0;
              write_pointer_q <= '0;
              status_cnt_q    <= '0;
            end else begin
              read_pointer_q  <= read_pointer_n;
              write_pointer_q <= write_pointer_n;
              status_cnt_q    <= status_cnt_n;
          end
      end
  end

  //---------------------------
  // Actual fifo updates
  //---------------------------
  always_ff @(posedge clk_i or negedge rst_ni) begin
      if(~rst_ni) begin
          mem_q <= '0;
      end else begin
          mem_q <= mem_n;
      end
  end

  //---------------------------
  // Sanity checking
  //---------------------------
`ifndef SYNTHESIS
`ifndef COMMON_CELLS_ASSERTS_OFF
  initial begin
      assert (FifoDepth > 0) else $error("FifoDepth must be greater than 0.");
  end

  full_write : assert property(
      @(posedge clk_i) disable iff (~rst_ni) (full_o |-> ~push_i))
      else $fatal (1, "Trying to push new data although the FIFO is full.");

  empty_read : assert property(
      @(posedge clk_i) disable iff (~rst_ni) (empty_o |-> ~pop_i))
      else $fatal (1, "Trying to pop data although the FIFO is empty.");
`endif
`endif

endmodule
