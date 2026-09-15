// rgb_to_bitplane — RGB888 a bitplanes (docs/11, docs/14)
//
// La gamma y la cuantización se resuelven con una LUT de 256 entradas por
// canal generada por el simulador (`panel_sim.vectors`), así el resultado
// coincide bit a bit con `panel_sim.quantize`. La salida empaqueta los planos
// como [bit*3 + canal] (bit 0 = LSB; canal 0 = R, 1 = G, 2 = B), el mismo
// layout [bit][canal] del software, pre-mapeo de scan.
//
// Un registro de salida: `planes` es válido un ciclo después de `valid_in`.
// Corre cuando cambia el contenido, no en el camino crítico del refresco.
//
// Si el contrato de wire termina mandando bitplanes ya armados desde la PC
// (docs/14), este bloque no se instancia.

`timescale 1ns / 1ps

module rgb_to_bitplane #(
    parameter integer DEPTH    = 5,
    parameter         LUT_FILE = "../simulator/vectors/gamma_lut_2p2_5b.mem"
) (
    input  wire               clk,
    input  wire               valid_in,
    input  wire [23:0]        rgb,        // {R[7:0], G[7:0], B[7:0]}
    output reg                valid_out,
    output reg  [3*DEPTH-1:0] planes
);

    reg [DEPTH-1:0] lut [0:255];
    initial $readmemh(LUT_FILE, lut);

    wire [DEPTH-1:0] r_lvl = lut[rgb[23:16]];
    wire [DEPTH-1:0] g_lvl = lut[rgb[15:8]];
    wire [DEPTH-1:0] b_lvl = lut[rgb[7:0]];

    integer i;
    always @(posedge clk) begin
        valid_out <= valid_in;
        for (i = 0; i < DEPTH; i = i + 1) begin
            planes[i*3 + 0] <= r_lvl[i];
            planes[i*3 + 1] <= g_lvl[i];
            planes[i*3 + 2] <= b_lvl[i];
        end
    end

endmodule
