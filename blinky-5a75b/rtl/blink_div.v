// Divisor: genera una señal cuadrada de HZ hercios a partir de un reloj CLK_HZ.
//
// El valor inicial va en la declaración: en ECP5 el estado de arranque de los
// flip-flops forma parte del bitstream, así que no hace falta reset.

`default_nettype none
`timescale 1ns / 1ps

module blink_div #(
    parameter integer CLK_HZ = 25_000_000,
    parameter integer HZ     = 1
) (
    input  wire clk,
    output reg  out
);

    localparam integer TICKS = CLK_HZ / (2 * HZ);
    localparam integer W     = $clog2(TICKS);

    // Anchos explicitos para que el comparador y el sumador no se extiendan a
    // 32 bits. El truncado es seguro por construccion: W = $clog2(TICKS).
    /* verilator lint_off WIDTHTRUNC */
    localparam [W-1:0] LAST = TICKS - 1;
    localparam [W-1:0] ONE  = 1;
    /* verilator lint_on WIDTHTRUNC */

    reg [W-1:0] count = 0;

    initial out = 1'b0;

    always @(posedge clk) begin
        if (count == LAST) begin
            count <= 0;
            out   <= ~out;
        end else begin
            count <= count + ONE;
        end
    end

endmodule

`default_nettype wire
