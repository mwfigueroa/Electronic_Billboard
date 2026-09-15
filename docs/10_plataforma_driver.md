# 10 — Elección de plataforma para el driver propio

> **Registro de decisión.** Fecha: 2026-09-13. Estado: **adoptada**.
> Plataforma elegida para el driver propio: **Colorlight 5A-75B** (FPGA Lattice ECP5-25).
> La ruta de producción inicial sigue siendo Huidu HD-WF4 + HD2020 / HDSign, ver [`06_control_contenido.md`](06_control_contenido.md).

## Contexto

El proyecto necesita decidir sobre qué hardware se implementa el control directo de la matriz de 256 × 128 px. Se evaluaron cuatro plataformas. La conclusión es que **el cuello de botella no es la velocidad del procesador, sino cuántos buses RGB pueden manejarse simultáneamente y dónde se almacena el framebuffer**.

Este documento corrige además el modelo de refresco usado en [`09_firmware_propio_hd_wf4.md`](09_firmware_propio_hd_wf4.md), que subestimaba los clocks necesarios por un factor de 2.

## Modelo de refresco (corregido)

Un panel HUB75 no tiene memoria ni PWM propio: es un registro de desplazamiento. El color se obtiene por modulación de código binario (BCM), mostrando *n* bitplanes con tiempos proporcionales a 1, 2, 4 … 2ⁿ⁻¹.

### Clocks por bitplane

El error del doc 09 fue usar el ancho físico de la fila como cantidad de clocks. Con scan 1/8 en un módulo de 64 × 32 px:

```
2048 px/módulo ÷ 8 (scan) ÷ 2 (grupos R1G1B1 / R2G2B2) = 128 px por grupo
```

Cada módulo necesita **128 clocks por paso de dirección, no 64**. La cadena de desplazamiento interna mide el doble del ancho físico — comportamiento normal en paneles outdoor de scan bajo, y distinto del caso indoor 1/16 donde clocks = ancho.

La forma general, independiente de la organización interna:

```
clocks_por_bitplane = (ancho × alto) ÷ (2 grupos × N buses)
t_bitplane          = clocks_por_bitplane ÷ f_clk
refresco            = 1 ÷ (t_bitplane × (2ⁿ − 1))
```

Para 256 × 128 px = 32.768 píxeles:

| Buses RGB simultáneos | Clocks por bitplane |
|---|---:|
| 2 (HD-WF4, bancos multiplexados) | 8.192 |
| 4 | 4.096 |
| **8 (5A-75B)** | **2.048** |

El número de buses es el único parámetro que mueve la aguja de verdad. **No hay software que baje ese piso.**

## Plataformas evaluadas

### A — Huidu HD-WF4 con firmware ESP-IDF propio

La placa no tiene cuatro buses RGB independientes: tiene **dos buses y dos bancos habilitados alternativamente** por GPIO45 y GPIO14, con `A`–`E`, `CLK`, `LAT` y `OE` compartidos. Los bancos son seriales, así que el piso es 8.192 clocks por bitplane.

Además, el periférico LCD_CAM del ESP32-S3 saca 16 bits por pixel clock y se necesitan 17:

| Señal | Bits |
|---|---:|
| RGB bus A + bus B | 12 |
| `LAT` | 1 |
| `A`, `B`, `C` (scan 1/8) | 3 |
| `OE` | 1 |
| **Total** | **17** sobre 16 disponibles |

Sobra exactamente un bit. Obliga a sacar `OE` del stream con LEDC/RMT, o las direcciones por CPU en el EOF del DMA, con jitter visible como variación de brillo.

Refresco alcanzable:

| Profundidad | 16 MHz | 20 MHz | 24 MHz |
|---|---:|---:|---:|
| 4 bits/color | 130 Hz | 163 Hz | 196 Hz |
| 5 bits/color | 63 Hz | 79 Hz | 95 Hz |

**Los objetivos originales del doc 09 (5 bits/color y ≥ 192 Hz) son mutuamente inalcanzables en esta placa.**

### B — ESP32-P4 en placa de desarrollo con etapa de salida propia

