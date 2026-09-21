# 02 — Lista de materiales (BOM)

Este BOM lista **qué comprar**. Los precios en USD son referencias FOB de planificación
para la electrónica y la protección; la estructura, el gabinete, la fundación, la
instalación y los honorarios se cotizan en pesos y están estimados en
[`19_costos_argentina.md`](19_costos_argentina.md). El objetivo original de
USD 500–1000 cubría solo materiales importados sin envío, sin estructura y sin mano
de obra; el proyecto completo con mástil y fundación queda en otro orden (ver 19).

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

## Gabinete y estructura de soporte

Configuración vigente: **gabinete en voladizo sobre mástil con brazo** —
[`17_montaje_y_proteccion.md`](17_montaje_y_proteccion.md) (gabinete R2) y
[`18_monoposte.md`](18_monoposte.md) (soporte R2.1). Las cantidades salen del modelo
`hardware/cad/monoposte.py`; los precios, en pesos, están en [`19`](19_costos_argentina.md).
La lista anterior de fachada (perfil de aluminio 40×40, chapa 1310×670, anclajes
químicos M10) **queda retirada**: no sirve para el bastidor en voladizo.

| # | Ítem | Especificación | Cant. | Precio |
|---|---|---|---|---|
| 12 | Mástil | Tubo estructural 120×120×**6,35** mm, largo terminado 2.280 mm; placa base 350×350×16 con 4 cartelas 100×100×10 | 1 | ver 19 |
| 13 | Brazo y brida | Tubo 120×120×**4,75** mm (tramo bruto 1.000 mm, mitrado a 45°); dos placas 280×220×12, 6× M12 8.8 con arandelas y tuercas | 1 | ver 19 |
| 14 | Bastidor del gabinete (acero) | Montante de borde 120×100×4, perímetro 60×40×3, montante central 40×40×2; galvanizado o sistema anticorrosivo | ≈ 24 kg | ver 19 |
| 15 | Envolvente del gabinete (aluminio) | Marco frontal L con asiento EPDM, 5 rieles tubulares 30×20×2, carcasa y fondo 2 mm, bandeja, 2 puertas con refuerzo, 4 capotas; anodizado o pintado | ≈ 20 kg | ver 19 |
| 16 | Fundación y anclaje | Zapata 1,6×1,6×0,6 m H-21 (~1,58 m³ con grout), armadura Ø8 (sin despiece liberado), 4 pernos M20 5.8 con placas de anclaje 80×80×10 y tuercas de nivelación, grout sin retracción, caño camisa Ø50 con curva, jabalina Ø16×1,5 m con caja de inspección | 1 | ver 19 |
| 16b | Herrajes del gabinete | Bisagras piano inox, cierres de compresión, retenes y cables de retención, juntas EPDM, separadores aislantes, tornillería inox A2 con aislación galvánica | 1 lote | ver 19 |

⚠ Dimensiones de mástil, brida, pernos y zapata son de anteproyecto: se compran
recién con el cálculo firmado (docs/18 §8).

## Sensores y varios

| # | Ítem | Cant. | Subtotal (USD) |
|---|---|---|---|
| 17 | Sensor Huidu HD-S107 o compatible HD-WF4 para brillo automático | 1 | 10 |
| 18 | Ventilación forzada | 2× ventilador 12 V de 120 mm seleccionados por curva caudal–presión (objetivo ~200 m³/h **entregados** con filtro y capotas) + termostato ~35 °C + fuente auxiliar 12 V (LRS-35-12); filtros y capotas según docs/17 §6 | 1 lote | 45 |
| 19 | Ferretería, sellante neutro PU/Sika, varios | 1 lote | 5 |

## Resumen

| Categoría | Subtotal |
|---|---|
| Electrónica (FOB, sin envío) | USD 438 |
| Protección/distribución CA y distribución 5 V | USD 76 |
| Sensores, ventilación y varios | USD 60 |
| **Materiales importables, FOB** | **~USD 574** |
| Gabinete, estructura, fundación, instalación y honorarios | en pesos, [`19`](19_costos_argentina.md): obra ≈ 6,71 M ARS + honorarios 1,65–3,4 M ARS (sept. 2026); requiere venta por corte de los tubos 120×120 |
| Driver propio — track paralelo, opcional | USD 53 |

## Notas de compra

1. **Módulos P5**: comprar los 16 del mismo lote/vendedor. Pedir 2 de repuesto del mismo modelo (~USD 26 adicionales, recomendado).
2. **Verificar compatibilidad HUB75/HUB75E** entre módulos y la Huidu HD-WF4. Confirmar pinout, polaridad, IC driver y archivo de configuración antes de comprar los cables flat.
3. **Meanwell LRS-350-5**: comprar en distribuidor autorizado — abundantes clones en mercados genéricos.
4. El camino crítico es el envío de módulos y controlador desde China: **2–3 semanas**. Fuentes y estructura se compran en paralelo localmente; la estructura recién con el cálculo firmado y el estudio de suelos (docs/18, docs/19 §9).
5. Guardar facturas para permiso municipal y seguro.
6. El módulo declara >4500 nits, no 5000 nits. Si habrá sol directo intenso, comprar primero una muestra y validarla en el lugar.

\* Precio de referencia de planificación; cotizar antes de comprar.
