# Driver propio — Colorlight 5A-75B

Bloques HDL del driver de panel de
[`docs/11_arquitectura_colorlight_5a75b.md`](../docs/11_arquitectura_colorlight_5a75b.md).
La carpeta crece con el plan de bring-up; hoy tiene el primer bloque, que se
valida **sin placa** contra los vectores dorados del simulador.

## Bloques

| Bloque | Estado |
|---|---|
| `rgb_to_bitplane` | implementado y validado contra vectores |
| `bitplane_store` | pendiente |
| `bcm_sequencer` | pendiente |
| `scan_mapper` | pendiente — necesita panel (Paso 2) |
| `hub75_serializer` ×8 | pendiente |

## rgb_to_bitplane

RGB888 → `3*DEPTH` bits de planos. La gamma y la cuantización las resuelve una
LUT de 256 entradas generada por el simulador (`panel_sim.vectors`), así el
bloque coincide **bit a bit** con `panel_sim.quantize` (mismo redondeo
incluido). Salida empaquetada `[bit*3 + canal]` (bit 0 = LSB; R=0, G=1, B=2),
un registro de salida. Es la duplicación deliberada de `docs/14` validada
contra su referencia de software.

```bash
make sim      # testbench contra los vectores dorados
make lint     # verilator
make synth    # yosys: recursos en ECP5 (sin bitstream, falta el top de placa)
make stats    # recursos tras sintetizar
make vectors  # regenera los vectores desde el simulador
```

El testbench carga `frame_rgb888.mem` (entrada), los 15 `bitplane_b*_*.mem`
(esperados) y `gamma_lut_2p2_5b.mem` desde `../simulator/vectors`, y compara
bit a bit: 1920 comparaciones (128 píxeles × 15 bits).

Si el contrato de wire termina en "la PC manda bitplanes ya armados"
(`docs/14`), este bloque no se instancia y la LUT se queda del lado software.

## Pendiente de hardware

El `.lpf` de los 56 pines HUB75 y el `scan_mapper` recién con la placa (Pasos
0 y 2 del plan). La cadena completa está en
[`docs/16_cadena_completa.md`](../docs/16_cadena_completa.md).
