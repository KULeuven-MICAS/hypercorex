//---------------------------
// Copyright 2024 KU Leuven
// Ryan Antonio <ryan.antonio@esat.kuleuven.be>
//
// Module: Register file set
//         for 1 write and 1 read port
// Description:
// A module for making register file sets.
// Useful for different dimensions and
// general purpose use.
//---------------------------

module reg_file_1w1r #(
  parameter int unsigned DataWidth    = 32,
  parameter int unsigned NumRegs      = 32,
  // Automatic computation - don't touch!
  parameter int unsigned NumRegsWidth = $clog2(NumRegs)
)(
  // Clocks and resets
  input  logic clk_i,
  input  logic rst_ni,
  // Write port
  input  logic                    clr_i,
  input  logic [NumRegsWidth-1:0] wr_addr_i,
  input  logic [   DataWidth-1:0] wr_data_i,
  input  logic                    wr_en_i,
  // Read port A
  input  logic [NumRegsWidth-1:0] rd_addr_i,
  output logic [   DataWidth-1:0] rd_data_o
);

  //---------------------------
  // Wires and regs
  //---------------------------
  logic [DataWidth-1:0] reg_file [NumRegs];

  //---------------------------
  // Register write control
  //---------------------------
  always_ff @ (posedge clk_i or negedge rst_ni) begin
    if (!rst_ni) begin
      // Initialize to 0 during resets
`ifdef SIM_VLT
        for (int i = 0; i < NumRegs; i++) begin
          reg_file[i] = {DataWidth{1'b0}}; // verilog_lint: waive always-ff-non-blocking
        end
`else
        for (int i = 0; i < NumRegs; i++) begin
          reg_file[i] <= {DataWidth{1'b0}};
        end
`endif
    end else begin
      if(clr_i) begin
`ifdef SIM_VLT
        for (int i = 0; i < NumRegs; i++) begin
          reg_file[i] = {DataWidth{1'b0}}; // verilog_lint: waive always-ff-non-blocking
        end
`else
        for (int i = 0; i < NumRegs; i++) begin
          reg_file[i] <= {DataWidth{1'b0}};
        end
`endif
      end else if(wr_en_i) begin
        reg_file[wr_addr_i] <= wr_data_i;
      end else begin
        reg_file[wr_addr_i] <= reg_file[wr_addr_i];
      end
    end
  end

  //---------------------------
  // Read control for port
  //---------------------------
  always_comb begin
    rd_data_o = reg_file[rd_addr_i];
  end

endmodule
