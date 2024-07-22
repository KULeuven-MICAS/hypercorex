<%
  import math

  num_hier_layers = int(math.log2(cfg["hv_dim"]/cfg["seed_dim"]))

  print(num_hier_layers)
%>
//---------------------------
// Copyright 2024 KU Leuven
// Ryan Antonio <ryan.antonio@esat.kuleuven.be>
//
// Module: CA90 Item Memory Hierarchical Base
// Description:
// This is a template to generate the CA90
// base HV. A template is needed due to SV limitations.
//---------------------------

module ca90_hier_base #(
  parameter int unsigned HVDimension = ${cfg["hv_dim"]},
  parameter int unsigned SeedWidth   = ${cfg["seed_dim"]}
)(
  // Inputs
  input  logic [  SeedWidth-1:0] seed_hv_i,
  output logic [HVDimension-1:0] base_hv_o
);

  //---------------------------
  // Wires
  //---------------------------
% for i in range(0,num_hier_layers):
  logic [${cfg["seed_dim"]*(2**i)-1}:0] ca90_layer_out_${i};
% endfor

% for i in range(1,num_hier_layers):
  logic [${cfg["seed_dim"]*(2**i)-1}:0] ca90_layer_in_${i};
% endfor

  //---------------------------
  // Wiring concatenation
  //---------------------------
% for i in range(1,num_hier_layers):
  % if i == 1:
    assign ca90_layer_in_${i} = {ca90_layer_out_${i-1}, seed_hv_i};
  % else:
    assign ca90_layer_in_${i} = {ca90_layer_out_${i-1}, ca90_layer_in_${i-1}};
  % endif
% endfor

  //---------------------------
  // CA 90 modules
  //---------------------------

% for i in range(0,num_hier_layers):
  % if i == 0:
  ca90_unit #(
    .Dimension   ( ${cfg["seed_dim"]*(2**i)} )
  ) i_ca90_im_${i} (
    .vector_i    (        seed_hv_i ),
    .shift_amt_i (                1 ),
    .vector_o    ( ca90_layer_out_${i} )
  );
  % else:
  ca90_unit #(
    .Dimension   ( ${cfg["seed_dim"]*(2**i)} )
  ) i_ca90_im_${i} (
    .vector_i    (  ca90_layer_in_${i} ),
    .shift_amt_i (                1 ),
    .vector_o    ( ca90_layer_out_${i} )
  );
  % endif

% endfor
  //---------------------------
  // Concatenating for output
  //---------------------------

  assign base_hv_o = {
% for i in range(0, num_hier_layers):
    ca90_layer_out_${num_hier_layers-i-1},
% endfor
    seed_hv_i
  };

endmodule
