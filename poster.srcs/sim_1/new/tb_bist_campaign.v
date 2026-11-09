`timescale 1ns / 1ps
//////////////////////////////////////////////////////////////////////////////////
// Company: 
// Engineer: 
// 
// Create Date: 20.10.2026 22:40:54
// Design Name: 
// Module Name: tb_bist_campaign
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
`timescale 1ns/1ps
module tb_bist_campaign;
  reg clk, rst, start;
  reg [15:0] golden;
  reg f_en, f_val;
  reg [1:0] f_kind;
  reg [2:0] f_tap;
  reg [4:0] f_bit;
  reg signed [11:0] ecg_x;
  wire signed [15:0] y;
  wire busy, done, pass;
  wire [15:0] sig;

  fir_top dut (.clk(clk), .rst(rst), .ecg_x(ecg_x), .bist_start(start), .golden(golden),
               .f_en(f_en), .f_kind(f_kind), .f_tap(f_tap), .f_bit(f_bit), .f_val(f_val),
               .y(y), .bist_busy(busy), .bist_done(done), .bist_pass(pass), .bist_sig(sig));

  initial clk = 0;
  always #5 clk = ~clk;

  task run_bist;
    begin
      @(negedge clk); start = 1;
      @(negedge clk); start = 0;
      wait (done == 1);
      @(negedge clk);
    end
  endtask

  integer fd, total, det, kind, tap, b, v, tmax, bmax;

  initial begin
    rst = 1; start = 0; golden = 16'd0; f_en = 0; f_val = 0;
    f_kind = 0; f_tap = 0; f_bit = 0; ecg_x = 0; total = 0; det = 0;
    fd = $fopen("bist_coverage.csv", "w");
    $fdisplay(fd, "kind,tap,bit,val,detected,sig");
    repeat (4) @(negedge clk);
    rst = 0;

    f_en = 0;
    run_bist;
    golden = sig;
    $display("GOLDEN SIGNATURE = %h", sig);

    for (kind = 0; kind < 3; kind = kind + 1) begin
      tmax = (kind == 0) ? 1 : 8;
      bmax = (kind == 0) ? 27 : ((kind == 1) ? 24 : 12);
      for (tap = 0; tap < tmax; tap = tap + 1)
        for (b = 0; b < bmax; b = b + 1)
          for (v = 0; v < 2; v = v + 1) begin
            f_en = 1; f_kind = kind; f_tap = tap; f_bit = b; f_val = v;
            run_bist;
            total = total + 1;
            if (!pass) det = det + 1;
            $fdisplay(fd, "%0d,%0d,%0d,%0d,%0d,%h", kind, tap, b, v, !pass, sig);
          end
    end

    f_en = 0;
    run_bist;
    $display("fault-free re-check pass = %0d (must be 1)", pass);
    $display("BIST detected %0d / %0d stuck-at faults", det, total);
    $fclose(fd);
    $finish;
  end
endmodule