El controlador Camera-LCD del P4 soporta modos paralelos de 8/16/24 bits (RGB888), así que el presupuesto de bits desaparece y se pueden manejar 4 buses reales. Con 768 KB de SRAM interna y PSRAM externa, la restricción de memoria del doc 09 también desaparece. Suma PPA (acelerador 2D) y 2D-DMA, útiles para scroll y composición.

Refresco con 4 buses:

| Profundidad | 16 MHz | 20 MHz | 25 MHz |
|---|---:|---:|---:|
| 4 bits/color | 260 Hz | 326 Hz | 407 Hz |
| 5 bits/color | 126 Hz | 158 Hz | 197 Hz |

Descartada por dos motivos prácticos:

1. **Pines.** Cuatro buses requieren 24 RGB + 3 direcciones + `LAT` + `OE` + `CLK` = **30 GPIO**. La FireBeetle 2 ESP32-P4 mide 25,4 × 60 mm con MIPI-DSI y MIPI-CSI ocupando pines; difícilmente exponga 30 libres.
2. **Etapa de salida.** Una dev board no tiene buffers, level shifters 3,3 → 5 V ni conectores HUB75E. Hay que diseñar, fabricar y depurar una placa de interfaz con terminación serie y plano de masa a 20–25 MHz.

### C — FPGA Cyclone IV EP4CE6E22C8N como etapa intermedia

La arquitectura correcta —FPGA al medio, MCU para contenido y red— pero el chip no alcanza. El EP4CE6 tiene **30 bloques M9K = 270 Kbit (276.480 bits)** de RAM embebida:

| Profundidad | Bits del frame | ¿Entra? |
|---|---:|---|
| 2 bits/color | 196.608 | Sí, pero son 64 colores |
| 3 bits/color | 294.912 | No, 7 % corto |
| 4 bits/color | 393.216 | **No, falta 42 %** |
| 5 bits/color | 491.520 | No |

Y eso es simple buffer. Para cartelería el almacenamiento del frame **no es opcional**: el contenido es estático 4–7 segundos por slide, así que el refresco debe salir de un frame guardado, no de un stream vivo. Sin memoria de frame, el MCU tendría que reenviar la imagen completa a la tasa de refresco:

```
32.768 px × 15 bits × 200 Hz = 98 Mbit/s ≈ 12,3 MB/s sostenidos
```

Con memoria de frame se escriben 60 KB al cambiar de slide: **~12 KB/s promedio**. Tres órdenes de magnitud.

Los pines sí alcanzaban (~90 I/O en E144, contra 53 necesarios para 8 buses), pero faltan SDRAM, level shifters y conectores, y el toolchain (Quartus) es propietario.

### D — Colorlight 5A-75B — **adoptada**

Es la arquitectura de la opción C, ya construida y documentada:

