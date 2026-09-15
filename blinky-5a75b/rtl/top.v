// Paso 0 del bring-up de la Colorlight 5A-75B (rev 8.0, LFE5U-25F-6BG256C).
//
// Objetivo doble:
//
//   1. Validar el flujo yosys -> nextpnr-ecp5 -> ecppack -> openFPGALoader
//      sobre hardware real, cargando solo a SRAM.
//
//   2. Resolver la discrepancia documentada del pin del LED de usuario:
//      chubby75 indica T6, la guia de weigu indica P11. Ver
//      ../docs/12_referencias_tecnicas.md, seccion 7.
//
// Los dos pines candidatos se manejan a frecuencias distintas, asi que una
// sola carga identifica cual es el LED por su cadencia:
//
//   - parpadeo lento (1 Hz)  -> el LED esta en T6
//   - parpadeo rapido (4 Hz) -> el LED esta en P11
//   - ninguno parpadea       -> ninguna de las dos fuentes acierta
//
// El boton (R7, activo bajo) fuerza ambas salidas a 0, lo que ademas resuelve
// la polaridad: si al presionarlo el LED se enciende fijo, es activo bajo.
//
// No se toca ningun pin de los conectores HUB75 ni la SPI flash.

`default_nettype none
`timescale 1ns / 1ps

module top #(
    parameter integer CLK_HZ  = 25_000_000,  // reloj del PHY U13 en P6
    parameter integer SLOW_HZ = 1,
    parameter integer FAST_HZ = 4
) (
    input  wire clk25,
    input  wire btn_n,     // R7, activo bajo con pull-up
    output wire led_t6,    // candidato de chubby75
    output wire led_p11    // candidato de weigu
);

    wire slow, fast;

    blink_div #(.CLK_HZ(CLK_HZ), .HZ(SLOW_HZ)) u_slow (.clk(clk25), .out(slow));
    blink_div #(.CLK_HZ(CLK_HZ), .HZ(FAST_HZ)) u_fast (.clk(clk25), .out(fast));

    // Sincronizador de dos etapas: btn_n es asincrono respecto de clk25.
    reg [1:0] btn_sync = 2'b11;
    always @(posedge clk25)
        btn_sync <= {btn_sync[0], btn_n};

    wire pressed = ~btn_sync[1];

    assign led_t6  = pressed ? 1'b0 : slow;
    assign led_p11 = pressed ? 1'b0 : fast;

endmodule

`default_nettype wire
