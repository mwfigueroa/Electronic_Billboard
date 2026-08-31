# 02 — Lista de materiales (BOM)

Presupuesto objetivo del proyecto: **USD 500–1000**. Estimado total: **~USD 795**.

## Electrónica

| # | Ítem | Especificación | Cant. | Precio unit. (USD) | Subtotal | Proveedor sugerido |
|---|---|---|---|---|---|---|
| 1 | Módulo LED P5 outdoor SMD | 160×160 mm, 32×32 px, HUB75E, IP65, ≥5000 nits | 28 | 13 | 364 | AliExpress / Alibaba |
| 2 | Controlador asíncrono | Colorlight A35 (WiFi, 2× puerto HUB75, hasta 650k px) | 1 | 55 | 55 | AliExpress / distribuidor Colorlight |
| 3 | Fuente switching | Meanwell LRS-350-5 (5 V / 60 A) | 3 | 35 | 105 | LCSC / Mouser / local |
| 4 | Fuente auxiliar | 5 V / 2 A para controlador (si no se alimenta del bus) | 1 | 6 | 6 | local |
| 5 | Flat cable HUB75 | 16 pines, 30–40 cm, con clip | 32 | 0,8 | 26 | AliExpress |
| 6 | Cable potencia 5 V | 12 AWG flexible (rojo/negro), silicona | 10 m | — | 15 | local |
| 7 | Cable señal datos | Cat6 (controlador → módulos, alternativa a flat) | 5 m | — | 4 | local |

## Protección y distribución CA

| # | Ítem | Especificación | Cant. | Subtotal (USD) |
|---|---|---|---|---|
| 8 | Interruptor diferencial | 2P, 25 A, 30 mA | 1 | 20 |
| 9 | Breaker termomagnético | 2P, curva C, 10 A | 1 | 8 |
| 10 | SPD (protector sobretensión) | Tipo 2, 275 V | 1 | 18 |
| 11 | Borneras, ferrules, termocontraíl, prensaestopas IP68 | — | — | 14 |

## Estructura y montaje

| # | Ítem | Especificación | Cant. | Subtotal (USD) |
|---|---|---|---|---|
| 12 | Perfil aluminio estructural | 40×40 mm, ranurado | 8 m | 45 |
| 13 | Chapa trasera aluminio | 2 mm, 1150×670 mm (puerta de servicio) | 1 | 35 |
| 14 | Marco frontal + junta neopreno | Perfil plegado + cordón EPDM | 1 lote | 40 |
| 15 | Rieles de montaje de módulos | Perfil 20×20 + tornillería inox M3/M4/M5 | 1 lote | 30 |
| 16 | Anclajes químicos | M10 × 110 mm + varilla roscada inox | 6 | 15 |

## Sensores y varios

| # | Ítem | Cant. | Subtotal (USD) |
|---|---|---|---|
| 17 | Sensor de luz ambiente (entrada del A35/LEDVISION para brillo automático) | 1 | 10 |
| 18 | Filtros de ventilación IP54, rejillas, drenajes | 1 lote | 10 |
| 19 | Ferretería, sellante neutro PU/Sika, varios | 1 lote | 5 |

## Resumen

| Categoría | Subtotal (USD) |
|---|---|
| Electrónica | 575 |
| Protección/distribución CA | 60 |
| Estructura y montaje | 165 |
| Sensores y varios | 25 |
| **Total estimado** | **~825** |

## Notas de compra

1. **Módulos P5**: comprar los 28 del mismo lote/vendedor (mismo lote LED = uniformidad de color y brillo). Pedir 1–2 de repuesto si el presupuesto da (~26 USD extra, recomendado).
2. **Verificar compatibilidad HUB75E** entre módulos y controlador A35 (polaridad de señal estándar; confirmar pinout del módulo antes de comprar flat cables).
3. **Meanwell LRS-350-5**: comprar en distribuidor autorizado — abundantes clones en mercados genéricos.
4. El camino crítico es el envío de módulos y controlador desde China: **2–3 semanas**. Fuentes y estructura se compran en paralelo localmente.
5. Guardar facturas para permiso municipal y seguro.
