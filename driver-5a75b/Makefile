# Driver propio — Colorlight 5A-75B (ECP5-25)
# Bloques de ../docs/11_arquitectura_colorlight_5a75b.md.
# Toolchain: OSS CAD Suite (ver ../TOOLCHAIN.md)

VECDIR := ../simulator/vectors
BUILD  := build

SYNTH := rgb_to_bitplane bcm_sequencer hub75_serializer bitplane_store

RTL     := rtl/rgb_to_bitplane.v rtl/bcm_sequencer.v rtl/hub75_serializer.v rtl/bitplane_store.v rtl/top.v
LPF     := constraints/colorlight_5a75b_v8.lpf
DEVICE  := 25k
PACKAGE := CABGA256
SPEED   := 6
CABLE   := dirtyJtag

.PHONY: all sim lint synth stats vectors bitstream prog clean help

all: sim lint

$(BUILD):
	mkdir -p $(BUILD)

# --- Simulacion --------------------------------------------------------------
# tb_rgb_to_bitplane: contra los vectores dorados del simulador.
# tb_hub75_timing:    invariantes de temporizacion BCM/HUB75.
# tb_bitplane_store:  cadena conversor -> store -> lectura.
# tb_top:             integracion completa y lockstep de los 8 puertos.
sim: $(BUILD)/tb_rgb_to_bitplane.vvp $(BUILD)/tb_hub75_timing.vvp $(BUILD)/tb_bitplane_store.vvp $(BUILD)/tb_top.vvp
	vvp $(BUILD)/tb_rgb_to_bitplane.vvp
	vvp $(BUILD)/tb_hub75_timing.vvp
	vvp $(BUILD)/tb_bitplane_store.vvp
	vvp $(BUILD)/tb_top.vvp

$(BUILD)/tb_rgb_to_bitplane.vvp: sim/tb_rgb_to_bitplane.v rtl/rgb_to_bitplane.v $(VECDIR)/manifest.json | $(BUILD)
	iverilog -g2012 -Wall -DVECDIR=\"$(VECDIR)/\" -o $@ sim/tb_rgb_to_bitplane.v rtl/rgb_to_bitplane.v

$(BUILD)/tb_hub75_timing.vvp: sim/tb_hub75_timing.v rtl/bcm_sequencer.v rtl/hub75_serializer.v | $(BUILD)
	iverilog -g2012 -Wall -o $@ sim/tb_hub75_timing.v rtl/bcm_sequencer.v rtl/hub75_serializer.v

$(BUILD)/tb_bitplane_store.vvp: sim/tb_bitplane_store.v rtl/rgb_to_bitplane.v rtl/bitplane_store.v $(VECDIR)/manifest.json | $(BUILD)
	iverilog -g2012 -Wall -DVECDIR=\"$(VECDIR)/\" -o $@ sim/tb_bitplane_store.v rtl/rgb_to_bitplane.v rtl/bitplane_store.v

$(BUILD)/tb_top.vvp: sim/tb_top.v $(RTL) $(VECDIR)/manifest.json | $(BUILD)
	iverilog -g2012 -Wall -o $@ sim/tb_top.v $(RTL)

# --- Verificacion estatica ---------------------------------------------------
lint:
	verilator --lint-only -Wall --top-module rgb_to_bitplane rtl/rgb_to_bitplane.v
	verilator --lint-only -Wall --top-module bcm_sequencer rtl/bcm_sequencer.v
	verilator --lint-only -Wall --top-module hub75_serializer rtl/hub75_serializer.v
	verilator --lint-only -Wall --top-module bitplane_store rtl/bitplane_store.v
	verilator --lint-only -Wall --top-module top $(RTL)

# --- Sintesis (recursos; sin bitstream: falta el top de placa) ---------------
synth: $(addprefix $(BUILD)/,$(addsuffix .json,$(SYNTH)))

$(BUILD)/rgb_to_bitplane.json: rtl/rgb_to_bitplane.v $(VECDIR)/manifest.json | $(BUILD)
	yosys -q -p 'synth_ecp5 -top rgb_to_bitplane -json $@' rtl/rgb_to_bitplane.v

$(BUILD)/bcm_sequencer.json: rtl/bcm_sequencer.v | $(BUILD)
	yosys -q -p 'synth_ecp5 -top bcm_sequencer -json $@' rtl/bcm_sequencer.v

$(BUILD)/hub75_serializer.json: rtl/hub75_serializer.v | $(BUILD)
	yosys -q -p 'synth_ecp5 -top hub75_serializer -json $@' rtl/hub75_serializer.v

$(BUILD)/bitplane_store.json: rtl/bitplane_store.v | $(BUILD)
	yosys -q -p 'synth_ecp5 -top bitplane_store -json $@' rtl/bitplane_store.v

stats: synth $(BUILD)/top.json
	@for m in $(SYNTH) top; do \
	  echo "=== $$m"; \
	  yosys -p "read_json $(BUILD)/$$m.json; stat" 2>&1 \
	    | sed -n '/Printing statistics/,/End of script/p' | sed '$$d'; \
	done

# --- Bitstream del top de integracion ----------------------------------------
bitstream: $(BUILD)/top.bit

$(BUILD)/top.json: $(RTL) $(VECDIR)/manifest.json | $(BUILD)
	yosys -q -p 'synth_ecp5 -top top -json $@' $(RTL)

$(BUILD)/top.config: $(BUILD)/top.json $(LPF)
	nextpnr-ecp5 --$(DEVICE) --package $(PACKAGE) --speed $(SPEED) \
	  --json $< --lpf $(LPF) --textcfg $@

$(BUILD)/top.bit: $(BUILD)/top.config
	ecppack --compress $< $@

# Solo SRAM: la SPI flash no se toca hasta respaldar el bitstream de fábrica
# (ver ../docs/11_arquitectura_colorlight_5a75b.md).
prog: $(BUILD)/top.bit
	openFPGALoader -c $(CABLE) $<

# --- Vectores (los genera el simulador) --------------------------------------
vectors:
	$(MAKE) -C ../simulator vectors

clean:
	rm -rf $(BUILD)

help:
	@echo "make          - simulacion + lint"
	@echo "make sim      - los 4 testbenches: vectores, temporizacion, store y top"
	@echo "make lint     - analisis estatico con verilator (bloques + top)"
	@echo "make synth    - sintesis con yosys (recursos por bloque y del top)"
	@echo "make stats    - recursos tras sintesis"
	@echo "make bitstream- bitstream del top de integracion (top.bit)"
	@echo "make prog     - carga a SRAM por JTAG (volatil); CABLE=$(CABLE)"
	@echo "make vectors  - regenera los vectores con el simulador"
	@echo "make clean    - borra artefactos"
