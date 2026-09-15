# Driver propio — Colorlight 5A-75B (ECP5-25)
# Bloques de ../docs/11_arquitectura_colorlight_5a75b.md.
# Bloque actual: rgb_to_bitplane contra los vectores del simulador.
# Toolchain: OSS CAD Suite (ver ../TOOLCHAIN.md)

TOP   := rgb_to_bitplane
TB    := tb_rgb_to_bitplane
SRC   := rtl/rgb_to_bitplane.v
SIM   := sim/tb_rgb_to_bitplane.v
VECDIR := ../simulator/vectors
BUILD := build

.PHONY: all sim lint synth stats vectors clean help

all: sim lint

$(BUILD):
	mkdir -p $(BUILD)

# --- Simulacion con vectores dorados -----------------------------------------
sim: $(BUILD)/$(TB).vvp
	vvp $<

$(BUILD)/$(TB).vvp: $(SRC) $(SIM) $(VECDIR)/manifest.json | $(BUILD)
	iverilog -g2012 -Wall -DVECDIR=\"$(VECDIR)/\" -o $@ $(SIM) $(SRC)

# --- Verificacion estatica ---------------------------------------------------
lint:
	verilator --lint-only -Wall --top-module $(TOP) $(SRC)

# --- Sintesis (recursos; sin bitstream: falta el top de placa) ---------------
synth: $(BUILD)/$(TOP).json

$(BUILD)/$(TOP).json: $(SRC) $(VECDIR)/manifest.json | $(BUILD)
	yosys -q -p 'synth_ecp5 -top $(TOP) -json $@' $(SRC)

stats: synth
	@yosys -p 'read_json $(BUILD)/$(TOP).json; stat' 2>&1 | sed -n '/Printing statistics/,$$p'

# --- Vectores (los genera el simulador) --------------------------------------
vectors:
	$(MAKE) -C ../simulator vectors

clean:
	rm -rf $(BUILD)

help:
	@echo "make          - simulacion + lint"
	@echo "make sim      - testbench contra los vectores dorados ($(VECDIR))"
	@echo "make lint     - analisis estatico con verilator"
	@echo "make synth    - sintesis con yosys (recursos, sin bitstream)"
	@echo "make stats    - recursos tras sintesis"
	@echo "make vectors  - regenera los vectores con el simulador"
	@echo "make clean    - borra artefactos"
