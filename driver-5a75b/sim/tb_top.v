// Testbench de integración del top: cadena completa y lockstep
//
// Verifica, corriendo el top real a 25 MHz:
//   - el patrón se escribe una vez: 32768 palabras en el store
//   - los ocho serializadores van en lockstep (mismos 6 bits siempre)
//   - el stream serie de cada puerto es el bitplane actual del store
//     (con la latencia de lectura + registro del serializador)
//   - D/E quedan en bajo (sin uso en scan 1/8)
//
// No valida el mapeo de scan: el top usa un placeholder (y = row, x = pix).

`timescale 1ns / 1ps

module tb_top;

    localparam integer DEPTH    = 5;
    localparam integer W        = 256;
    localparam integer H        = 128;
    localparam integer PIXELS   = W * H;
    localparam real    CLK_NS   = 40.0;     // 25 MHz

    reg clk = 0;
    always #(CLK_NS / 2.0) clk = ~clk;

    reg btn_n = 0;
    initial #(CLK_NS * 5) btn_n = 1;

    wire led_t6, led_p11;
    wire hub_a, hub_b, hub_c, hub_d, hub_e, hub_clk, hub_lat, hub_oe;
    wire j1_r1, j1_g1, j1_b1, j1_r2, j1_g2, j1_b2;
    wire j2_r1, j2_g1, j2_b1, j2_r2, j2_g2, j2_b2;
    wire j3_r1, j3_g1, j3_b1, j3_r2, j3_g2, j3_b2;
    wire j4_r1, j4_g1, j4_b1, j4_r2, j4_g2, j4_b2;
    wire j5_r1, j5_g1, j5_b1, j5_r2, j5_g2, j5_b2;
    wire j6_r1, j6_g1, j6_b1, j6_r2, j6_g2, j6_b2;
    wire j7_r1, j7_g1, j7_b1, j7_r2, j7_g2, j7_b2;
    wire j8_r1, j8_g1, j8_b1, j8_r2, j8_g2, j8_b2;

    top u_top (
        .clk25(clk),
        .btn_n(btn_n),
        .led_t6(led_t6),
        .led_p11(led_p11),
        .hub_a(hub_a),
        .hub_b(hub_b),
        .hub_c(hub_c),
        .hub_d(hub_d),
        .hub_e(hub_e),
        .hub_clk(hub_clk),
        .hub_lat(hub_lat),
        .hub_oe(hub_oe),
        .j1_r1(j1_r1), .j1_g1(j1_g1), .j1_b1(j1_b1),
        .j1_r2(j1_r2), .j1_g2(j1_g2), .j1_b2(j1_b2),
        .j2_r1(j2_r1), .j2_g1(j2_g1), .j2_b1(j2_b1),
        .j2_r2(j2_r2), .j2_g2(j2_g2), .j2_b2(j2_b2),
        .j3_r1(j3_r1), .j3_g1(j3_g1), .j3_b1(j3_b1),
        .j3_r2(j3_r2), .j3_g2(j3_g2), .j3_b2(j3_b2),
        .j4_r1(j4_r1), .j4_g1(j4_g1), .j4_b1(j4_b1),
        .j4_r2(j4_r2), .j4_g2(j4_g2), .j4_b2(j4_b2),
        .j5_r1(j5_r1), .j5_g1(j5_g1), .j5_b1(j5_b1),
        .j5_r2(j5_r2), .j5_g2(j5_g2), .j5_b2(j5_b2),
        .j6_r1(j6_r1), .j6_g1(j6_g1), .j6_b1(j6_b1),
        .j6_r2(j6_r2), .j6_g2(j6_g2), .j6_b2(j6_b2),
        .j7_r1(j7_r1), .j7_g1(j7_g1), .j7_b1(j7_b1),
        .j7_r2(j7_r2), .j7_g2(j7_g2), .j7_b2(j7_b2),
        .j8_r1(j8_r1), .j8_g1(j8_g1), .j8_b1(j8_b1),
        .j8_r2(j8_r2), .j8_g2(j8_g2), .j8_b2(j8_b2)
    );

    wire [5:0] p1 = {j1_r1, j1_g1, j1_b1, j1_r2, j1_g2, j1_b2};
    wire [5:0] p2 = {j2_r1, j2_g1, j2_b1, j2_r2, j2_g2, j2_b2};
    wire [5:0] p3 = {j3_r1, j3_g1, j3_b1, j3_r2, j3_g2, j3_b2};
    wire [5:0] p4 = {j4_r1, j4_g1, j4_b1, j4_r2, j4_g2, j4_b2};
    wire [5:0] p5 = {j5_r1, j5_g1, j5_b1, j5_r2, j5_g2, j5_b2};
    wire [5:0] p6 = {j6_r1, j6_g1, j6_b1, j6_r2, j6_g2, j6_b2};
    wire [5:0] p7 = {j7_r1, j7_g1, j7_b1, j7_r2, j7_g2, j7_b2};
    wire [5:0] p8 = {j8_r1, j8_g1, j8_b1, j8_r2, j8_g2, j8_b2};

    integer writes = 0;
    integer fails = 0;
    integer lockstep_checks = 0;
    integer frames = 0;

    always @(posedge clk)
        if (u_top.store_we)
            writes = writes + 1;

    always @(posedge clk)
        if (u_top.seq_frame)
            frames = frames + 1;

    // stream esperado: el serializador registra el dato del clock anterior.
    // Mismo mux que el top (3*bitplane), calculado para el chequeo.
    wire [3:0] bp3 = (u_top.seq_bp[3:0] << 1) + u_top.seq_bp[3:0];
    wire [5:0] cur = {
        u_top.rdata[bp3], u_top.rdata[bp3 + 4'd1], u_top.rdata[bp3 + 4'd2],
        u_top.rdata[bp3], u_top.rdata[bp3 + 4'd1], u_top.rdata[bp3 + 4'd2]
    };
    reg [5:0] exp_data = 0;
    reg       check = 0;

    always @(posedge clk) begin
        #1;
        if (!btn_n) begin
            check = 0;
        end else begin
            lockstep_checks = lockstep_checks + 1;

            if (p2 !== p1 || p3 !== p1 || p4 !== p1 ||
                p5 !== p1 || p6 !== p1 || p7 !== p1 || p8 !== p1) begin
                fails = fails + 1;
                if (fails <= 10)
                    $display("FALLA [%0t]: puertos fuera de lockstep: %b %b %b %b %b %b %b %b",
                             $time, p1, p2, p3, p4, p5, p6, p7, p8);
            end

            if (check) begin
                check = 0;
                if (p1 !== exp_data) begin
                    fails = fails + 1;
                    if (fails <= 10)
                        $display("FALLA [%0t]: stream p1=%b esperado=%b", $time, p1, exp_data);
                end
            end
            if (u_top.seq_shift) begin
                exp_data = cur;
                check = 1;
            end

            if (hub_d !== 1'b0 || hub_e !== 1'b0) begin
                fails = fails + 1;
                if (fails <= 10)
                    $display("FALLA [%0t]: D/E no estan en bajo", $time);
            end

            // OE del panel: activo bajo. En el pin debe estar en 0 (fila
            // encendida) durante el shift —salvo el clock de asentamiento,
            // fase 0— y en 1 (apagada) con LAT.
            if (hub_oe !== ~u_top.seq_oe) begin
                fails = fails + 1;
                if (fails <= 10)
                    $display("FALLA [%0t]: hub_oe no es ~seq_oe", $time);
            end
            if (u_top.seq_shift && u_top.seq.phase != 9'd0 && hub_oe !== 1'b0) begin
                fails = fails + 1;
                if (fails <= 10)
                    $display("FALLA [%0t]: fila apagada durante el shift", $time);
            end
            if (u_top.seq_lat && hub_oe !== 1'b1) begin
                fails = fails + 1;
                if (fails <= 10)
                    $display("FALLA [%0t]: LAT con la fila encendida (ghosting)", $time);
            end

            if (led_t6 !== led_p11) begin
                fails = fails + 1;
                if (fails <= 10)
                    $display("FALLA [%0t]: LEDs en desacuerdo", $time);
            end
        end
    end

    initial begin
        // las escrituras del patrón terminan poco después de PIXELS clocks
        #(CLK_NS * (PIXELS + 20));
        if (writes != PIXELS) begin
            fails = fails + 1;
            $display("FALLA: escrituras %0d (esperado %0d)", writes, PIXELS);
        end else begin
            $display("patron escrito: %0d palabras", writes);
        end

        // poco más de un frame de 64480 clocks
        #(CLK_NS * 70000);

        if (frames == 0) begin
            fails = fails + 1;
            $display("FALLA: no hubo frame_start");
        end else if (u_top.heartbeat !== frames[8:0]) begin
            fails = fails + 1;
            $display("FALLA: latido %0d distinto de frames %0d", u_top.heartbeat, frames);
        end

        $display("frames: %0d · chequeos de lockstep: %0d · fallas: %0d",
                 frames, lockstep_checks, fails);
        if (fails == 0) begin
            $display("PASS: top integra la cadena y los 8 puertos van en lockstep");
            $finish;
        end
        $fatal(1, "FALLA: %0d fallas en el top", fails);
    end

endmodule
