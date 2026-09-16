# Driver propio — Colorlight 5A-75B

Bloques HDL del driver de panel de
[`docs/11_arquitectura_colorlight_5a75b.md`](../docs/11_arquitectura_colorlight_5a75b.md),
más un top de integración sintetizable. Todo lo que se puede validar **sin
placa** ya está: conversión contra vectores, temporización BCM/HUB75, store y
la cadena completa con bitstream.

## Bloques

| Bloque | Estado |
|---|---|
| `rgb_to_bitplane` | implementado y validado contra vectores |
| `bcm_sequencer` | implementado, temporización verificada en testbench |
| `hub75_serializer` ×8 | implementado (un puerto; se instancia ocho veces) |
| `bitplane_store` | implementado; escritura y lectura validadas contra vectores |
| `scan_mapper` | pendiente — necesita panel (Paso 2) |

## rgb_to_bitplane

RGB888 → `3*DEPTH` bits de planos. La gamma y la cuantización las resuelve una
LUT de 256 entradas generada por el simulador (`panel_sim.vectors`), así el
bloque coincide **bit a bit** con `panel_sim.quantize` (mismo redondeo
incluido). Salida empaquetada `[bit*3 + canal]` (bit 0 = LSB; R=0, G=1, B=2),
un registro de salida. Es la duplicación deliberada de `docs/14` validada
contra su referencia de software.

```bash
make sim      # testbenches: vectores dorados + temporización HUB75
make lint     # verilator (3 bloques)
make synth    # yosys: recursos en ECP5 (sin bitstream, falta el top de placa)
make stats    # recursos tras sintetizar
make vectors  # regenera los vectores desde el simulador
```

El testbench carga `frame_rgb888.mem` (entrada), los 15 `bitplane_b*_*.mem`
(esperados) y `gamma_lut_2p2_5b.mem` desde `../simulator/vectors`, y compara
bit a bit: 1920 comparaciones (128 píxeles × 15 bits).

Si el contrato de wire termina en "la PC manda bitplanes ya armados"
(`docs/14`), este bloque no se instancia y la LUT se queda del lado software.

## bitplane_store

Memoria de bitplanes con dos puertos (escritura del conversor, lectura del
futuro `scan_mapper`). Palabra = `3*DEPTH` bits de un píxel, empaquetada
`[bit*3 + canal]` igual que la salida de `rgb_to_bitplane`, con dirección
lineal `addr = y*WIDTH + x`. El testbench encadena conversor → store →
lectura al revés y compara contra los planos reconstruidos de los vectores.

Con los valores reales (256×128, 5 bits) la síntesis en ECP5 ocupa
**30 bloques DP16KD de 56 (54 %)**: algo más que el 48 % estimado en
`docs/11` porque una palabra de 15 bits no llena los 18 del primitivo.
Entra cómodo, pero conviene saberlo si más adelante se quisiera doble buffer.
El lado de lectura sirve una palabra por clock; el frente de serialización
necesita dos píxeles por clock (R1/R2), así que será el `scan_mapper` el que
decida entre leer a 2× del clock de píxel o duplicar el puerto.

## Temporización: bcm_sequencer + hub75_serializer

El secuenciador es el maestro del frame BCM y gobierna los ocho serializadores
en lockstep (comparten `A/B/C`, `CLK`, `LAT` y `OE`):

- Paso de dirección: 256 clocks de shift + 4 de blanking. Durante el shift se
  desplazan los datos de la fila `row` mientras el panel muestra los
  latcheados de `row−1` (shift-while-display); la dirección cambia en el
  blanking y `OE` queda en bajo un clock más, para que la fila se encienda
  con la dirección ya asentada.
- Peso BCM: el bitplane `k` se muestra `2^k` pasadas; un frame son
  `(2^DEPTH−1) × 8 × (SHIFT+BLANK)` clocks = **64.480 a 5 bits**, o sea
  **193,9 Hz a 12,5 MHz** (docs/11 idealizaba 2048 clocks por bitplane sin
  contar el blanking; el criterio de aceptación es ≥ 192 Hz y se cumple).
- El serializador registra los datos un clock y saca `CLK` invertido y
  gateado por `shift_en`: el registro del panel no avanza durante el
  blanking, así la posición de los píxeles no se corre.

El testbench verifica un frame completo: 256 clocks de shift por paso, 8
pasos por pasada, un `LAT` por paso, `OE` en bajo en cada `LAT` y en cada
cambio de dirección/fila, los pesos 1-2-4-8-16 y el refresco medido. No
valida el mapeo de píxeles: eso es del `scan_mapper`, que necesita el panel.

## Top de integración y `.lpf`

`rtl/top.v` encadena todo: un generador de patrón escribe el frame una vez
tras el reset (R = x, G ≈ y, B damero), el conversor lo pasa a bitplanes, el
store lo guarda y el secuenciador lo emite por los ocho serializadores con
las señales compartidas. Un latido de frame sale por los dos candidatos a LED
de usuario (T6/P11, la disputa que resuelve `blinky-5a75b`).

Es un top de bring-up, no el driver final: el mapeo de lectura es un
**placeholder** (`y = row`, `x = pix`), los ocho puertos reciben el mismo
dato y R1/R2 usan el mismo píxel. Todo eso lo define el `scan_mapper` con el
panel (Paso 2). Corre a 25 MHz: 5 bits por color → 388 Hz de refresco.

El pin `OE` sale **invertido** respecto del display-enable interno del
secuenciador: el de HUB75 es activo bajo (`0` enciende la fila, `docs/08`).
El testbench lo fija contra el pin: fila encendida durante el shift —salvo el
clock de asentamiento— y apagada en el blanking y durante `LAT`.

`constraints/colorlight_5a75b_v8.lpf` tiene los 60 pines (54 de HUB75 + los
dos LED + clock + botón) desde `docs/12 §2`, con la aclaración de nombres
R0/R1 de chubby75 vs R1/R2 de HUB75.

```bash
make sim        # los 4 testbenches (vectores, temporización, store, top)
make bitstream  # top.bit (yosys → nextpnr → ecppack)
make prog       # carga a SRAM por JTAG (volátil, no toca la flash)
make stats      # recursos de los bloques y del top
```

Medido en el top: **181 LUT4 (1 %), 131 FF, 71,7 MHz máximos** (PASS a
25 MHz), 60 I/O de 197. El BRAM del top reporta 15 bloques DP16KD en vez de
los 30 del store: con el mapeo placeholder yosys poda las direcciones que
nunca se leen; con la lectura completa (mapeo real) vuelve a 30, como la
medición standalone.

## Pendientes

Con placa: el Paso 0 del bring-up (revisión, respaldo de flash, blinky real) y
el `scan_mapper` (Paso 2, la incógnita principal). Después vienen el `bitplane_store`
de doble buffer si el contenido lo pide, LiteX/LiteDRAM/LiteEth (Paso 5) y el
`.lpf`/top definitivos. La cadena completa está en
[`docs/16_cadena_completa.md`](../docs/16_cadena_completa.md).
