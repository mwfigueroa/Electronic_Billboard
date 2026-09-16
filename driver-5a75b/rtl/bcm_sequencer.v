// bcm_sequencer — secuenciador BCM de un frame (docs/11)
//
// Es el maestro de temporización: gobierna los ocho serializadores HUB75 en
// lockstep (comparten A/B/C, CLK, LAT y OE) y avanza los bitplanes con peso
// binario. Un frame con DEPTH bits por color son (2^DEPTH - 1) pasadas:
// el bitplane k se muestra 2^k veces, así el brillo sale ponderado.
//
// Esquema por paso de dirección (256 clocks de desplazamiento + blanking):
//
//   fase shift (SHIFT_CLOCKS): shift_en = 1, OE = 1
//       se desplazan los datos de la fila `row` mientras el panel muestra
//       los datos latcheados de `row - 1` (la dirección `addr` va un paso
//       atrás: shift-while-display, el truco que permite refrescar sin
//       tiempo extra de display).
//   fase blank (BLANK_CLOCKS): shift_en = 0, OE = 0
//       pulso de LAT en el medio y avance de `addr`/`row` al final.
//       Canal de datos detenido (CLK gateado por shift_en en el serializador).
//
// `oe` es un display-enable ACTIVO ALTO interno (1 = fila encendida). El pin
// OE de HUB75 es activo bajo, así que el top lo invierte al sacarlo (docs/08).
//
// Además, OE queda en bajo durante el primer clock de cada paso: la
// dirección cambia en el flanco anterior y así tiene un clock completo de
// asentamiento antes de que la fila se encienda (criterio de docs/11:
// "las transiciones de dirección y latch mantienen OE deshabilitado").
//
// Por eso el paso real dura SHIFT_CLOCKS + BLANK_CLOCKS: 8 x 260 = 2080
// clocks por pasada en vez de los 2048 ideales de docs/11 (que no contaban
// el blanking). A 12,5 MHz y 5 bits el refresco medido queda en ~194 Hz,
// por encima del criterio de aceptación de 192 Hz.
//
// El mapeo de (x, y) a fila y posición de cadena NO vive acá: es del
// scan_mapper, que recién se cierra con el panel (Paso 2 del bring-up).

`timescale 1ns / 1ps

module bcm_sequencer #(
    parameter integer DEPTH        = 5,     // bits por color
    parameter integer SHIFT_CLOCKS = 256,   // clocks por paso (cadena de 2 módulos)
    parameter integer BLANK_CLOCKS = 4,     // blanking de OE alrededor de LAT
    parameter integer ADDR_BITS    = 3      // pasos de dirección (1/8 scan)
) (
    input  wire                 clk,
    input  wire                 rst,        // síncrono, activo alto
    output reg  [ADDR_BITS-1:0] addr,       // A/B/C hacia la placa
    output reg  [ADDR_BITS-1:0] row,        // fila cuyos datos se desplazan
    output reg  [DEPTH-1:0]     bitplane,
    output reg  [7:0]           pix,        // 0..SHIFT_CLOCKS-1
    output wire                 shift_en,   // datos válidos en el serializador
    output wire                 lat,
    output wire                 oe,
    output reg                  frame_start
);

    localparam integer STEPS_PER_PASS = 1 << ADDR_BITS;
    localparam integer PHASE_LAST_I   = SHIFT_CLOCKS + BLANK_CLOCKS - 1;
    localparam integer SHIFT_LAST_I   = SHIFT_CLOCKS - 1;
    localparam integer SHIFT_W_I      = SHIFT_CLOCKS;
    localparam integer LAT_PHASE_I    = BLANK_CLOCKS / 2;
    localparam integer LAST_STEP_I    = STEPS_PER_PASS - 1;
    localparam integer LAST_BP_I      = DEPTH - 1;
    localparam [8:0] PHASE_LAST = PHASE_LAST_I[8:0];
    localparam [8:0] SHIFT_LAST = SHIFT_LAST_I[8:0];
    localparam [8:0] SHIFT_W    = SHIFT_W_I[8:0];
    localparam [8:0] LAT_PHASE  = LAT_PHASE_I[8:0];
    localparam [ADDR_BITS-1:0] LAST_STEP = LAST_STEP_I[ADDR_BITS-1:0];
    localparam [DEPTH-1:0]     LAST_BP   = LAST_BP_I[DEPTH-1:0];

    reg [8:0] phase;             // 0..PHASE_LAST dentro del paso
    reg [ADDR_BITS-1:0] step;    // 0..STEPS_PER_PASS-1 dentro de la pasada
    reg [4:0] pass;              // 0..2^(DEPTH-1)-1 dentro del bitplane

    wire shifting = (phase <= SHIFT_LAST);

    assign shift_en = shifting && !rst;
    assign oe       = shifting && (phase != 9'd0) && !rst;   // fase 0: asentamiento
    assign lat      = (!shifting) && !rst && ((phase - SHIFT_W) == LAT_PHASE);

    always @(posedge clk) begin
        if (rst) begin
            phase       <= 0;
            pix         <= 0;
            row         <= 0;
            addr        <= {ADDR_BITS{1'b1}};   // fila "anterior" a la 0
            step        <= 0;
            pass        <= 0;
            bitplane    <= 0;
            frame_start <= 1'b0;
        end else begin
            frame_start <= 1'b0;
            if (phase < SHIFT_LAST)
                pix <= pix + 1'b1;

            if (phase == PHASE_LAST) begin
                phase <= 0;
                pix   <= 0;
                row   <= row + 1'b1;            // envuelve dentro de ADDR_BITS
                addr  <= row;                   // lo que se acaba de shiftear
                if (step == LAST_STEP) begin
                    step <= 0;
                    if (pass == ((5'd1 << bitplane) - 5'd1)) begin
                        pass     <= 0;
                        bitplane <= (bitplane == LAST_BP) ? 0 : bitplane + 1'b1;
                        frame_start <= (bitplane == LAST_BP);
                    end else begin
                        pass <= pass + 1'b1;
                    end
                end else begin
                    step <= step + 1'b1;
                end
            end else begin
                phase <= phase + 1'b1;
            end
        end
    end

endmodule
