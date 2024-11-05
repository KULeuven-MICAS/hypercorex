//---------------------------
// Copyright 2024 KU Leuven
// Ryan Antonio <ryan.antonio@esat.kuleuven.be>
//
// Module: Data Slicer
// Description:
// This module slices data very fetch
// from the low-dim input
//
// This module will only support:
// 1. 1-bit
// 2. 4-bit
// 3. 8-bit
// 4. Max-bit width (64b in this case)
//---------------------------

module data_slicer #(
  parameter int unsigned LowDimWidth     = 64,
  parameter int unsigned NumTotIm        = 1024,
  parameter int unsigned SlicerFifoDepth = 4,
  parameter int unsigned CsrDataWidth     = 32,
  // Don't touch!
  parameter int unsigned FifoFallthrough = 1'b0,
  parameter int unsigned ModeWidth       = 2,
  parameter int unsigned ImAddrWidth     = $clog2(NumTotIm)
)(
  // Clocks and reset
  input  logic                    clk_i,
  input  logic                    rst_ni,
  // Control inputs
  input  logic                    enable_i,
  input  logic                    clr_i,
  input  logic [  ModeWidth-1:0]  sel_mode_i,
  // Settings
  input  logic [CsrDataWidth-1:0] csr_elem_size_i,
  // Data inputs
  input  logic [ LowDimWidth-1:0] lowdim_data_i,
  input  logic                    lowdim_data_valid_i,
  output logic                    lowdim_data_ready_o,
  // Address outputs
  output logic [ ImAddrWidth-1:0] addr_o,
  output logic                    addr_valid_o,
  input  logic                    addr_ready_i
);

  //---------------------------
  // Local parameters
  //---------------------------

  // The total number of counts
  localparam int unsigned MaxCounter8b   = LowDimWidth / 8;
  localparam int unsigned MaxCounter4b   = LowDimWidth / 4;
  localparam int unsigned MaxCounter1b   = LowDimWidth / 1;

  // Mode definitions
  localparam int unsigned Mode64b        = 0;
  localparam int unsigned Mode1b         = 1;
  localparam int unsigned Mode4b         = 2;
  localparam int unsigned Mode8b         = 3;

  // Max counter width
  localparam int unsigned MaxCountWidth  = $clog2(MaxCounter1b);

  // Max element counter width
  localparam int unsigned MaxElemWidth   = 32;

  //---------------------------
  // Register and Wires
  //---------------------------

  logic [MaxCountWidth-1:0] chunk_count_reg;
  logic [ MaxElemWidth-1:0] elem_count_reg;
  logic                     count_control_reg;
  logic                     enable_elem_chunk_counter;
  logic                     count_control_ready;

  logic [MaxCountWidth-1:0] max_chunk_count;

  logic chunk_count_finish;
  logic elem_count_finish;

  logic [ImAddrWidth-1:0] data_slice;
  logic [7:0]             data_slice_8b [MaxCounter8b];
  logic [3:0]             data_slice_4b [MaxCounter4b];

  logic fifo_out_full;
  logic fifo_out_empty;

  logic fifo_out_push;
  logic fifo_out_pop;

  // Address data + 1 bit valid
  logic [ImAddrWidth-1:0] fifo_in_data;
  logic [ImAddrWidth-1:0] fifo_out_data;

  //---------------------------
  // Combinational Logic
  //---------------------------

  // Element counter finish
  assign elem_count_finish = (elem_count_reg == csr_elem_size_i-1);
  assign enable_elem_chunk_counter = enable_i && (sel_mode_i != Mode64b);

  // Selection for max count
  always_comb begin
    case (sel_mode_i)
      Mode1b:  max_chunk_count = MaxCounter1b;
      Mode4b:  max_chunk_count = MaxCounter4b;
      Mode8b:  max_chunk_count = MaxCounter8b;
      default: max_chunk_count = {MaxElemWidth{1'b0}};
    endcase
  end

  // Chunk count finish
  assign chunk_count_finish = (chunk_count_reg == max_chunk_count - 1);

  // Re-mapping signals
  always_comb begin
    // Re-map for 8b cuts
    for (int i = 0; i < MaxCounter8b; i++) begin
      data_slice_8b[i] = lowdim_data_i[8*i +: 8];
    end
    // Re-map for 4b cuts
    for (int i = 0; i < MaxCounter4b; i++) begin
      data_slice_4b[i] = lowdim_data_i[4*i +: 4];
    end
  end

  // Logic for data slicing in different modes other than 64b
  always_comb begin
    case (sel_mode_i)
      Mode1b:  begin
        data_slice = {{(ImAddrWidth-1){1'b0}}, lowdim_data_i[chunk_count_reg]};
      end
      Mode4b:  begin
        data_slice = {{(ImAddrWidth-4){1'b0}}, data_slice_4b[chunk_count_reg[3:0]]};
      end
      Mode8b:  begin
        data_slice = {{(ImAddrWidth-8){1'b0}}, data_slice_8b[chunk_count_reg[2:0]]};
      end
      default: begin
        data_slice = lowdim_data_i;
      end
    endcase
  end

  // Logic for FIFO input
  assign fifo_in_data = data_slice;

  //---------------------------
  // Chunk and Element Counter
  //---------------------------

  // Element counter
  always_ff @(posedge clk_i or negedge rst_ni) begin
    if (!rst_ni) begin
      elem_count_reg  <= {MaxElemWidth{1'b0}};
    end else begin
      if (enable_elem_chunk_counter) begin
        if (elem_count_finish) begin
          elem_count_reg <= {MaxElemWidth{1'b0}};
        end else if (fifo_out_push) begin
          elem_count_reg <= elem_count_reg + 1;
        end else begin
          elem_count_reg <= elem_count_reg;
        end
      end else begin
        elem_count_reg <= {MaxElemWidth{1'b0}};
      end
    end
  end

  // Chunk counter, note that the only difference
  // is that chunk counter also resets after every
  // element counter finish
  always_ff @(posedge clk_i or negedge rst_ni) begin
    if (!rst_ni) begin
      chunk_count_reg <= {MaxCountWidth{1'b0}};
    end else begin
      if (enable_elem_chunk_counter) begin
        if (chunk_count_finish || elem_count_finish) begin
          chunk_count_reg <= {MaxCountWidth{1'b0}};
        end else if (fifo_out_push) begin
          chunk_count_reg <= chunk_count_reg + 1;
        end else begin
          chunk_count_reg <= chunk_count_reg;
        end
      end else begin
        chunk_count_reg <= {MaxCountWidth{1'b0}};
      end
    end
  end

  //---------------------------
  // Chunk and Element Counter Control Register
  //---------------------------
  // This is for controlling the ready
  // signal towards the data streamers
  //---------------------------
  always_ff @(posedge clk_i or negedge rst_ni) begin
    if (!rst_ni) begin
      count_control_reg <= 1'b0;
    end else begin
      if (enable_elem_chunk_counter) begin
        if (fifo_out_push) begin
          count_control_reg <= 1'b1;
        end else begin
          count_control_reg <= count_control_reg;
        end
      end else begin
        count_control_reg <= 1'b0;
      end
    end
  end

  assign count_control_ready = count_control_reg && (chunk_count_finish || elem_count_finish);

  // FIFO control logic
  assign fifo_out_push = enable_i &&
                         lowdim_data_valid_i &&
                         !fifo_out_full;
  assign fifo_out_pop  = enable_i &&
                         addr_ready_i &&
                         !fifo_out_empty;

  //---------------------------
  // Output FIFO
  //---------------------------
  // Output width is IM addrwidth + 1 bit valid
  fifo_buffer #(
    .FallThrough     ( FifoFallthrough ),
    .DataWidth       ( ImAddrWidth     ),
    .FifoDepth       ( SlicerFifoDepth )
  ) i_fifo_data_slicer (
    // Clocks and reset
    .clk_i           ( clk_i           ),
    .rst_ni          ( rst_ni          ),
    // Software synchronous clear
    .clr_i           ( clr_i           ),
    // Status flags
    .full_o          ( fifo_out_full   ),
    .empty_o         ( fifo_out_empty  ),
    // Note that this counter state is index 1
    .counter_state_o ( /*Unused*/      ),
    // Input push
    .data_i          ( fifo_in_data    ),
    .push_i          ( fifo_out_push   ),
    // Output pop
    .data_o          ( fifo_out_data   ),
    .pop_i           ( fifo_out_pop    )
  );

  //---------------------------
  // Output
  //---------------------------
  // Data in FIFO is always valid
  // as long as it's not on an empty state
  assign addr_o       = fifo_out_data[ImAddrWidth-1:0];
  assign addr_valid_o = !fifo_out_empty;

  // We accept new data whenever FIFO is not full
  // and depending if the mode is ready or not
  assign lowdim_data_ready_o = (sel_mode_i == Mode64b) ?
                               (enable_i && !fifo_out_full) :
                               (enable_i && !fifo_out_full && count_control_ready);

endmodule
