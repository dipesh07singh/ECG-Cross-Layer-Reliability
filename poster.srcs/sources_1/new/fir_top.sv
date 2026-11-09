`timescale 1ns / 1ps
//////////////////////////////////////////////////////////////////////////////////
// Company: 
// Engineer: 
// 
// Create Date: 20.10.2026 22:38:01
// Design Name: 
// Module Name: fir_top
// Project Name: 
// Target Devices: 
// Tool Versions: 
// Description: 
// 
// Dependencies: 
// 
// Revision:
// Revision 0.01 - File Created
// Additional Comments:
// 
//////////////////////////////////////////////////////////////////////////////////

module fir_top (
  input clk,
  input rst,
  input signed [11:0] ecg_x,
  input bist_start,
  input [15:0] golden,
  input f_en,
  input [1:0] f_kind,
  input [2:0] f_tap,
  input [4:0] f_bit,
  input f_val,
  output signed [15:0] y,
  output bist_busy,
  output bist_done,
  output bist_pass,
  output [15:0] bist_sig
);
  wire bist_mode;
  wire signed [11:0] bist_x;
  wire signed [11:0] x_sel;
  assign x_sel = bist_mode ? bist_x : ecg_x;

  fir_core u_fir (.clk(clk), .rst(rst), .x_in(x_sel), .f_en(f_en), .f_kind(f_kind),
                  .f_tap(f_tap), .f_bit(f_bit), .f_val(f_val), .y_out(y));

  bist_ctrl u_bist (.clk(clk), .rst(rst), .start(bist_start), .golden(golden), .y(y),
                    .bist_mode(bist_mode), .bist_x(bist_x), .busy(bist_busy),
                    .done(bist_done), .pass(bist_pass), .sig(bist_sig));
endmodule

