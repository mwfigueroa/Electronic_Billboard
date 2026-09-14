# 13 — BOM de desarrollo (banco)

Hardware mínimo para desarrollar el driver propio. **No es el BOM del cartel** — ese está en [`02_bom.md`](02_bom.md). Acá está solo lo que hace falta sobre la mesa para llegar desde cero hasta la matriz completa andando.

Está ordenado en niveles: cada uno es comprable por separado y desbloquea una etapa concreta del plan de bring-up de [`11_arquitectura_colorlight_5a75b.md`](11_arquitectura_colorlight_5a75b.md). **No hace falta comprar todo junto.**

---

## Nivel 0 — Toolchain y primer bitstream

Desbloquea el **Paso 0**: instalar el entorno, identificar la placa, respaldar el bitstream de fábrica y hacer parpadear un LED. Todo esto se hace **sin ningún panel conectado**.

| # | Ítem | Especificación | Cant. | USD | Nota |
|---|---|---|---|---|---|
| B1 | **Colorlight 5A-75B** | **Exigir revisión 8.0 u 8.2.** Ver tabla de revisiones en [`12_referencias_tecnicas.md`](12_referencias_tecnicas.md) | 1 | 18 | El corazón del asunto |
| B2 | **Raspberry Pi Pico** | Programador JTAG con firmware DirtyJTAG | 1 | 5 | Alternativa: FT2232H mini-module, ~13 |
| B3 | Tira de pin headers 2,54 mm | El header JTAG de la placa viene **sin poblar** | 1 | 2 | Hay que soldarlos |
| B4 | Cables Dupont hembra-hembra | Pico ↔ header JTAG | 1 lote | 3 | |
| | | | **Subtotal** | **28** | |

Con esto ya se puede trabajar: instalar oss-cad-suite, correr el flujo `yosys → nextpnr-ecp5 → ecppack`, cargar a SRAM y resolver la discrepancia del pin del LED. Es la compra que conviene hacer primero y sola, porque valida el flujo completo antes de gastar en lo demás.

> Se asume soldador disponible. Si no lo hay, sumar ~USD 25 por una estación básica.

## Nivel 1 — Primer panel encendido

Desbloquea los **Pasos 1 y 2**: un módulo en `J1`, patrones de color, y el descubrimiento del mapeo de scan 1/8 — que es la incógnita crítica del proyecto.

| # | Ítem | Especificación | Cant. | USD | Nota |
|---|---|---|---|---|---|
| B5 | **Módulo LED P5 outdoor** | LYERAEEN P5-320x160-8S-1921 — **el mismo del cartel** | 2 | 13 | 26 · Ya previstos en Fase 0 |
| B6 | **Fuente 5 V / 60 A** | Meanwell LRS-350-5 | 1 | 35 | Ya prevista en el BOM del cartel |
| B7 | Cables flat HUB75 | 30–40 cm, con clip | 4 | 0,8 | 3 · Pinout a confirmar con el módulo |
| B8 | Cable de potencia 5 V | 12 AWG rojo/negro, con terminales | 2 m | — | 4 |
| | | | **Subtotal** | **68** | |

Dos módulos, no uno: uno solo no permite validar el encadenamiento `IN`/`OUT` ni el mapeo de una cadena real. Son los mismos que ya pide la Fase 0 de [`05_fabricacion_fases.md`](05_fabricacion_fases.md), así que **no son gasto adicional del proyecto** — es adelantar una compra que ya estaba.

Consumo de dos módulos a blanco pleno: 2 × 40,96 W = 82 W ≈ 16,4 A a 5 V. La LRS-350-5 sobra; si se prefiere no comprometer una fuente del cartel, una 5 V / 20 A genérica (~USD 12) alcanza para el banco.

## Nivel 2 — Instrumentación

Desbloquea los **Pasos 3 y 4**: ajustar blanking de `LAT`, ancho de `OE`, profundidad de color y clock de píxel. **Sin instrumento, estos pasos se hacen a ciegas.**

| # | Ítem | Especificación | Cant. | USD |
|---|---|---|---|---|
| B9 | **Analizador lógico** | Ver la nota de abajo — es la decisión importante de esta sección | 1 | 10–110 |
| B10 | Multímetro | Continuidad y tensión | 1 | — |
| B11 | Cámara | Para el descubrimiento del mapeo de píxeles | 1 | — |

