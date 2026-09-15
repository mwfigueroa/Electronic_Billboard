// Testbench de top.v — comprueba la cadencia y el patrón de rotación.
//
// Se instancia con un CLK_HZ ficticio para que TICKS sea pequeño:
// CLK_HZ=1000, BLINK_HZ=100 -> TICKS = 1000/200 = 5 ciclos por paso.

`default_nettype none
`timescale 1ns / 1ps

module tb_top;

    localparam integer TICKS = 5;

    reg        clk = 1'b0;
    wire [4:0] led;

    always #5 clk = ~clk;   // 100 MHz simulados

    top #(.CLK_HZ(1000), .BLINK_HZ(100)) dut (.clk(clk), .led(led));

    integer errors = 0;
    integer i;
    reg [3:0] expected_ring;
    reg       expected_slow;

    task check(input [3:0] ring, input slow);
        begin
            if (led[3:0] !== ring) begin
                $display("FAIL t=%0t: ring=%b, esperado %b", $time, led[3:0], ring);
                errors = errors + 1;
            end
            if (led[4] !== slow) begin
                $display("FAIL t=%0t: D5=%b, esperado %b", $time, led[4], slow);
                errors = errors + 1;
            end
        end
    endtask

    initial begin
        $dumpfile("sim/tb_top.vcd");
        $dumpvars(0, tb_top);

        @(negedge clk);
        check(4'b0001, 1'b0);   // estado inicial

        expected_ring = 4'b0001;
        expected_slow = 1'b0;

        // Ocho pasos: la rotación debe volver al origen dos veces y D5
        // debe alternar en cada paso.
        for (i = 0; i < 8; i = i + 1) begin
            repeat (TICKS) @(negedge clk);
            expected_ring = {expected_ring[2:0], expected_ring[3]};
            expected_slow = ~expected_slow;
            check(expected_ring, expected_slow);
        end

        // Tras 8 pasos de un anillo de 4, se vuelve al patrón inicial.
        if (led[3:0] !== 4'b0001) begin
            $display("FAIL: el anillo no volvio al origen tras 8 pasos");
            errors = errors + 1;
        end

        if (errors == 0)
            $display("PASS: %0d comprobaciones sin errores", 8*2 + 3);
        else
            $display("FAIL: %0d errores", errors);

        $finish;
    end

endmodule

`default_nettype wire
