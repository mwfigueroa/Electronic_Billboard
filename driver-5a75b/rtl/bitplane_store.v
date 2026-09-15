// bitplane_store — memoria de bitplanes (docs/11)
//
// Simple dual port: el conversor escribe, el scan_mapper/secuenciador lee.
// Palabra = 3*DEPTH bits de un píxel, empaquetados [bit*3 + canal], igual que
// la salida de rgb_to_bitplane y que el layout [bit][canal] del software.
// Dirección lineal: addr = y*WIDTH + x (raster).
//
// Con los valores por defecto (256x128, 5 bits) son 32768 palabras de 15
// bits = 60 KB. En BRAM de ECP5, de 18 bits de ancho, eso ocupa 32 bloques
// DP16KD de 56 (~57 %), algo más que el 48 % estimado en docs/11 porque una
// palabra de 15 bits no llena los 18 del primitivo.
//
// El lado de lectura sirve una palabra por clock. El frente de serialización
// necesita 6 bits por clock (R1/G1/B1 y R2/G2/B2, o sea dos píxeles del
// bitplane actual), así que el scan_mapper tendrá que decidir entre leer a
// 2x del clock de píxel o duplicar el puerto; esa decisión queda abierta y
// depende del mapeo de rows que recién se conoce con el panel (Paso 2).

`timescale 1ns / 1ps

module bitplane_store #(
    parameter integer DEPTH     = 5,
    parameter integer WIDTH     = 256,
    parameter integer HEIGHT    = 128,
    parameter integer ADDR_BITS = $clog2(WIDTH * HEIGHT)
) (
    input  wire                 clk,
    // puerto de escritura (conversor)
    input  wire                 we,
    input  wire [ADDR_BITS-1:0] waddr,
    input  wire [3*DEPTH-1:0]   wdata,
    // puerto de lectura (scan_mapper / secuenciador)
    input  wire                 re,
    input  wire [ADDR_BITS-1:0] raddr,
    output reg  [3*DEPTH-1:0]   rdata,
    output reg                  rvalid
);

    localparam integer WORDS = WIDTH * HEIGHT;

    reg [3*DEPTH-1:0] mem [0:WORDS-1];

    always @(posedge clk) begin
        if (we)
            mem[waddr] <= wdata;
        if (re) begin
            rdata  <= mem[raddr];
            rvalid <= 1'b1;
        end else begin
            rvalid <= 1'b0;
        end
    end

endmodule
