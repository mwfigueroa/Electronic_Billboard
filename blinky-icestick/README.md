# Blinky — Lattice iCEstick

Proyecto de prueba para validar el toolchain de OSS CAD Suite de punta a punta:
síntesis, place & route, bitstream, simulación, lint y timing.

**Placa:** iCEstick (iCE40HX1K-TQ144, oscilador de 12 MHz)

## Qué hace

- **D5** (verde, centro) parpadea a 1 Hz.
- **D1..D4** (rojos, exteriores) rotan un `1` a la misma cadencia.

## Uso

```bash
make          # sintetiza y genera build/blinky.bin
make sim      # simula el testbench con iverilog  -> "PASS: 19 comprobaciones"
make wave     # simula y abre GTKWave
make lint     # verilator -Wall
make timing   # reporte de icetime
make stats    # recursos usados tras síntesis
make prog     # carga a SRAM (volátil, se pierde al desconectar)
make flash    # graba en la SPI flash (persiste)
make clean
```

`make help` resume lo mismo.

## Estructura

```
rtl/top.v                 diseño
constraints/icestick.pcf  asignación de pines
sim/tb_top.v              testbench
Makefile                  flujo completo
build/                    artefactos (ignorado por git)
```

## Resultados de la última corrida

Síntesis (`make stats`):

```
83 cells:  34 SB_LUT4, 23 SB_DFFSR, 21 SB_CARRY, 5 SB_DFFE
```

Place & route: los 6 puertos quedaron fijados a sus bels y la frecuencia máxima
del reloj es **201.09 MHz** contra la restricción de 12.00 MHz — margen amplio,
como corresponde a un contador.

Timing (`make timing`, icetime): camino crítico de 6.48 ns (154.27 MHz),
6 niveles de lógica, restricción de 83.33 ns **PASSED**.

Lint (`make lint`): limpio.

## Notas de diseño

**Parámetros para simular.** `top` toma `CLK_HZ` y `BLINK_HZ`. El testbench lo
instancia con `CLK_HZ=1000, BLINK_HZ=100` para que cada paso sean 5 ciclos en
vez de 6 millones; así la simulación termina en microsegundos.

**Sin reset.** Los registros se declaran con valor inicial (`reg [3:0] ring =
4'b0001`). En iCE40 el estado inicial de los flip-flops forma parte del
bitstream, así que es la forma idiomática y ahorra lógica. Por eso el Makefile
pasa `-Wno-PROCASSINIT` a verilator: su advertencia asume un flujo ASIC donde
esto no sintetiza.

**Anchos explícitos.** `LAST` y `ONE` son `localparam` de `W` bits para que el
comparador y el sumador no se extiendan a 32 bits. El truncado de 32 a `W` bits
lleva un `lint_off WIDTHTRUNC` acotado: es seguro por construcción, ya que
`W = $clog2(TICKS)`.

## Programación en WSL2

`make prog` necesita ver el FTDI de la placa. Desde Windows:

```powershell
usbipd list                      # localizar el "Lattice FTUSB Interface"
usbipd attach --wsl --busid <N>  # exponerlo a la distro
```

Las reglas udev y el grupo `plugdev` ya están configurados (ver `../TOOLCHAIN.md`).
