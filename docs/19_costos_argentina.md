# 19 — Estimación de costos · Mercado argentino

> **Estimación para presupuestar, no una cotización.** Las cantidades salen del
> modelo R2.1 (`hardware/cad/monoposte.py`, SHA-256 `b18f1b68…`) y las masas de la
> ficha regenerable. Los precios se relevaron el **2026-09-17** donde se indica y,
> donde no, son estimaciones marcadas. Todo ítem **[B]** debe reemplazarse por
> cotización antes de comprometer dinero. Alcance: ruta de producción (Huidu
> HD-WF4) sobre la estructura monoposte de docs/17 y docs/18. El driver propio va
> aparte (capítulo 9).

## 1. Resumen

| Capítulo | ARS | USD @MEP | Conf. |
|---|---:|---:|---|
| 1. Electrónica (importada y puesta en el país) | 1.810.000 | 1.180 | M |
| 2. Gabinete (materiales + fabricación) | 1.150.000 | 750 | M |
| 3. Estructura monoposte (materiales + fabricación) | 1.220.000 | 795 | B |
| 4. Fundación | 1.310.000 | 855 | M |
| 5. Instalación eléctrica, izaje y montaje | 1.220.000 | 795 | M |
| **Obra (materiales y servicios)** | **6.710.000** | **4.375** | B |
| 6. Honorarios y trámites (rango) | 1.650.000 – 3.400.000 | 1.075 – 2.216 | B |
| **Total ruta HD-WF4** | **8.360.000 – 10.110.000** | **5.450 – 6.590** | B |
| 7. Driver propio (opcional, track paralelo) | ~400.000 | 261 | B |
| **Total con driver propio** | **8.760.000 – 10.510.000** | **5.710 – 6.850** | B |

Escenario de **mano de obra propia** (el dueño suelda y arma; se contrata solo
electricista, fundación e izaje): obra ≈ **5,6 M ARS**, total ≈ **7,3 – 9,0 M ARS**.

No incluye: tasa municipal de publicidad (puede ser un canon anual), seguro de
responsabilidad civil, energía, impuestos ni contingencias.

**Contraste con el objetivo original.** Los USD 500–1.000 de docs/02 eran
materiales importados sin envío, sin estructura y sin mano de obra. Solo la
electrónica puesta en el país hoy ronda los **USD 1.180** al MEP; el proyecto
completo, con fundación y firma profesional, queda en el orden de los
**USD 5.450–6.590**.

El resumen supone que la acerera vende los perfiles por corte. Tubo Center
publica para medidas mayores de 100 × 100 mm un largo estándar de **12 m**. Si
obliga a comprar una barra completa de cada espesor, solo los dos tubos suman
505,7 kg y el capítulo 3 aumenta aproximadamente **1,39 M ARS** al ancla usada;
no comprar bajo esa condición sin comparar corte, remanente aprovechable o venta
del sobrante.

## 2. Tipo de cambio (relevado 2026-09-17)

| Casa | Venta (ARS/USD) |
|---|---:|
| Oficial | 1.535 |
| Blue | 1.555 |
| MEP / Bolsa | 1.534,4 |
| Tarjeta | 1.995 |

Fuente: `dolarapi.com/v1/dolares`. Criterio: las compras al exterior pagadas con
tarjeta se convierten a **dólar tarjeta**; el mercado local se referencia en
**MEP** para expresar totales en USD.

## 3. Cantidades tomadas del modelo R2.1

| Ítem | Cantidad | Origen |
|---|---:|---|
| Acero estructural instalado (mástil, placa base, cartelas, 2 bridas, brazo y M12) | 92,34 kg | Masa CAD R2.1 |
| Tubo 120×120×6,35, mástil terminado 2,280 m | 54,29 kg | 23,812 kg/m, tabla informativa Escoda |
| Tubo 120×120×4,75, tramo bruto 1,000 m | 18,33 kg | 18,331 kg/m, tabla informativa Escoda |
| Acero estructural para cotizar por corte (tubos comerciales + placas/cartelas/bridas del CAD) | **101,12 kg** | 72,62 kg de tubos comerciales + 28,49 kg restantes del CAD |
| Acero del bastidor del gabinete (120×100×4 + 60×40×3 + 40×40×2) | ≈ 24 kg | Ídem |
| Aluminio (5 rieles 30×20×2, marco, carcasa, fondo, 2 puertas, bandeja, capotas) | ≈ 20 kg | Ídem |
| Componentes (16 módulos, 4 fuentes, 2 ventiladores, 2 filtros) | 23,5 kg | Masas asignadas del modelo |
| Reserva de equipamiento no representado | 5,0 kg | docs/17 §8 |
| **Conjunto que se iza** | **91,09 kg** | Ficha R2.1, incluye reserva de 5 kg |
| Hormigón (zapata neta 1,534 m³ + grout) | 1,58 m³ | Modelo |
| Jabalina Ø16 × 1,5 m + caja de inspección | 1 | docs/18 |
| Pernos M20 con placas de anclaje 80×80×10 | 4 juegos | Modelo |
| Caño camisa Ø50 con curva R100 (reserva en zapata) | ~6 m | Modelo |
| Armadura Ø8 (doble malla + jaula) — **sin despiece liberado** | ~60 kg (est.) | Estimado |

