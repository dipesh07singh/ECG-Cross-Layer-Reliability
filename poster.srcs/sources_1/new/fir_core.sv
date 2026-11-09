`timescale 1ns / 1ps
//////////////////////////////////////////////////////////////////////////////////
// Company: 
// Engineer: 
// 
// Create Date: 20.10.2026 22:38:01
// Design Name: 
// Module Name: fir_core
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

module fir_core (
  input clk,
  input rst,
  input signed [11:0] x_in,
  input f_en,
  input [1:0] f_kind,   // 0=accumulator, 1=product, 2=coefficient
  input [2:0] f_tap,
  input [4:0] f_bit,
  input f_val,          // 0=stuck-at-0, 1=stuck-at-1
  output reg signed [15:0] y_out
);
  function [11:0] coef_rom;
    input integer i;
    begin
      case (i)
        0: coef_rom = 12'd60;
        1: coef_rom = 12'd170;
        2: coef_rom = 12'd300;
        3: coef_rom = 12'd494;
        4: coef_rom = 12'd494;
        5: coef_rom = 12'd300;
        6: coef_rom = 12'd170;
        default: coef_rom = 12'd60;
      endcase
    end
  endfunction

  reg [95:0] sr;                 // 8 samples x 12 bits
  reg [11:0] cf;
  reg [11:0] xs;
  reg signed [23:0] p;
  reg signed [26:0] acc;
  integer i;

  always @* begin
    acc = 27'sd0;
    for (i = 0; i < 8; i = i + 1) begin
      cf = coef_rom(i);
      if (f_en && f_kind == 2'd2 && f_tap == i && f_bit < 12) cf[f_bit] = f_val;
      xs = sr[i*12 +: 12];
      p = $signed(xs) * $signed(cf);
      if (f_en && f_kind == 2'd1 && f_tap == i && f_bit < 24) p[f_bit] = f_val;
      acc = acc + p;
    end
    if (f_en && f_kind == 2'd0 && f_bit < 27) acc[f_bit] = f_val;
  end

  always @(posedge clk) begin
    if (rst) begin
      sr <= 96'd0;
      y_out <= 16'sd0;
    end else begin
      sr <= {sr[83:0], x_in};
      y_out <= acc[26:11];
    end
  end
endmodule

  
