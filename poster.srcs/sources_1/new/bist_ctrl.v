`timescale 1ns / 1ps
//////////////////////////////////////////////////////////////////////////////////
// Company: 
// Engineer: 
// 
// Create Date: 20.10.2026 22:38:01
// Design Name: 
// Module Name: bist_ctrl
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


module bist_ctrl #(
  parameter int N_PAT = 8192,
  parameter int WARM  = 12     // cycles to flush ECG data out of the FIR
)(
  input  logic clk, rst, start,
  input  logic [15:0] golden,
  input  logic signed [15:0] y,
  output logic bist_mode,
  output logic signed [11:0] bist_x,
  output logic busy, done, pass,
  output logic [15:0] sig
);
  typedef enum logic [1:0] {IDLE, RUN, DONE} st_t;
  st_t st;
  logic [15:0] lfsr, misr, cnt;

  // advance the LFSR 12 steps in one clock -> every pattern is fresh
  function automatic logic [15:0] adv12(input logic [15:0] s);
    logic [15:0] t;
    t = s;
    for (int i = 0; i < 12; i++)
      t = {t[14:0], t[15]^t[14]^t[12]^t[3]};
    return t;
  endfunction

  assign bist_mode = (st == RUN);
  assign bist_x    = lfsr[11:0];
  assign busy      = (st == RUN);
  assign done      = (st == DONE);
  assign sig       = misr;
  assign pass      = (misr == golden);

  always_ff @(posedge clk) begin
    if (rst) begin
      st <= IDLE; lfsr <= 16'hACE1; misr <= '0; cnt <= '0;
    end else case (st)
      IDLE, DONE: if (start) begin
        st <= RUN; lfsr <= 16'hACE1; misr <= '0; cnt <= '0;
      end
      RUN: begin
        lfsr <= adv12(lfsr);
        cnt  <= cnt + 1;
        if (cnt >= WARM)
          misr <= {misr[14:0], misr[15]^misr[14]^misr[12]^misr[3]} ^ y;
        if (cnt == WARM + N_PAT - 1) st <= DONE;
      end
      default: st <= IDLE;
    endcase
  end
endmodule