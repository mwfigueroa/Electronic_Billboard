# Blinky / Paso 0 de bring-up — Colorlight 5A-75B rev 8.0
# Toolchain: OSS CAD Suite (ver ../TOOLCHAIN.md)
# Arquitectura y plan: ../docs/11_arquitectura_colorlight_5a75b.md

PROJ    := blinky
TOP     := top
DEVICE  := 25k
PACKAGE := CABGA256
SPEED   := 6
CABLE   := dirtyJtag

SRC := rtl/blink_div.v rtl/top.v
LPF := constraints/colorlight_5a75b_v8.lpf
TB  := sim/tb_top.v

BUILD := build

.PHONY: all clean prog sim wave lint stats help

all: $(BUILD)/$(PROJ).bit

$(BUILD):
	mkdir -p $(BUILD)

# --- Sintesis ---------------------------------------------------------------
$(BUILD)/$(PROJ).json: $(SRC) | $(BUILD)
	yosys -q -p 'synth_ecp5 -top $(TOP) -json $@' $(SRC)

# --- Place & route ----------------------------------------------------------
$(BUILD)/$(PROJ).config: $(BUILD)/$(PROJ).json $(LPF)
	nextpnr-ecp5 --$(DEVICE) --package $(PACKAGE) --speed $(SPEED) \
	  --json $< --lpf $(LPF) --textcfg $@ -q

# --- Bitstream --------------------------------------------------------------
$(BUILD)/$(PROJ).bit: $(BUILD)/$(PROJ).config
	ecppack --compress $< $@

# --- Programacion -----------------------------------------------------------
# Solo SRAM. NO hay objetivo de flash a proposito: durante el bring-up no se
# escribe la SPI flash, y el bitstream de fabrica debe estar respaldado antes
# de siquiera considerarlo. Ver ../docs/11_arquitectura_colorlight_5a75b.md.
prog: $(BUILD)/$(PROJ).bit
	openFPGALoader -c $(CABLE) $<

# --- Verificacion -----------------------------------------------------------
sim: $(BUILD)/tb_top.vvp
	vvp $<

$(BUILD)/tb_top.vvp: $(SRC) $(TB) | $(BUILD)
	iverilog -g2012 -Wall -o $@ $(TB) $(SRC)

wave: sim
	gtkwave sim/tb_top.vcd

lint:
	verilator --lint-only -Wall -Wno-PROCASSINIT --top-module $(TOP) $(SRC)

stats: $(BUILD)/$(PROJ).json
	@yosys -p 'read_json $<; stat' 2>&1 | sed -n '/Printing statistics/,$$p'

clean:
	rm -rf $(BUILD) sim/tb_top.vcd

help:
	@echo "make          - sintetiza y genera build/$(PROJ).bit"
	@echo "make sim      - simula el testbench con iverilog"
	@echo "make wave     - simula y abre GTKWave"
	@echo "make lint     - analisis estatico con verilator"
	@echo "make stats    - recursos usados tras sintesis"
	@echo "make prog     - carga a SRAM por JTAG (volatil)"
	@echo "make clean    - borra artefactos"
	@echo ""
	@echo "CABLE=$(CABLE) — cambiar si se usa otro adaptador JTAG:"
	@echo "  make prog CABLE=ft2232"
