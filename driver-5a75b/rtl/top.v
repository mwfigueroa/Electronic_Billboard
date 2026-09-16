// top — top de integración del driver (docs/11, docs/16)
//
// Cadena completa de un frame de prueba, sin panel:
//
//   patrón RGB888 -> rgb_to_bitplane -> bitplane_store -> bcm_sequencer
//        -> 8 x hub75_serializer -> J1..J8
//
// Es un top de bring-up e integración, no el driver final:
//
//   - El generador escribe el patrón una vez tras el reset: R = x,
//     G ~ y (2y + bit 6), B = damero. 32768 píxeles, uno por clock.
//   - El mapeo de lectura es un PLACEHOLDER (y = row, x = pix): el mapeo
//     real de scan lo definirá el scan_mapper (Paso 2, con panel).
//   - Los ocho serializadores reciben el mismo dato (una lectura por clock);
//     el reparto por cadena también es del scan_mapper.
//   - R1 y R2 usan el mismo píxel del placeholder.
//
// Corre a 25 MHz (clock del PHY): 5 bits por color -> 388 Hz de refresco,
// por encima del criterio de 192 Hz.

`timescale 1ns / 1ps

module top #(
    parameter integer DEPTH    = 5,
    parameter integer WIDTH    = 256,
    parameter integer HEIGHT   = 128,
    parameter         LUT_FILE = "../simulator/vectors/gamma_lut_2p2_5b.mem"
) (
    input  wire clk25,
    input  wire btn_n,          // activo bajo: recarga el patrón
    output wire led_t6,         // latido de frame (candidato a LED de usuario)
    output wire led_p11,        // el otro candidato; la placa decide cuál es
    output wire hub_a,
    output wire hub_b,
    output wire hub_c,
    output wire hub_d,          // sin uso (scan 1/8): a 0
    output wire hub_e,          // sin uso: a 0
    output wire hub_clk,
    output wire hub_lat,
    output wire hub_oe,
    output wire j1_r1, j1_g1, j1_b1, j1_r2, j1_g2, j1_b2,
    output wire j2_r1, j2_g1, j2_b1, j2_r2, j2_g2, j2_b2,
    output wire j3_r1, j3_g1, j3_b1, j3_r2, j3_g2, j3_b2,
    output wire j4_r1, j4_g1, j4_b1, j4_r2, j4_g2, j4_b2,
    output wire j5_r1, j5_g1, j5_b1, j5_r2, j5_g2, j5_b2,
    output wire j6_r1, j6_g1, j6_b1, j6_r2, j6_g2, j6_b2,
    output wire j7_r1, j7_g1, j7_b1, j7_r2, j7_g2, j7_b2,
    output wire j8_r1, j8_g1, j8_b1, j8_r2, j8_g2, j8_b2
);

    localparam integer PIXELS      = WIDTH * HEIGHT;
    localparam integer LAST_PIX_I  = PIXELS - 1;
    localparam [14:0]  LAST_PIX    = LAST_PIX_I[14:0];

    wire rst = ~btn_n;

    // --- generador del patrón (una vez tras el reset) -----------------------
    reg  [14:0] gen_addr;
    reg         gen_run;
    reg  [14:0] waddr_d;

    always @(posedge clk25) begin
        if (rst) begin
            gen_addr <= 15'd0;
            gen_run  <= 1'b1;
        end else if (gen_addr != LAST_PIX) begin
            gen_addr <= gen_addr + 15'd1;
            gen_run  <= 1'b1;
        end else begin
            gen_run  <= 1'b0;      // el último píxel ya se emitió
        end
    end

    always @(posedge clk25)
        waddr_d <= gen_addr;

    wire [7:0] px_x  = gen_addr[7:0];
    wire [7:0] px_y  = {1'b0, gen_addr[14:8]};
    wire [7:0] pat_r = px_x;
    wire [7:0] pat_g = (px_y << 1) | {7'b0, px_y[6]};
    wire [7:0] pat_b = (px_x[0] ^ px_y[0]) ? 8'hFF : 8'h00;

    // --- conversión a bitplanes ---------------------------------------------
    wire               conv_valid;
    wire [3*DEPTH-1:0] conv_planes;

    rgb_to_bitplane #(
        .DEPTH(DEPTH),
        .LUT_FILE(LUT_FILE)
    ) conv (
        .clk(clk25),
        .valid_in(gen_run && !rst),
        .rgb({pat_r, pat_g, pat_b}),
        .valid_out(conv_valid),
        .planes(conv_planes)
    );

    // --- secuenciador BCM ---------------------------------------------------
    wire [2:0]       seq_addr, seq_row;
    wire [DEPTH-1:0] seq_bp;
    wire [7:0]       seq_pix;
    wire             seq_shift, seq_lat, seq_oe, seq_frame;

    bcm_sequencer #(
        .DEPTH(DEPTH)
    ) seq (
        .clk(clk25),
        .rst(rst),
        .addr(seq_addr),
        .row(seq_row),
        .bitplane(seq_bp),
        .pix(seq_pix),
        .shift_en(seq_shift),
        .lat(seq_lat),
        .oe(seq_oe),
        .frame_start(seq_frame)
    );

    // --- store y lectura (placeholder: y = row, x = pix) --------------------
    wire [14:0]        raddr = {4'b0, seq_row, seq_pix};
    wire [3*DEPTH-1:0] rdata;
    wire               store_we = conv_valid && !rst;

    /* verilator lint_off PINCONNECTEMPTY */
    bitplane_store #(
        .DEPTH(DEPTH),
        .WIDTH(WIDTH),
        .HEIGHT(HEIGHT)
    ) store (
        .clk(clk25),
        .we(store_we),
        .waddr(waddr_d),
        .wdata(conv_planes),
        .re(seq_shift),
        .raddr(raddr),
        .rdata(rdata),
        .rvalid()
    );

    // --- dato serie: bitplane actual de R, G y B (placeholder R1 = R2) ------
    // Mux de 5 vías con índices constantes: sin DSP y sin índice variable.
    reg sel_r, sel_g, sel_b;
    always @(*) begin
        case (seq_bp)
            5'd0:    {sel_b, sel_g, sel_r} = rdata[2:0];
            5'd1:    {sel_b, sel_g, sel_r} = rdata[5:3];
            5'd2:    {sel_b, sel_g, sel_r} = rdata[8:6];
            5'd3:    {sel_b, sel_g, sel_r} = rdata[11:9];
            default: {sel_b, sel_g, sel_r} = rdata[14:12];   // bitplane 4
        endcase
    end
    wire [5:0] ser_data = {sel_r, sel_g, sel_b, sel_r, sel_g, sel_b};

    // --- ocho serializadores en lockstep ------------------------------------
    hub75_serializer ser1 (
        .clk(clk25), .shift_en(seq_shift), .data(ser_data),
        .pins({j1_r1, j1_g1, j1_b1, j1_r2, j1_g2, j1_b2}), .clk_out(hub_clk)
    );
    hub75_serializer ser2 (
        .clk(clk25), .shift_en(seq_shift), .data(ser_data),
        .pins({j2_r1, j2_g1, j2_b1, j2_r2, j2_g2, j2_b2}), .clk_out()
    );
    hub75_serializer ser3 (
        .clk(clk25), .shift_en(seq_shift), .data(ser_data),
        .pins({j3_r1, j3_g1, j3_b1, j3_r2, j3_g2, j3_b2}), .clk_out()
    );
    hub75_serializer ser4 (
        .clk(clk25), .shift_en(seq_shift), .data(ser_data),
        .pins({j4_r1, j4_g1, j4_b1, j4_r2, j4_g2, j4_b2}), .clk_out()
    );
    hub75_serializer ser5 (
        .clk(clk25), .shift_en(seq_shift), .data(ser_data),
        .pins({j5_r1, j5_g1, j5_b1, j5_r2, j5_g2, j5_b2}), .clk_out()
    );
    hub75_serializer ser6 (
        .clk(clk25), .shift_en(seq_shift), .data(ser_data),
        .pins({j6_r1, j6_g1, j6_b1, j6_r2, j6_g2, j6_b2}), .clk_out()
    );
    hub75_serializer ser7 (
        .clk(clk25), .shift_en(seq_shift), .data(ser_data),
        .pins({j7_r1, j7_g1, j7_b1, j7_r2, j7_g2, j7_b2}), .clk_out()
    );
    hub75_serializer ser8 (
        .clk(clk25), .shift_en(seq_shift), .data(ser_data),
        .pins({j8_r1, j8_g1, j8_b1, j8_r2, j8_g2, j8_b2}), .clk_out()
    );
    /* verilator lint_on PINCONNECTEMPTY */

    // --- latido de frame para bring-up --------------------------------------
    reg [8:0] heartbeat;
    always @(posedge clk25)
        if (rst)
            heartbeat <= 9'd0;
        else if (seq_frame)
            heartbeat <= heartbeat + 9'd1;

    assign led_t6  = heartbeat[8];   // ~0,7 s por toggle a 388 Hz de frame
    assign led_p11 = heartbeat[8];

    // --- señales compartidas ------------------------------------------------
    // El OE del panel HUB75 es ACTIVO BAJO (docs/08): 0 enciende la fila.
    // seq_oe es display-enable activo alto (1 durante el shift, 0 en el
    // blanking), así que acá se invierte: con esto la fila queda encendida
    // durante el shift y apagada en el blanking/LAT, que es lo correcto.
    assign hub_a   = seq_addr[0];
    assign hub_b   = seq_addr[1];
    assign hub_c   = seq_addr[2];
    assign hub_d   = 1'b0;
    assign hub_e   = 1'b0;
    assign hub_lat = seq_lat;
    assign hub_oe  = ~seq_oe;

endmodule
