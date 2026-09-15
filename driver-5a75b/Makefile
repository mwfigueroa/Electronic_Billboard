# Driver propio — Colorlight 5A-75B (ECP5-25)
# Bloques de ../docs/11_arquitectura_colorlight_5a75b.md.
# Toolchain: OSS CAD Suite (ver ../TOOLCHAIN.md)

VECDIR := ../simulator/vectors
BUILD  := build

SYNTH := rgb_to_bitplane bcm_sequencer hub75_serializer

.PHONY: all sim lint synth stats vectors clean help

all: sim lint

$(BUILD):
	mkdir -p $(BUILD)

# --- Simulacion --------------------------------------------------------------
# tb_rgb_to_bitplane: contra los vectores dorados del simulador.
# tb_hub75_timing:    invariantes de temporizacion BCM/HUB75.
sim: $(BUILD)/tb_rgb_to_bitplane.vvp $(BUILD)/tb_hub75_timing.vvp
	vvp $(BUILD)/tb_rgb_to_bitplane.vvp
	vvp $(BUILD)/tb_hub75_timing.vvp

$(BUILD)/tb_rgb_to_bitplane.vvp: sim/tb_rgb_to_bitplane.v rtl/rgb_to_bitplane.v $(VECDIR)/manifest.json | $(BUILD)
	iverilog -g2012 -Wall -DVECDIR=\"$(VECDIR)/\" -o $@ sim/tb_rgb_to_bitplane.v rtl/rgb_to_bitplane.v

$(BUILD)/tb_hub75_timing.vvp: sim/tb_hub75_timing.v rtl/bcm_sequencer.v rtl/hub75_serializer.v | $(BUILD)
	iverilog -g2012 -Wall -o $@ sim/tb_hub75_timing.v rtl/bcm_sequencer.v rtl/hub75_serializer.v

# --- Verificacion estatica ---------------------------------------------------
lint:
	verilator --lint-only -Wall --top-module rgb_to_bitplane rtl/rgb_to_bitplane.v
	verilator --lint-only -Wall --top-module bcm_sequencer rtl/bcm_sequencer.v
	verilator --lint-only -Wall --top-module hub75_serializer rtl/hub75_serializer.v

# --- Sintesis (recursos; sin bitstream: falta el top de placa) ---------------
synth: $(addprefix $(BUILD)/,$(addsuffix .json,$(SYNTH)))

$(BUILD)/rgb_to_bitplane.json: rtl/rgb_to_bitplane.v $(VECDIR)/manifest.json | $(BUILD)
	yosys -q -p 'synth_ecp5 -top rgb_to_bitplane -json $@' rtl/rgb_to_bitplane.v

$(BUILD)/bcm_sequencer.json: rtl/bcm_sequencer.v | $(BUILD)
	yosys -q -p 'synth_ecp5 -top bcm_sequencer -json $@' rtl/bcm_sequencer.v

$(BUILD)/hub75_serializer.json: rtl/hub75_serializer.v | $(BUILD)
	yosys -q -p 'synth_ecp5 -top hub75_serializer -json $@' rtl/hub75_serializer.v

stats: synth
	@for m in $(SYNTH); do \
	  echo "=== $$m"; \
	  yosys -p "read_json $(BUILD)/$$m.json; stat" 2>&1 \
	    | sed -n '/Printing statistics/,/End of script/p' | sed '$$d'; \
	done

# --- Vectores (los genera el simulador) --------------------------------------
vectors:
	$(MAKE) -C ../simulator vectors

clean:
	rm -rf $(BUILD)

help:
	@echo "make          - simulacion + lint"
	@echo "make sim      - testbenches: rgb_to_bitplane (vectores) y temporizacion HUB75"
	@echo "make lint     - analisis estatico con verilator (3 bloques)"
	@echo "make synth    - sintesis con yosys (recursos, sin bitstream)"
	@echo "make stats    - recursos tras sintesis"
	@echo "make vectors  - regenera los vectores con el simulador"
	@echo "make clean    - borra artefactos"
