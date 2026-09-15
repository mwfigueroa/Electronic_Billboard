// Testbench de rgb_to_bitplane contra los vectores dorados del simulador.
//
// Carga el frame de entrada (frame_rgb888.mem), los 15 planos esperados
// (bitplane_b*_{r,g,b}.mem) y compara bit a bit la salida del DUT.
// VECDIR se define con -D en el Makefile; por defecto apunta al simulador.

`timescale 1ns / 1ps

`ifndef VECDIR
`define VECDIR "../simulator/vectors/"
`endif

module tb_rgb_to_bitplane;

    localparam integer W     = 16;
    localparam integer H     = 8;
    localparam integer DEPTH = 5;
    localparam integer N     = W * H;

    reg clk = 0;
    always #5 clk = ~clk;

    reg                valid_in = 0;
    reg  [23:0]        rgb = 0;
    wire               valid_out;
    wire [3*DEPTH-1:0] planes;

    rgb_to_bitplane #(
        .DEPTH(DEPTH),
        .LUT_FILE({`VECDIR, "gamma_lut_2p2_5b.mem"})
    ) dut (
        .clk(clk),
        .valid_in(valid_in),
        .rgb(rgb),
        .valid_out(valid_out),
        .planes(planes)
    );

    reg [23:0]  frame [0:N-1];
    reg [W-1:0] exp [0:15*H-1];  // [(bit*3 + canal)*H + y]

    integer fails = 0;
    integer checks = 0;
    integer n, bit_i, ch_i, y, x;

    initial begin
        $readmemh({`VECDIR, "frame_rgb888.mem"}, frame);
        $readmemh({`VECDIR, "bitplane_b0_r.mem"}, exp,  0*H,  1*H-1);
        $readmemh({`VECDIR, "bitplane_b0_g.mem"}, exp,  1*H,  2*H-1);
        $readmemh({`VECDIR, "bitplane_b0_b.mem"}, exp,  2*H,  3*H-1);
        $readmemh({`VECDIR, "bitplane_b1_r.mem"}, exp,  3*H,  4*H-1);
        $readmemh({`VECDIR, "bitplane_b1_g.mem"}, exp,  4*H,  5*H-1);
        $readmemh({`VECDIR, "bitplane_b1_b.mem"}, exp,  5*H,  6*H-1);
        $readmemh({`VECDIR, "bitplane_b2_r.mem"}, exp,  6*H,  7*H-1);
        $readmemh({`VECDIR, "bitplane_b2_g.mem"}, exp,  7*H,  8*H-1);
        $readmemh({`VECDIR, "bitplane_b2_b.mem"}, exp,  8*H,  9*H-1);
        $readmemh({`VECDIR, "bitplane_b3_r.mem"}, exp,  9*H, 10*H-1);
        $readmemh({`VECDIR, "bitplane_b3_g.mem"}, exp, 10*H, 11*H-1);
        $readmemh({`VECDIR, "bitplane_b3_b.mem"}, exp, 11*H, 12*H-1);
        $readmemh({`VECDIR, "bitplane_b4_r.mem"}, exp, 12*H, 13*H-1);
        $readmemh({`VECDIR, "bitplane_b4_g.mem"}, exp, 13*H, 14*H-1);
        $readmemh({`VECDIR, "bitplane_b4_b.mem"}, exp, 14*H, 15*H-1);

        for (n = 0; n < N; n = n + 1) begin
            @(negedge clk);
            rgb = frame[n];
            valid_in = 1;
            @(posedge clk);
            #1;
            y = n / W;
            x = n % W;
            if (!valid_out) begin
                fails = fails + 1;
                $display("FALLA: valid_out en bajo para el pixel %0d", n);
            end
            for (bit_i = 0; bit_i < DEPTH; bit_i = bit_i + 1) begin
                for (ch_i = 0; ch_i < 3; ch_i = ch_i + 1) begin
                    checks = checks + 1;
                    if (planes[bit_i*3 + ch_i] !== exp[(bit_i*3 + ch_i)*H + y][x]) begin
                        fails = fails + 1;
                        if (fails <= 10)
                            $display("  mismatch y=%0d x=%0d bit=%0d canal=%0d: esperado %b, obtenido %b",
                                     y, x, bit_i, ch_i,
                                     exp[(bit_i*3 + ch_i)*H + y][x],
                                     planes[bit_i*3 + ch_i]);
                    end
                end
            end
        end

        @(negedge clk);
        valid_in = 0;
        @(posedge clk);
        #1;
        $display("pixeles: %0d · comparaciones: %0d · fallas: %0d", N, checks, fails);
        if (fails == 0) begin
            $display("PASS: rgb_to_bitplane coincide con los vectores dorados");
            $finish;
        end
        $fatal(1, "FALLA: rgb_to_bitplane no coincide con los vectores dorados");
    end

endmodule
