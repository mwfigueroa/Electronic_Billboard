# 02 — Lista de materiales (BOM)

Presupuesto objetivo del proyecto: **USD 500–1000**. Estimado total: **~USD 754**, sin envío ni impuestos.

## Electrónica

| # | Ítem | Especificación | Cant. | Precio unit. (USD) | Subtotal | Proveedor sugerido |
|---|---|---|---|---|---|---|
| 1 | Módulo LED P5 outdoor SMD | LYERAEEN P5-320x160-8S-1921, 320×160 mm, 64×32 px, HUB75, scan 1/8, >4500 nits | 16 | 12,96* | 208 | [AliExpress](https://es.aliexpress.com/item/1005010560338789.html) |
| 2 | Controlador asíncrono | Huidu HD-WF4 (WiFi + USB, 4× HUB75E, sensor externo). Controladora de producción con su firmware de fábrica; el driver propio va sobre la 5A-75B del ítem D1. | 1 | 40* | 40 | AliExpress / distribuidor Huidu |
| 3 | Fuente switching | Meanwell LRS-350-5 (5 V / 60 A), una por fila | 4 | 35 | 140 | LCSC / Mouser / local |
| 4 | Fuente auxiliar | 5 V / 2 A para pruebas de banco de la controladora (opcional) | 1 | 6 | 6 | local |
| 5 | Flat cable HUB75 | Pinout, cantidad de pines, polaridad y paso compatibles con la HD-WF4 y el módulo; 30–40 cm | 20 | 0,8 | 16 | AliExpress |
| 6 | Cable potencia 5 V | 12 AWG flexible (rojo/negro), silicona; dos inyecciones por fila | 16 m | — | 24 | local |
| 7 | Cable señal datos | Cat6 (controlador → módulos, alternativa a flat) | 5 m | — | 4 | local |

## Driver propio (track paralelo)

No forma parte del presupuesto de puesta en marcha: la ruta de producción es la HD-WF4 del ítem 2. Ver [`10_plataforma_driver.md`](10_plataforma_driver.md) y [`11_arquitectura_colorlight_5a75b.md`](11_arquitectura_colorlight_5a75b.md).

| # | Ítem | Especificación | Cant. | Subtotal (USD) |
|---|---|---|---|---|
| D1 | Colorlight 5A-75B | FPGA Lattice ECP5-25, 8× HUB75, 4 MB SDRAM, 2× PHY Gigabit. **Exigir revisión 8.0 u 8.2** — los pinouts difieren entre revisiones y LiteDRAM solo soporta esas dos | 1 | 18 |
| D2 | Programador JTAG | FT2232H mini-module o compatible con openFPGALoader | 1 | 12 |
| D3 | AP / router WiFi con Ethernet | Enlace de contenido a la placa; la 5A-75B no tiene WiFi | 1 | 20 |
| D4 | Cable Ethernet, patch corto | Cat5e/Cat6 | 1 | 3 |
| | | | **Subtotal** | **53** |

El conteo de cables flat no cambia: 8 cadenas de 2 módulos necesitan los mismos 16 cables que 4 cadenas de 4.

## Protección y distribución CA

| # | Ítem | Especificación | Cant. | Subtotal (USD) |
|---|---|---|---|---|
| 8 | Interruptor diferencial | 2P, 25 A, 30 mA | 1 | 20 |
| 9 | Breaker termomagnético | 2P, curva C, 10 A | 1 | 8 |
| 10 | SPD (protector sobretensión) | Tipo 2, 275 V | 1 | 18 |
| 11 | Borneras, 8× porta-fusible 20 A, 1× porta-fusible 2 A, fusibles, ferrules, termocontraíl, prensaestopas IP68 | — | — | 30 |

## Estructura y montaje

| # | Ítem | Especificación | Cant. | Subtotal (USD) |
|---|---|---|---|---|
| 12 | Perfil aluminio estructural | 40×40 mm, ranurado | 8 m | 55 |
| 13 | Chapa trasera aluminio | 2 mm, 1310×670 mm (puerta de servicio) | 1 | 40 |
| 14 | Marco frontal + junta neopreno | Perfil plegado + cordón EPDM | 1 lote | 45 |
| 15 | Rieles de montaje de módulos | Perfil 20×20 + tornillería inox M3/M4/M5 | 1 lote | 35 |
| 16 | Anclajes químicos | M10 × 110 mm + varilla roscada inox | 6 | 15 |

## Sensores y varios

| # | Ítem | Cant. | Subtotal (USD) |
|---|---|---|---|
| 17 | Sensor Huidu HD-S107 o compatible HD-WF4 para brillo automático | 1 | 10 |
| 18 | Ventilación forzada | 2× ventilador 5 V con rulemán + termostato, flujo total ≥200 m³/h, filtros IP54, rejillas y drenajes | 1 lote | 35 |
| 19 | Ferretería, sellante neutro PU/Sika, varios | 1 lote | 5 |

## Resumen

| Categoría | Subtotal (USD) |
|---|---|
| Electrónica | 438 |
| Protección/distribución CA y distribución 5 V | 76 |
| Estructura y montaje | 190 |
| Sensores y varios | 50 |
| **Total estimado (puesta en marcha)** | **~754** |
| Driver propio — track paralelo, opcional | 53 |
| **Total con driver propio** | **~807** |

## Notas de compra

1. **Módulos P5**: comprar los 16 del mismo lote/vendedor. Pedir 2 de repuesto del mismo modelo (~USD 26 adicionales, recomendado).
2. **Verificar compatibilidad HUB75/HUB75E** entre módulos y la Huidu HD-WF4. Confirmar pinout, polaridad, IC driver y archivo de configuración antes de comprar los cables flat.
3. **Meanwell LRS-350-5**: comprar en distribuidor autorizado — abundantes clones en mercados genéricos.
4. El camino crítico es el envío de módulos y controlador desde China: **2–3 semanas**. Fuentes y estructura se compran en paralelo localmente.
5. Guardar facturas para permiso municipal y seguro.
6. El módulo declara >4500 nits, no 5000 nits. Si habrá sol directo intenso, comprar primero una muestra y validarla en el lugar.

\* Precio de referencia de planificación; cotizar antes de comprar.
