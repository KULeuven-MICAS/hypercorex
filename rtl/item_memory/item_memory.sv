//---------------------------
// Copyright 2024 KU Leuven
// Ryan Antonio <ryan.antonio@esat.kuleuven.be>
//
// Module: CA90 Item Memory
// Description:
// This is the main item memory block
// It consists of both the CiM and CA90
// with control ports that are used to select
// the IM addresses and whether it gets
// from CiM or from the CA 90
//---------------------------

module item_memory #(
  parameter int unsigned HVDimension = 512,
  parameter int unsigned NumTotIm    = 1024,
  parameter int unsigned NumPerImBank= 128,
  parameter int unsigned SeedWidth   = 32,
  parameter bit          EnableRomIM = 1'b0,
  // Don't touch!
  parameter int unsigned ImAddrWidth = $clog2(NumTotIm),
  parameter int unsigned NumImSets   = NumTotIm/NumPerImBank

)(
  // Clock and reset
  input  logic                                  clk_i,
  input  logic                                  rst_ni,
  // Configurations from CSR
  input  logic                                  port_a_cim_i,
  input  logic                [  SeedWidth-1:0] cim_seed_hv_i,
  input  logic [NumImSets-1:0][  SeedWidth-1:0] im_seed_hv_i,
  input  logic                [ImAddrWidth-1:0] im_a_addr_i,
  input  logic                [ImAddrWidth-1:0] im_b_addr_i,
  // For dimensional expansion
  input  logic                                  enable_i,
  input  logic                                  extend_enable_i,
  input  logic                                  extend_increment_i,
  input  logic                [            4:0] extend_count_i,
  // Outputs towards the encoder
  output logic                [HVDimension-1:0] im_a_o,
  output logic                [HVDimension-1:0] im_b_o
);

  //---------------------------
  // Local parameters
  //---------------------------
  localparam int unsigned NumCimLevels = HVDimension/2;
  localparam int unsigned CimSelWidth  = $clog2(NumCimLevels);

  //---------------------------
  // Wires
  //---------------------------
  logic [HVDimension-1:0] cim_a;
  logic [HVDimension-1:0] im_a;

  logic [1:0][HVDimension-1:0] mux_porta_out_in;

  logic [1:0][CimSelWidth-1:0] mux_cim_addr_in;
  logic      [CimSelWidth-1:0] mux_cim_addr_out;


  logic [1:0][ ImAddrWidth-1:0] mux_im_addr_in;
  logic      [ ImAddrWidth-1:0] mux_im_addr_out;

  logic [ImAddrWidth-1:0] im_addr_a_ext;
  logic [ImAddrWidth-1:0] im_addr_b_ext;

  logic [ImAddrWidth-1:0] im_ext_counter;
  logic                   im_ext_counter_end;

  //---------------------------
  // Input MUX for CiM
  //---------------------------
  assign mux_cim_addr_in[0] = {CimSelWidth{1'b0}};
  assign mux_cim_addr_in[1] = im_a_addr_i[CimSelWidth-1:0];

  mux #(
    .DataWidth  ( CimSelWidth       ),
    .NumSel     ( 2                 )
  ) i_mux_cim_in (
    .sel_i      ( port_a_cim_i      ),
    .signal_i   ( mux_cim_addr_in   ),
    .signal_o   ( mux_cim_addr_out  )
  );

  //---------------------------
  // CiM Module
  //---------------------------
  cim #(
    .HVDimension ( HVDimension      ),
    .SeedWidth   ( SeedWidth        )
  ) i_cim (
    .seed_hv_i   ( cim_seed_hv_i    ),
    .cim_sel_i   ( mux_cim_addr_out ),
    .cim_o       ( cim_a            )
  );

  //---------------------------
  // Input MUX for iM
  //---------------------------
  assign mux_im_addr_in[0] = im_addr_a_ext[ImAddrWidth-1:0];
  assign mux_im_addr_in[1] = {ImAddrWidth{1'b0}};

  mux #(
    .DataWidth  ( ImAddrWidth     ),
    .NumSel     ( 2               )
  ) i_mux_im_in (
    .sel_i      ( port_a_cim_i    ),
    .signal_i   ( mux_im_addr_in  ),
    .signal_o   ( mux_im_addr_out )
  );

  //---------------------------
  // Dimensional expansion
  //---------------------------
  assign im_ext_counter_end = (im_ext_counter == extend_count_i-1);

  always_ff @(posedge clk_i or negedge rst_ni) begin
    if (!rst_ni) begin
      im_ext_counter <= '0;
    end else begin
      if (extend_enable_i && enable_i) begin
        if (im_ext_counter_end && extend_increment_i) begin
          im_ext_counter <= '0;
        end else if (extend_increment_i) begin
          im_ext_counter <= im_ext_counter + 1'b1;
        end else begin
          im_ext_counter <= im_ext_counter;
        end
      end else begin
        im_ext_counter <= '0;
      end
    end
  end

  assign im_addr_a_ext = (extend_enable_i) ?
                         (im_a_addr_i + im_ext_counter):
                         im_a_addr_i;

  assign im_addr_b_ext = (extend_enable_i) ?
                         (im_b_addr_i + im_ext_counter):
                         im_b_addr_i;

  //---------------------------
  // CA90 iM Module
  //---------------------------
  if (EnableRomIM) begin: gen_use_rom_im
    rom_item_memory #(
    .HVDimension  ( HVDimension     ),
    .NumTotIm     ( NumTotIm        ),
    .SeedWidth    ( SeedWidth       )
  ) i_rom_item_memory (
    .im_sel_a_i   ( mux_im_addr_out ),
    .im_sel_b_i   ( im_addr_b_ext   ),
    .im_a_o       ( im_a            ),
    .im_b_o       ( im_b_o          )
  );
  end else begin: gen_use_ca90_im
    ca90_item_memory #(
    .HVDimension  ( HVDimension     ),
    .NumTotIm     ( NumTotIm        ),
    .NumPerImBank ( NumPerImBank    ),
    .SeedWidth    ( SeedWidth       )
  ) i_ca90_item_memory (
    .seed_hv_i    ( im_seed_hv_i    ),
    .im_sel_a_i   ( mux_im_addr_out ),
    .im_sel_b_i   ( im_b_addr_i     ),
    .im_a_o       ( im_a            ),
    .im_b_o       ( im_b_o          )
  );
  end

  //---------------------------
  // Output MUX
  //---------------------------
  assign mux_porta_out_in[0] = im_a;
  assign mux_porta_out_in[1] = cim_a;

  mux #(
    .DataWidth  ( HVDimension      ),
    .NumSel     ( 2                )
  ) i_mux_porta_out (
    .sel_i      ( port_a_cim_i     ),
    .signal_i   ( mux_porta_out_in ),
    .signal_o   ( im_a_o           )
  );

endmodule
