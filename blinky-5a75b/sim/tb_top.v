// Testbench de top.v — comprueba las dos cadencias y el efecto del boton.
//
// Se instancia con un CLK_HZ ficticio para que los divisores sean cortos:
//   SLOW: 100/(2*10) = 5 ciclos por semiperiodo
//   FAST: 100/(2*25) = 2 ciclos por semiperiodo
// La relacion rapido/lento es 2.5x, la misma que 4 Hz / 1.6 Hz; basta para
// verificar que son distintas y que cada divisor conmuta cuando debe.

`default_nettype none
`timescale 1ns / 1ps

module tb_top;

    localparam integer SLOW_TICKS = 5;
    localparam integer FAST_TICKS = 2;

    reg  clk   = 1'b0;
    reg  btn_n = 1'b1;   // sin presionar
    wire led_t6, led_p11;

    always #5 clk = ~clk;

    top #(.CLK_HZ(100), .SLOW_HZ(10), .FAST_HZ(25))
        dut (.clk25(clk), .btn_n(btn_n), .led_t6(led_t6), .led_p11(led_p11));

    integer errors = 0;
    integer i;
    integer slow_edges = 0;
    integer fast_edges = 0;
    integer slow_at_ratio = 0;
    integer fast_at_ratio = 0;
    reg exp_slow, exp_fast;

    task check(input [8*20:1] what, input got, input want);
        begin
            if (got !== want) begin
                $display("FAIL t=%0t: %0s=%b, esperado %b", $time, what, got, want);
                errors = errors + 1;
            end
        end
    endtask

    // Contadores de flanco, para comprobar la relacion de frecuencias.
    always @(led_t6)  if ($time > 0) slow_edges = slow_edges + 1;
    always @(led_p11) if ($time > 0) fast_edges = fast_edges + 1;

    initial begin
        $dumpfile("sim/tb_top.vcd");
        $dumpvars(0, tb_top);

        @(negedge clk);
        check("led_t6",  led_t6,  1'b0);
        check("led_p11", led_p11, 1'b0);

        // --- Cadencia lenta: cuatro conmutaciones -------------------------
        exp_slow = 1'b0;
        for (i = 0; i < 4; i = i + 1) begin
            repeat (SLOW_TICKS) @(negedge clk);
            exp_slow = ~exp_slow;
            check("led_t6", led_t6, exp_slow);
        end

        // --- El rapido debe haber conmutado 2.5 veces mas -----------------
        slow_at_ratio = slow_edges;
        fast_at_ratio = fast_edges;
        if (fast_edges != slow_edges * 5 / 2) begin
            $display("FAIL: flancos rapido=%0d lento=%0d, esperado %0d",
                     fast_edges, slow_edges, slow_edges * 5 / 2);
            errors = errors + 1;
        end

        // --- Boton presionado: ambas salidas a 0 --------------------------
        btn_n = 1'b0;
        repeat (4) @(negedge clk);          // 2 ciclos de sincronizador + margen
        repeat (SLOW_TICKS * 2) @(negedge clk);
        check("led_t6 (btn)",  led_t6,  1'b0);
        check("led_p11 (btn)", led_p11, 1'b0);

        // --- Soltar: vuelve a parpadear -----------------------------------
        btn_n = 1'b1;
        repeat (4) @(negedge clk);
        fast_edges = 0;
        repeat (FAST_TICKS * 4) @(negedge clk);
        if (fast_edges == 0) begin
            $display("FAIL: led_p11 no reanudo tras soltar el boton");
            errors = errors + 1;
        end

        if (errors == 0)
            $display("PASS: sin errores (relacion de flancos %0d:%0d = 2.5x, boton OK)",
                     fast_at_ratio, slow_at_ratio);
        else
            $display("FAIL: %0d errores", errors);

        $finish;
    end

endmodule

`default_nettype wire