### Sobre el analizador lógico

Es el ítem donde conviene no ahorrar, y el criterio es el **muestreo**, no los canales.

Con un clock de píxel de 12,5 MHz hace falta muestrear a **≥ 62,5 MSa/s** para ver algo útil, y a 25 MHz el piso sube a ~125 MSa/s. Los clones USB de 8 canales que se consiguen a USD 10 muestrean a **24 MSa/s**: alcanzan para los primeros patrones a clock bajo, pero **no sirven** para el punto de operación de destino.

Canales necesarios en simultáneo: `CLK`, `LAT`, `OE`, `A`, `B`, `C` más una o dos líneas RGB = **8 mínimo, 16 cómodo**.

| Opción | MSa/s | Canales | USD | Veredicto |
|---|---:|---:|---:|---|
| Clon tipo Saleae 8ch | 24 | 8 | 10 | Solo Paso 1 a clock bajo. Falso ahorro |
| **DSLogic Plus o equivalente** | 400 | 16 | ~110 | **Recomendado.** Cubre todo el rango de trabajo |
| Osciloscopio ≥ 100 MHz | — | 2–4 | 150+ | Complementario, no sustituto. Para integridad de señal, ringing y overshoot en los cables flat |

Si el presupuesto obliga a elegir, el analizador lógico va antes que el osciloscopio: los problemas de este proyecto son de **temporización y secuencia**, no de forma de onda — al menos hasta que se suba el clock.

## Nivel 3 — Red y contenido

Desbloquea el **Paso 5**. Se compra recién cuando la salida HUB75 esté estable.

| # | Ítem | Especificación | Cant. | USD |
|---|---|---|---|---|
| B12 | AP / router WiFi con Ethernet | Enlace de contenido; la 5A-75B no tiene WiFi | 1 | 20 |
| B13 | Cable de red patch | Cat5e/Cat6 corto | 2 | 3 |
| | | | **Subtotal** | **23** |

## Nivel 4 — Matriz completa

El **Paso 4** con los 16 módulos y el **Paso 6** de estrés no necesitan compras nuevas de desarrollo: usan el hardware del cartel que ya está en [`02_bom.md`](02_bom.md). El banco se conecta a la matriz real una vez ensamblada.

---

## Resumen

| Nivel | Desbloquea | USD | ¿Gasto nuevo? |
|---|---|---:|---|
| 0 — Toolchain | Pasos 0 | 28 | Sí |
| 1 — Primer panel | Pasos 1–2 | 68 | **No** — ya previsto en Fase 0 y en el BOM del cartel |
| 2 — Instrumentación | Pasos 3–4 | 110 | Sí, pero es herramienta reutilizable |
| 3 — Red | Paso 5 | 23 | Ya contemplado en el BOM del driver |
| | **Total** | **229** | **Neto nuevo: ~138** |

El neto sobre el proyecto es bajo porque el Nivel 1 ya estaba presupuestado como muestra de Fase 0, y el analizador lógico del Nivel 2 es herramienta que queda.

## Lo que se puede empezar hoy sin comprar nada

Mientras llegan las compras hay trabajo real disponible:

- Instalar **oss-cad-suite** y correr los ejemplos de `prjtrellis`.
- Escribir y **simular con Verilator** el `hub75_serializer` y el `bcm_sequencer` completos. Toda la lógica de temporización se desarrolla y verifica en testbench, sin hardware.
- Escribir el `.lpf` para la revisión 8.0 a partir del pinout de [`12_referencias_tecnicas.md`](12_referencias_tecnicas.md).
- **Pedirle al vendedor el modelo de IC driver y el archivo de configuración del panel.** Es gratis, tarda días en responder y condiciona la arquitectura entera — conviene mandarlo antes que cualquier orden de compra.

## Orden de compra sugerido

1. **Nivel 0 solo**, y validar el flujo completo. Es USD 28 de riesgo para confirmar que el toolchain, el programador y la revisión de placa funcionan.
2. En paralelo, el correo al vendedor del panel.
3. **Nivel 1** junto con la muestra de Fase 0 — misma orden, mismo envío.
4. **Nivel 2** antes de pasar del Paso 2 al 3.
5. **Nivel 3** cuando la matriz esté estable.

El camino crítico sigue siendo el envío desde China de los módulos y la respuesta del vendedor sobre el IC driver, no la placa FPGA.
