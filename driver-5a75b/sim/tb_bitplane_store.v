// Testbench de bitplane_store: cadena conversor -> store -> lectura
//
// Escribe el frame dorado con rgb_to_bitplane (LUT incluida) en el store y
// lo relee al revés, comparando cada palabra contra los planos esperados
// reconstruidos desde los .mem del simulador. Valida el layout de palabra
// [bit*3 + canal] y la dirección lineal y = addr / W, x = addr % W.

`timescale 1ns / 1ps

`ifndef VECDIR
`define VECDIR "../simulator/vectors/"
`endif

module tb_bitplane_store;

    localparam integer W     = 16;
    localparam integer H     = 8;
    localparam integer DEPTH = 5;
    localparam integer N     = W * H;
    localparam integer ADDR_BITS = $clog2(N);

    reg clk = 0;
    always #5 clk = ~clk;

    reg                valid_in = 0;
    reg  [23:0]        rgb = 0;
    wire               valid_out;
    wire [3*DEPTH-1:0] planes;

    rgb_to_bitplane #(
        .DEPTH(DEPTH),
        .LUT_FILE({`VECDIR, "gamma_lut_2p2_5b.mem"})
    ) dut_conv (
        .clk(clk),
        .valid_in(valid_in),
        .rgb(rgb),
        .valid_out(valid_out),
        .planes(planes)
    );

    reg                 we = 0;
    reg  [ADDR_BITS-1:0] waddr = 0;
    reg                 re = 0;
    reg  [ADDR_BITS-1:0] raddr = 0;
    wire [3*DEPTH-1:0]  rdata;
    wire                rvalid;

    bitplane_store #(
        .DEPTH(DEPTH),
        .WIDTH(W),
        .HEIGHT(H)
    ) dut_store (
        .clk(clk),
        .we(we),
        .waddr(waddr),
        .wdata(planes),
        .re(re),
        .raddr(raddr),
        .rdata(rdata),
        .rvalid(rvalid)
    );

    reg [23:0]        frame [0:N-1];
    reg [W-1:0]       exp [0:15*H-1];
    reg [3*DEPTH-1:0] exp_word [0:N-1];

    integer fails = 0;
    integer n, bit_i, ch_i, y, x;
    reg [3*DEPTH-1:0] word;

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

        // palabra esperada por píxel, [bit*3 + canal]
        for (n = 0; n < N; n = n + 1) begin
            y = n / W;
            x = n % W;
            word = 0;
            for (bit_i = 0; bit_i < DEPTH; bit_i = bit_i + 1)
                for (ch_i = 0; ch_i < 3; ch_i = ch_i + 1)
                    word[bit_i*3 + ch_i] = exp[(bit_i*3 + ch_i)*H + y][x];
            exp_word[n] = word;
        end

        // fase 1: conversor -> store
        for (n = 0; n < N; n = n + 1) begin
            @(negedge clk);
            rgb = frame[n];
            valid_in = 1;
            @(posedge clk);
            #1;
            if (!valid_out) begin
                fails = fails + 1;
                $display("FALLA [%0t]: valid_out en bajo para el pixel %0d", $time, n);
            end
            we = 1;
            waddr = n[ADDR_BITS-1:0];
            @(posedge clk);   // se escribe mem[n]
            #1;
        end
        @(negedge clk);
        we = 0;
        valid_in = 0;

        // fase 2: lectura al revés contra los planos esperados
        for (n = N-1; n >= 0; n = n - 1) begin
            @(negedge clk);
            re = 1;
            raddr = n[ADDR_BITS-1:0];
            @(posedge clk);
            #1;
            if (!rvalid) begin
                fails = fails + 1;
                $display("FALLA [%0t]: rvalid en bajo para addr %0d", $time, raddr);
            end
            if (rdata !== exp_word[raddr]) begin
                fails = fails + 1;
                if (fails <= 10)
                    $display("FALLA [%0t]: addr %0d -> %b, esperado %b",
                             $time, raddr, rdata, exp_word[raddr]);
            end
        end
        @(negedge clk);
        re = 0;
        @(posedge clk);
        #1;

        $display("palabras: %0d · fallas: %0d", N, fails);
        if (fails == 0) begin
            $display("PASS: bitplane_store conserva el frame del conversor");
            $finish;
        end
        $fatal(1, "FALLA: bitplane_store no devolvio el frame esperado");
    end

endmodule
