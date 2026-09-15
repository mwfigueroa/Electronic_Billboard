// Blinky para Lattice iCEstick (iCE40HX1K-TQ144)
//
// D5 (verde, centro) parpadea a BLINK_HZ.
// D1..D4 (rojos, exteriores) rotan un "1" a la misma cadencia.
//
// Los parámetros existen para poder simular rápido: el testbench instancia el
// módulo con CLK_HZ pequeño en vez de esperar millones de ciclos.

`default_nettype none
`timescale 1ns / 1ps

module top #(
    parameter integer CLK_HZ   = 12_000_000,  // oscilador de la iCEstick
    parameter integer BLINK_HZ = 1
) (
    input  wire       clk,
    output wire [4:0] led   // [3:0] = D1..D4, [4] = D5
);

    localparam integer TICKS = CLK_HZ / (2 * BLINK_HZ);
    localparam integer W     = $clog2(TICKS);

    // Constantes con ancho explicito: evitan que el comparador y el sumador
    // se extiendan a 32 bits (verilator -Wall lo marca como WIDTHEXPAND).
    // El truncado de 32 a W bits es seguro por construccion, W = $clog2(TICKS).
    /* verilator lint_off WIDTHTRUNC */
    localparam [W-1:0] LAST = TICKS - 1;
    localparam [W-1:0] ONE  = 1;
    /* verilator lint_on WIDTHTRUNC */

    // Los registros arrancan con valor conocido: en iCE40 el estado inicial de
    // los flip-flops va en el bitstream, por eso no hace falta reset.
    reg [W-1:0] count = 0;
    reg         slow  = 1'b0;
    reg [3:0]   ring  = 4'b0001;

    wire tick = (count == LAST);

    always @(posedge clk) begin
        if (tick) begin
            count <= 0;
            slow  <= ~slow;
            ring  <= {ring[2:0], ring[3]};
        end else begin
            count <= count + ONE;
        end
    end

    assign led = {slow, ring};

endmodule

`default_nettype wire
