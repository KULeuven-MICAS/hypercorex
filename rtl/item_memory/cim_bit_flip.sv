module cim_bit_flip #(
  parameter int unsigned HVDimension = 512,
  parameter int unsigned FlipBitPos  = 1
)(
  input  logic [HVDimension-1:0] hv_i,
  output logic [HVDimension-1:0] hv_o
);

  always_comb begin
    hv_o = {
      hv_i[HVDimension-1:HVDimension-FlipBitPos],
      !hv_i[HVDimension-FlipBitPos-1],
      hv_i[HVDimension-FlipBitPos-2:0]
    };
  end

endmodule
