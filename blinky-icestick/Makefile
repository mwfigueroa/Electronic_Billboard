# Blinky iCEstick — iCE40HX1K-TQ144
# Toolchain: OSS CAD Suite (ver ../TOOLCHAIN.md)

PROJ     := blinky
TOP      := top
DEVICE   := hx1k
PACKAGE  := tq144
FREQ_MHZ := 12

SRC := rtl/top.v
PCF := constraints/icestick.pcf
TB  := sim/tb_top.v

BUILD := build

.PHONY: all clean prog flash sim lint timing stats help

all: $(BUILD)/$(PROJ).bin

$(BUILD):
	mkdir -p $(BUILD)

# --- Sintesis ---------------------------------------------------------------
$(BUILD)/$(PROJ).json: $(SRC) | $(BUILD)
	yosys -q -p 'synth_ice40 -top $(TOP) -json $@' $(SRC)

# --- Place & route ----------------------------------------------------------
$(BUILD)/$(PROJ).asc: $(BUILD)/$(PROJ).json $(PCF)
	nextpnr-ice40 --$(DEVICE) --package $(PACKAGE) \
	  --json $< --pcf $(PCF) --asc $@ \
	  --freq $(FREQ_MHZ) -q

# --- Bitstream --------------------------------------------------------------
$(BUILD)/$(PROJ).bin: $(BUILD)/$(PROJ).asc
	icepack $< $@

# --- Programacion -----------------------------------------------------------
# prog  = SRAM, volatil, se pierde al desconectar (iteracion rapida)
# flash = SPI flash, persiste tras el power cycle
prog: $(BUILD)/$(PROJ).bin
	iceprog -S $<

flash: $(BUILD)/$(PROJ).bin
	iceprog $<

# --- Verificacion -----------------------------------------------------------
sim: $(BUILD)/tb_top.vvp
	vvp $<

$(BUILD)/tb_top.vvp: $(SRC) $(TB) | $(BUILD)
	iverilog -g2012 -Wall -o $@ $(TB) $(SRC)

wave: sim
	gtkwave sim/tb_top.vcd

lint:
	verilator --lint-only -Wall -Wno-PROCASSINIT --top-module $(TOP) $(SRC)

timing: $(BUILD)/$(PROJ).asc
	icetime -d $(DEVICE) -P $(PACKAGE) -c $(FREQ_MHZ) -t $<

stats: $(BUILD)/$(PROJ).json
	@yosys -p 'read_json $<; stat' 2>&1 | sed -n '/Printing statistics/,$$p'

clean:
	rm -rf $(BUILD) sim/tb_top.vcd

help:
	@echo "make          - sintetiza y genera build/$(PROJ).bin"
	@echo "make sim      - simula el testbench con iverilog"
	@echo "make wave     - simula y abre GTKWave"
	@echo "make lint     - analisis estatico con verilator"
	@echo "make timing   - reporte de timing con icetime"
	@echo "make stats    - recursos usados tras sintesis"
	@echo "make prog     - carga a SRAM (volatil)"
	@echo "make flash    - graba en la SPI flash (persistente)"
	@echo "make clean    - borra artefactos"