## 4. Capítulo 1 — Electrónica

Precios FOB de docs/02 convertidos a **dólar tarjeta** y con recargo estimado de
flete internacional, despacho y gestión (+70 % sobre FOB, dos bultos, ~35 kg).

| Ítem | Cant. | Unitario ARS | Subtotal ARS | Conf. |
|---|---:|---:|---:|---|
| Módulo P5 320×160 outdoor (FOB USD 12,96) | 16 | 46.000 | 736.000 | M |
| Huidu HD-WF4 (FOB USD 40) | 1 | 150.000 | 150.000 | M |
| Mean Well LRS-350-5 (FOB USD 35; local genuina 90–110 USD) | 4 | 165.000 | 660.000 | M |
| Fuente auxiliar 12 V (LRS-35-12) | 1 | 60.000 | 60.000 | B |
| Ventiladores 120 mm 12 V + termostato | 2 + 1 | 35.000 / 20.000 | 90.000 | B |
| Filtros, rejillas y burletes | lote | — | 40.000 | B |
| Cables flat HUB75 30–40 cm | 16 | 2.500 | 40.000 | B |
| Sensor de luz (Huidu o compatible) | 1 | 30.000 | 30.000 | B |
| **Subtotal** | | | **1.806.000** | |

Alternativa de compra local de todo el capítulo: mismo orden (±15 %), con la
ventaja de garantía y sin despacho. Comprar las fuentes afuera y los módulos
localmente suele ser el peor de ambos: cotizar.

## 5. Capítulo 2 — Gabinete

| Ítem | Cant. | Unitario | Subtotal ARS | Conf. |
|---|---:|---:|---:|---|
| Acero del bastidor | 24 kg | 3.200 ARS/kg | 77.000 | M |
| Aluminio (perfiles y chapa 2 mm) | 20 kg | 6.500 ARS/kg | 130.000 | B |
| Juntas EPDM, separadores aislantes, sellante PU | lote | — | 35.000 | B |
| Bisagras piano, cierres, retenes, tornillería inox A2 | lote | — | 150.000 | B |
| Protección de superficie (anodizado/pintura) | lote | — | 100.000 | B |
| Fabricación: corte, plegado, soldadura, armado | 6 jornadas | 110.000 | 660.000 | B |
| **Subtotal** | | | **1.152.000** | |

Pendiente de cotización: plegado de capotas y puertas, y tratamiento final del
aluminio. Las bisagras comerciales y los cierres aún no están seleccionados
(docs/17 §4 y §9), así que el lote de herrajes puede moverse ±40 %.

## 6. Capítulo 3 — Estructura monoposte

| Ítem | Cant. | Unitario | Subtotal ARS | Conf. |
|---|---:|---:|---:|---|
| Acero estructural por corte (mástil, brazo, placa base, cartelas, bridas) | 101,12 kg | 3.200 ARS/kg | 323.574 | B |
| Tornillería M12 8.8 + arandelas + tuercas | 6 juegos | — | 25.000 | B |
| Mecanizado de placas (agujeros Ø22 y Ø32, cortes) | lote | — | 60.000 | B |
| Galvanizado en caliente (estructura por corte + bastidor del gabinete) | 125,12 kg | 2.200 ARS/kg | 275.257 | B |
| Fabricación y soldadura de taller (mitrados, cartelas, bridas) | 4 jornadas | 120.000 | 480.000 | B |
| Transporte a obra | lote | — | 60.000 | B |
| **Subtotal** | | | **1.223.831** | |

El valor de 101,12 kg usa los pesos comerciales publicados para los tubos y venta
por corte; no es la masa instalada de 92,34 kg ni contempla una barra completa de
12 m. El cálculo de uniones, soldaduras y placa base está pendiente (docs/18 §2).
Si el profesional pide rigidizadores o subir la brida a 8 tornillos, actualizar acá.

## 7. Capítulo 4 — Fundación

| Ítem | Cant. | Unitario | Subtotal ARS | Conf. |
|---|---:|---:|---:|---|
| Excavación manual 1,6×1,6×0,6 m + sobreancho | 3,5 m³ | 60.000/m³ | 210.000 | B |
| Hormigón H-21 elaborado en obra (cemento + áridos + peón) | 1,58 m³ | 280.000/m³ | 450.000 | M |
| Armadura Ø8 (malla doble + jaula) | 60 kg | 3.300 ARS/kg | 198.000 | B |
| Pernos M20 5.8, placas de anclaje, tuercas de nivelación, plantilla | 4 juegos | — | 150.000 | B |
| Jabalina + caja de inspección + conductor de conexión | 1 | — | 120.000 | B |
| Caño camisa Ø50 con curva + malla de advertencia | ~6 m | — | 140.000 | B |
| Grout sin retracción | 0,05 m³ | — | 40.000 | B |
| **Subtotal** | | | **1.308.000** | |

