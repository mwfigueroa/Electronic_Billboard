# Blinky — Colorlight 5A-75B (rev 8.0)

**Paso 0 del bring-up** definido en
[`../docs/11_arquitectura_colorlight_5a75b.md`](../docs/11_arquitectura_colorlight_5a75b.md):
*"cargar un bitstream de blink por JTAG (sin tocar la flash) para validar el flujo"*.

**FPGA:** Lattice ECP5 LFE5U-25F-6BG256C · CABGA256 · speed 6
**Reloj:** 25 MHz en `P6`, generados por el PHY U13

## Para qué sirve

Dos objetivos, no uno:

1. **Validar el flujo completo** `yosys → nextpnr-ecp5 → ecppack → openFPGALoader`
   contra hardware real, cargando solo a SRAM.

2. **Resolver la discrepancia del pin del LED de usuario.** La sección 7 de
   [`../docs/12_referencias_tecnicas.md`](../docs/12_referencias_tecnicas.md) la
   marca como pendiente de verificar: chubby75 indica `T6`, la guía de weigu
   indica `P11`. El diseño maneja **los dos pines a frecuencias distintas**, así
   que una sola carga lo resuelve por observación:

   | Lo que se ve | Conclusión |
   |---|---|
   | Parpadeo lento, ~1 Hz | El LED está en **T6** (chubby75 acierta) |
   | Parpadeo rápido, ~4 Hz | El LED está en **P11** (weigu acierta) |
   | Nada parpadea | Ninguna de las dos fuentes acierta para esta placa |

   Y la **polaridad** sale del botón (`R7`, activo bajo): mientras se lo mantiene
   presionado, ambas salidas se fuerzan a `0`. Si con eso el LED se enciende fijo,
   es activo bajo (`user_led_n`, como lo nombra litex-boards); si se apaga, es
   activo alto.

Anotar el resultado en el checklist de la sección 7 del doc 12.

## Uso

```bash
make          # sintetiza y genera build/blinky.bit
make sim      # testbench con iverilog -> "PASS: sin errores"
make wave     # simula y abre GTKWave
make lint     # verilator -Wall
make stats    # recursos tras síntesis
make prog     # carga a SRAM por JTAG
make clean
```

El adaptador JTAG por defecto es `dirtyJtag` (Raspberry Pi Pico con ese
firmware, la opción de ~USD 5 del doc 12). Para otro:

```bash
make prog CABLE=ft2232
```

## No hay `make flash`

Es deliberado. El doc 11 lo dice en su primera advertencia: la placa arranca
desde su SPI flash con el bitstream de fábrica, y **no se sobrescribe sin
respaldo previo**. Durante todo el bring-up se carga solo a SRAM. Cuando llegue
el momento de grabar la flash, será con el volcado de fábrica ya hecho y
verificado, y con el comando escrito a conciencia — no con un objetivo de
Makefile que se pueda invocar por accidente.

## Estructura

```
rtl/blink_div.v                     divisor parametrizado
rtl/top.v                           top level
constraints/colorlight_5a75b_v8.lpf pines de la rev 8.0
sim/tb_top.v                        testbench autoverificable
Makefile
```

## Resultados de la última corrida

Síntesis (`make stats`, yosys): 99 celdas — 50 `TRELLIS_FF`, 23 `LUT4`,
23 `CCU2C` (carry), 3 `PFUMX`. Sin BRAM ni DSP.

nextpnr las cuenta antes de empaquetar como 69 LUT4 sobre 24.288 disponibles
(**0 %**): 23 lógicas más 46 de carry.

Place & route:

```
TRELLIS_IO:  4/197   2%      # clk25, btn_n, led_t6, led_p11
DCCA:        1/56    1%      # clk25 promovido a red global
DP16KD:      0/56    0%
MULT18X18D:  0/28    0%

led_t6   -> X4/Y50/PIOA
led_p11  -> X72/Y47/PIOC
clk25    -> X0/Y47/PIOC
btn_n    -> X6/Y50/PIOA

Max frequency: 233.15 MHz (PASS at 25.00 MHz)
```

Bitstream: `build/blinky.bit`, 100.017 bytes con `--compress`.

Simulación: `PASS: sin errores (relación de flancos 10:4 = 2.5x, botón OK)`.

Lint: limpio.

## Notas de diseño

**Sin PLL.** Los divisores cuelgan directamente de los 25 MHz de `P6`. El clock
de píxel derivado con `sysCLOCK` (TN1263) entra recién en el Paso 1, cuando haya
que generar los 12,5 MHz del punto de operación.

**Sin reset.** Los registros arrancan con valor declarado; en ECP5 el estado
inicial de los flip-flops va en el bitstream. De ahí el `-Wno-PROCASSINIT` que
el Makefile pasa a verilator: esa advertencia asume un flujo ASIC.

**Botón sincronizado.** `btn_n` es asíncrono respecto de `clk25`, así que pasa
por dos flip-flops antes de usarse. Es un detalle que no cambia nada en un
blinky, pero el hábito importa cuando el mismo patrón aparezca en el
secuenciador BCM.

**El testbench simula rápido.** `top` toma `CLK_HZ`, `SLOW_HZ` y `FAST_HZ`; el
banco lo instancia con `CLK_HZ=100` para que cada semiperiodo sean 5 y 2 ciclos
en vez de 12,5 y 3,1 millones.

**Ningún pin HUB75 está restringido.** El `.lpf` solo declara reloj, botón y los
dos candidatos a LED. Nada de este diseño llega a los conectores de panel.

## Programación en WSL2

```powershell
usbipd list                      # localizar el adaptador JTAG
usbipd attach --wsl --busid <N>
```

Reglas udev y grupo `plugdev` ya configurados — ver
[`../TOOLCHAIN.md`](../TOOLCHAIN.md).

## Antes de conectar la placa

Del checklist de la sección 7 del doc 12, lo que aplica a este paso:

- [ ] Leer la revisión serigrafiada y confirmar que es **8.0 u 8.2**. Con una
      6.1 hay que cambiar `PACKAGE` a `CABGA381` en el Makefile y rehacer el
      `.lpf` entero: es otro encapsulado.
- [ ] Verificar continuidad de los pines del header JTAG antes de soldar.
- [ ] Volcar la SPI flash completa antes de escribir nada.
