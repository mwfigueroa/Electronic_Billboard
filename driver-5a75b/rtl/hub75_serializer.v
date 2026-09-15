// hub75_serializer — una cadena HUB75 (docs/11)
//
// Registra los 6 bits de datos de la cadena y genera el CLK del panel,
// gateado por shift_en: el registro de desplazamiento del panel solo avanza
// cuando llegan datos válidos, así el blanking del secuenciador no corre la
// posición de los píxeles.
//
// `pins` va un clock atrás de `data` (registro de salida) y `clk_out` es el
// clock invertido: los datos cambian en el flanco de bajada y el panel
// muestrea en el de subida, lo que deja medio período de margen de setup.
//
// Se instancia ocho veces (una por puerto), todas con el mismo `shift_en`,
// `lat` y `oe` del bcm_sequencer: los ocho puertos van en lockstep.

`timescale 1ns / 1ps

module hub75_serializer (
    input  wire       clk,
    input  wire       shift_en,
    input  wire [5:0] data,     // {R1, G1, B1, R2, G2, B2}
    output reg  [5:0] pins,     // hacia el buffer de 5 V
    output wire       clk_out
);

    assign clk_out = shift_en & ~clk;

    always @(posedge clk) begin
        if (shift_en)
            pins <= data;
    end

endmodule