| Se necesita | La 5A-75B trae |
|---|---|
| FPGA | Lattice **ECP5-25** (LFE5U-25F): 24.300 LUT, **1.008 Kbit EBR** |
| Buses paralelos | **8 puertos HUB75** — exacto para 16 módulos, 2 por puerto |
| Level shifters 3,3 → 5 V | Ya instalados en la placa |
| Memoria de frame | SDRAM en placa (4 u 8 MB según revisión) más 126 KB de BRAM interna |
| Red | 2× PHY Gigabit Ethernet |
| Toolchain | **Yosys + nextpnr-ecp5 + Project Trellis, 100 % abierto** |
| Framework | Soporte de primera clase en **LiteX** (`colorlight_5a_75b`) |
| Documentación | [chubby75](https://github.com/q3k/chubby75) — esquemáticos, pinouts y ejemplos |

Refresco con 8 buses (2.048 clocks de datos por bitplane):

| Profundidad | 12,5 MHz | 16 MHz | 25 MHz |
|---|---:|---:|---:|
| 4 bits/color | 407 Hz | 521 Hz | 814 Hz |
| 5 bits/color | **197 Hz** | 252 Hz | 394 Hz |
| 6 bits/color | 97 Hz | 124 Hz | 194 Hz |

Incluso a un clock conservador de 12,5 MHz se obtienen 5 bits/color a ~194 Hz con el secuenciador implementado (193,9 Hz medidos en simulación; el blanking suma 4 clocks por paso, ver [`11`](11_arquitectura_colorlight_5a75b.md)), por encima del criterio de aceptación. Es otra categoría respecto de los 130 Hz a 4 bits de la HD-WF4.

## Comparación

| | HD-WF4 | ESP32-P4 propio | EP4CE6 | **5A-75B** |
|---|---|---|---|---|
| Buses RGB simultáneos | 2 (bancos) | 4 | 8 | **8** |
| Clocks/bitplane (datos) | 8.192 | 4.096 | 2.048 | **2.048** |
| Mejor punto realista | 4 bit @ 130 Hz | 5 bit @ 197 Hz | — | **5 bit @ 388 Hz** |
| Memoria de frame | No | PSRAM | **Insuficiente** | BRAM + 4–8 MB SDRAM |
| Etapa de salida 5 V | Incluida | **A diseñar** | **A diseñar** | Incluida |
| Conectores HUB75 | 4 | **A diseñar** | **A diseñar** | 8 |
| Toolchain | ESP-IDF | ESP-IDF | Quartus (propietario) | **Abierto** |
| Costo aproximado | USD 40 | 15 + PCB | 20 + PCB | **USD 15–20** |

## Qué no resuelve esta decisión

Tres puntos siguen abiertos y son idénticos en las cuatro plataformas:

1. **Modelo de IC driver del panel.** Si el módulo usa un IC de desplazamiento simple (clase ICN2038S), vale todo el modelo BCM de arriba. Si usa un IC con **S-PWM interno** (MBI5153, FM6353 y similares), el protocolo de manejo es otro y el refresco deja de ser un presupuesto de bitplanes. Es la pregunta número uno para el vendedor — ver [`08_hub75e_y_panel_p5.md`](08_hub75e_y_panel_p5.md).
2. **Mapeo de píxeles del scan 1/8.** La relación entre `(x, y)` y `(paso de dirección, posición en cadena, grupo)` es específica del fabricante. Se obtiene del archivo de configuración del vendedor, o empíricamente.
3. **Ficha real del panel**: IP, rango térmico, refresco y niveles eléctricos.

Pasar a FPGA **no acorta** el camino crítico del proyecto, que son estas incógnitas.

## Consecuencias

- La topología de datos cambia de **4 cadenas de 4 módulos** a **8 cadenas de 2 módulos**. La cantidad total de cables flat no cambia (16). Ver [`03_electrico.md`](03_electrico.md).
- El cableado de potencia 5 V **no cambia**: sigue siendo una fuente por fila con dos inyecciones.
- La 5A-75B es una **placa receptora**: no tiene WiFi, RTC ni almacenamiento de playlist. Necesita un MCU acompañante para contenido, red y horarios. Ver [`11_arquitectura_colorlight_5a75b.md`](11_arquitectura_colorlight_5a75b.md).
- El documento [`09_firmware_propio_hd_wf4.md`](09_firmware_propio_hd_wf4.md) queda **superado** para la ruta de driver propio; se conserva como análisis de por qué se descartó la HD-WF4.

## Fuentes

- [Espressif ESP32-P4](https://www.espressif.com/en/products/socs/esp32-p4) — especificaciones del SoC
- [ESP-IDF: RGB LCD en ESP32-P4](https://docs.espressif.com/projects/esp-idf/en/stable/esp32p4/api-reference/peripherals/lcd/rgb_lcd.html) — modos paralelos 8/16/24 bits
- [arduino-esp32: variante `huidu_hd_wf4`](https://github.com/espressif/arduino-esp32/tree/master/variants/huidu_hd_wf4) — pinout verificado de la HD-WF4
- [Cyclone IV Product Table](https://cdrdv2-public.intel.com/714186/cyclone-iv-product-table.pdf) — 30 M9K / 270 Kbit del EP4CE6
- [chubby75](https://github.com/q3k/chubby75) — ingeniería inversa de la 5A-75B
- [YosysHQ: Introducing the Colorlight 5A-75B](https://blog.yosyshq.com/p/colorlight-part-1/)
- [litex-boards: `colorlight_5a_75b`](https://github.com/litex-hub/litex-boards/blob/master/litex_boards/platforms/colorlight_5a_75b.py)
