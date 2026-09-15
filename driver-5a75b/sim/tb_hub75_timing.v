// Testbench de temporización HUB75: bcm_sequencer + hub75_serializer
//
// Verifica, sobre un frame completo (5 bits, 12,5 MHz):
//   - 256 clocks de shift por paso de dirección, 8 pasos por pasada
//   - un pulso de LAT por paso, siempre con OE en bajo
//   - OE en bajo en cada cambio de dirección y de fila de datos, con un
//     clock de asentamiento (criterio de docs/11)
//   - peso BCM: 1, 2, 4, 8 y 16 pasadas por bitplane
//   - frame de (2^DEPTH-1) x 8 x (SHIFT+BLANK) clocks y refresco >= 192 Hz
//   - el serializador registra los datos y gatea CLK en el blanking
//
// El monitor muestrea 1 ns después del flanco (valores ya asentados), así
// los cambios se detectan en el mismo flanco en que ocurren.
//
// No valida el mapeo de píxeles: eso es del scan_mapper (Paso 2, con panel).

`timescale 1ns / 1ps

module tb_hub75_timing;

    localparam integer DEPTH          = 5;
    localparam integer SHIFT_CLOCKS   = 256;
    localparam integer BLANK_CLOCKS   = 4;
    localparam integer STEPS_PER_PASS = 8;
    localparam integer PASSES         = (1 << DEPTH) - 1;
    localparam integer EXP_FRAME_CLOCKS =
        PASSES * STEPS_PER_PASS * (SHIFT_CLOCKS + BLANK_CLOCKS);
    localparam real    CLK_HZ = 12.5e6;
    localparam real    CLK_NS = 1.0e9 / CLK_HZ;   // 80 ns
    localparam real    MIN_HZ = 192.0;            // criterio docs/11

    reg clk = 0;
    always #(CLK_NS / 2.0) clk = ~clk;

    reg rst = 1;
    initial #(CLK_NS * 5) rst = 0;

    wire [2:0]       addr, row;
    wire [DEPTH-1:0] bitplane;
    wire [7:0]       pix;
    wire             shift_en, lat, oe, frame_start;

    bcm_sequencer #(
        .DEPTH(DEPTH),
        .SHIFT_CLOCKS(SHIFT_CLOCKS),
        .BLANK_CLOCKS(BLANK_CLOCKS)
    ) dut_seq (
        .clk(clk),
        .rst(rst),
        .addr(addr),
        .row(row),
        .bitplane(bitplane),
        .pix(pix),
        .shift_en(shift_en),
        .lat(lat),
        .oe(oe),
        .frame_start(frame_start)
    );

    wire [5:0] pins;
    wire       clk_out;

    hub75_serializer dut_ser (
        .clk(clk),
        .shift_en(shift_en),
        .data(pix[5:0]),
        .pins(pins),
        .clk_out(clk_out)
    );

    integer fails = 0;
    integer clk_edges = 0;
    integer lats_in_pass = 0;
    integer passes_in_bp = 0;
    integer frames_seen = 0;
    integer t_frame0 = 0;
    integer frame_clocks = 0;

    reg [2:0]       addr_q = 3'd7;
    reg [2:0]       row_q  = 3'd0;
    reg [DEPTH-1:0] bp_q   = 0;
    reg             lat_q  = 0;
    reg             oe_q   = 0;
    reg             check_pins = 0;
    reg [5:0]       exp_pins = 0;

    always @(posedge clk_out)
        clk_edges = clk_edges + 1;

    always @(posedge clk) begin
        #1;   // valores post-flanco, ya asentados

        if (!rst) begin
            // --- invariantes de OE (docs/11) --------------------------------
            if (lat && oe) begin
                fails = fails + 1;
                $display("FALLA [%0t]: LAT con OE activo", $time);
            end
            if (lat_q && oe) begin
                fails = fails + 1;
                $display("FALLA [%0t]: OE sigue activo tras LAT", $time);
            end
            if ((addr !== addr_q) && (oe || oe_q)) begin
                fails = fails + 1;
                $display("FALLA [%0t]: cambio de direccion con OE activo", $time);
            end
            if ((row !== row_q) && (oe || oe_q)) begin
                fails = fails + 1;
                $display("FALLA [%0t]: cambio de fila de datos con OE activo", $time);
            end

            // --- serializador: pins registra data un clock ----------------
            if (check_pins) begin
                check_pins = 0;
                if (pins !== exp_pins) begin
                    fails = fails + 1;
                    $display("FALLA [%0t]: pins=%b esperado=%b", $time, pins, exp_pins);
                end
            end
            exp_pins = pix[5:0];
            check_pins = shift_en;   // el latch ocurre en el proximo flanco

            // --- conteos por paso, pasada y bitplane ------------------------
            if (lat)
                lats_in_pass = lats_in_pass + 1;

            if (row !== row_q) begin
                if (clk_edges != SHIFT_CLOCKS) begin
                    fails = fails + 1;
                    $display("FALLA [%0t]: paso con %0d clocks de shift (esperado %0d)",
                             $time, clk_edges, SHIFT_CLOCKS);
                end
                clk_edges = 0;
                if (row_q == 3'd7) begin
                    passes_in_bp = passes_in_bp + 1;
                    if (lats_in_pass != STEPS_PER_PASS) begin
                        fails = fails + 1;
                        $display("FALLA [%0t]: pasada con %0d LAT (esperado %0d)",
                                 $time, lats_in_pass, STEPS_PER_PASS);
                    end
                    lats_in_pass = 0;
                end
            end

            if (bitplane !== bp_q) begin
                if (passes_in_bp != (1 << bp_q)) begin
                    fails = fails + 1;
                    $display("FALLA [%0t]: bitplane %0d con %0d pasadas (esperado %0d)",
                             $time, bp_q, passes_in_bp, 1 << bp_q);
                end
                passes_in_bp = 0;
            end

            // --- frame -------------------------------------------------------
            if (frame_start) begin
                frames_seen = frames_seen + 1;
                if (frames_seen == 2) begin
                    t_frame0 = $time;
                end else if (frames_seen == 3) begin
                    frame_clocks = ($time - t_frame0) / CLK_NS;
                    if (frame_clocks != EXP_FRAME_CLOCKS) begin
                        fails = fails + 1;
                        $display("FALLA: frame de %0d clocks (esperado %0d)",
                                 frame_clocks, EXP_FRAME_CLOCKS);
                    end
                    $display("frame: %0d clocks · refresco %.1f Hz a %0.1f MHz",
                             frame_clocks, CLK_HZ / frame_clocks, CLK_HZ / 1.0e6);
                    if ((CLK_HZ / frame_clocks) < MIN_HZ) begin
                        fails = fails + 1;
                        $display("FALLA: refresco por debajo de %.0f Hz", MIN_HZ);
                    end
                    if (fails == 0) begin
                        $display("PASS: temporizacion BCM/HUB75 dentro de lo esperado");
                        $finish;
                    end
                    $fatal(1, "FALLA: %0d fallas de temporizacion", fails);
                end
            end

            addr_q = addr;
            row_q  = row;
            lat_q  = lat;
            oe_q   = oe;
            bp_q   = bitplane;
        end
    end

endmodule