Hormigón elaborado de camión: mínimo comercial de 3 m³ (~250.000 ARS/m³) más
bombeo; para 1,58 m³ conviene elaborar en obra con mixera, que es lo cotizado.
El estudio de suelos puede cambiar zapata y armadura (capítulo 6).

## 8. Capítulo 5 — Instalación eléctrica, izaje y montaje

| Ítem | Cant. | Unitario | Subtotal ARS | Conf. |
|---|---:|---:|---:|---|
| Materiales eléctricos (diferencial 30 mA, breaker 2P 10 A, SPD tipo 2, borneras, fusibles, 12 AWG, PE, prensaestopas) | lote | — | 380.000 | B |
| Electricista matriculado (acometida, tablero, PE, pruebas) | 2,5 jornadas | 120.000 | 300.000 | B |
| Izaje: camión con pluma media jornada + eslingas | 1 | — | 460.000 | B |
| Alquiler de plataforma/andamio | 1 semana | — | 80.000 | B |
| **Subtotal** | | | **1.220.000** | |

## 9. Capítulo 6 — Honorarios y trámites

| Ítem | Rango ARS | Conf. |
|---|---:|---|
| Cálculo estructural firmado + planos de taller (requisito del permiso de obra) | 900.000 – 1.800.000 | B |
| Estudio de suelos | 600.000 – 1.200.000 | B |
| Seguro de responsabilidad civil (anual) | 150.000 – 400.000 | B |
| Permiso municipal / tasa de publicidad | **a consultar** — según municipio y m² | B |

Sin el estudio de suelos no hay cálculo firmado, y sin cálculo no hay permiso:
estos importes son camino crítico administrativo, no opcionales.

## 10. Capítulo 7 — Driver propio (opcional)

Del BOM de docs/13, sin repetir módulos ni fuentes: Colorlight 5A-75B (~USD 18),
programador JTAG (~USD 5–15), analizador lógico (~USD 110), red (~USD 23).
Puesto en el país, **~350.000 – 450.000 ARS**. Es track paralelo: no bloquea la
puesta en marcha.

## 11. Anclas de precio usadas (2026-09-17)

| Ancla | Valor relevado | Fuente |
|---|---|---|
| Dólar oficial / blue / MEP / tarjeta | 1.535 / 1.555 / 1.534,4 / 1.995,5 | `dolarapi.com` |
| Caño estructural 100×100×1,6 mm × 3 m | 62.700 ARS (≈ 4.300 ARS/kg) | API de Easy Argentina |
| Caño estructural 50×50×1,6 mm × 3 m | 28.400 ARS (≈ 3.950 ARS/kg) | Ídem |
| Caño estructural 20×20×1,2 mm × 3 m | 8.700 ARS (≈ 4.050 ARS/kg) | Ídem |
| Cemento de albañilería 25 kg | 7.490 – 8.690 ARS | Ídem |
| Acero estructural a granel (distribuidor) | 3.200 ARS/kg (est.) | Derivado del retail |
| Aluminio | 6.500 ARS/kg (est.) | Estimado |
| Galvanizado en caliente | 2.200 ARS/kg (est.) | Estimado |
| Jornada oficial / peón | 120.000 / 70.000 ARS (est.) | Estimado |
| Tubo Center, 120×120×4,75 y 120×120×6,35 | Medidas catalogadas; largo estándar 12 m | Catálogo público, sin precio publicado |
| Tubos comerciales 120×120×4,75 / 6,35 | 18,331 / 23,812 kg/m | Tabla informativa de Metalúrgica Escoda |

Las nueve referencias de Easy se tomaron del mismo catálogo y mismo día:
consistencia entre 3.950 y 4.300 ARS/kg para caños de distinta sección. Un
distribuidor de acero debería quedar 20–30 % por debajo del retail de home
center; el 3.200 ARS/kg lo refleja. Los catálogos de Tubo Center y Escoda validan
medidas y pesos, pero no publican el precio del perfil elegido. **Cotizar igual: el
mercado se mueve.**

## 12. Cómo actualizar esta estimación

1. Reemplazar todo unitario **[B]** por cotización real (fecha y proveedor).
2. Recalcular cantidades si cambia el modelo: las masas salen de la ficha R2.1
   (`hardware/cad/build/especificaciones_cartel.md`, regenerable).
3. Actualizar el tipo de cambio antes de cada decisión de compra.
4. Sumar la tasa municipal y el seguro cuando se conozcan: hoy están fuera.

## 13. Lo que más mueve el total

| Palanca | Efecto |
|---|---|
| Honorarios y estudio de suelos | ±1,7 M ARS |
| Importar la electrónica uno mismo vs. comprar local | ±0,3 M ARS |
| Hacer propia la fabricación/soldadura | −1,1 M ARS |
| Elegir camión con pluma vs. aparejo manual en el mástil | ±0,4 M ARS |
| Hormigón de camión (mínimo 3 m³) en vez de obra | +0,3 M ARS |
| Acerera sin venta por corte de los tubos 120×120 | +1,39 M ARS de material no instalado |

Pendiente de cotización real (orden sugerido): módulos y controladora ·
fuentes · perfilería de acero y galvanizado · plegado de chapa · hormigón ·
honorarios profesionales.
