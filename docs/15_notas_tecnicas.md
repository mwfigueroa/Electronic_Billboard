# 15 — Notas técnicas y bitácora

## Propósito

Dos cosas viven acá:

1. **Observaciones de diseño** que surgieron del análisis y no tienen un lugar natural en los documentos estructurados — consecuencias, implicancias y cosas que conviene tener presentes pero que no son especificación.
2. **Bitácora de bring-up**: el registro de lo que se vaya encontrando al trabajar con el hardware real.

Lo que **no** va acá: datos de referencia. Pinouts, part numbers, comandos y specs viven en [`12_referencias_tecnicas.md`](12_referencias_tecnicas.md) y no se duplican, porque dos copias de un dato se desincronizan. Si algo de acá se vuelve especificación estable, se muda al documento que corresponda y queda solo el enlace.

---

## Observaciones de diseño

### El recurso ajustado es la BRAM, no las LUTs

Con 24.300 LUT4, el ECP5-25 sobra para lo que pide este proyecto. Los ocho serializadores HUB75 y el secuenciador BCM son lógica chica; incluso sumando el softcore VexRiscv de LiteX queda margen.

**El límite real es la BRAM**: 126 KB contra los 60 KB que ocupa un frame de 5 bits por color. Ver el presupuesto en [`11_arquitectura_colorlight_5a75b.md`](11_arquitectura_colorlight_5a75b.md).

Consecuencia práctica: al optimizar, no tiene sentido pelear por LUTs. Si hay que recortar, se recorta profundidad de color o se empuja el framebuffer a SDRAM.

### 12,5 y 25 MHz son los clocks "gratis"

El clock de entrada de la placa es de **25 MHz**. Eso hace que los dos puntos de operación más interesantes salgan sin gimnasia de PLL:

| Clock de píxel | Cómo se obtiene |
|---|---|
| **25 MHz** | Entrada directa, sin PLL |
| **12,5 MHz** | División por 2 |
| 16 MHz | Requiere PLL con relación 16/25 |

El objetivo inicial de 12,5 MHz y el techo de 25 MHz están convenientemente alineados con el hardware. **16 MHz es el punto incómodo**, aunque las tablas de refresco lo incluyan — si hay que elegir un paso intermedio, conviene revisar si 12,5 alcanza antes de meter un PLL.

### Los ocho puertos van obligatoriamente en lockstep

En la revisión 8.0, las señales `A`–`E`, `CLK`, `LAT` y `OE` están **compartidas entre los ocho conectores** — cada puerto tiene solo sus seis líneas RGB propias.

Consecuencias para el HDL:

- Las ocho cadenas están siempre en el **mismo paso de dirección y el mismo bitplane**. No se puede desfasar un puerto respecto de otro.
- El framebuffer debe organizarse de modo que los datos de las ocho cadenas para un paso de dirección dado estén disponibles **simultáneamente**. Esto condiciona el layout de la BRAM de bitplanes, no solo su tamaño.
- **Los 16 módulos tienen que ser idénticos** en scan y temporización. No se pueden mezclar paneles distintos en puertos distintos. Para este proyecto no es limitación —son 16 módulos del mismo lote— pero descarta reusar la placa con paneles heterogéneos.

Es la misma restricción que tenía la HD-WF4 con sus dos bancos. La diferencia está en que acá los ocho transmiten a la vez en vez de alternarse, que es de donde sale la ganancia de refresco.

### El simulador de software precede al hardware

La conversión RGB → bitplanes existe dos veces, en software y en HDL. Escribirla primero en Python da un vector dorado contra el cual validar el Verilog en testbench. Ver [`14_software_contenido.md`](14_software_contenido.md).

Vale la pena insistir en el orden: **el simulador no es una herramienta auxiliar, es la referencia de corrección del driver.** Diagnosticar bugs de bitplanes mirando un panel es muy caro; compararlos contra vectores generados en software es trivial.

---

## Entorno de trabajo

Notas específicas de este entorno (Windows 11), consolidadas. El detalle del toolchain está en [`12_referencias_tecnicas.md`](12_referencias_tecnicas.md) §5.

| Tema | Nota |
|---|---|
| Síntesis, P&R, simulación | Funcionan nativo sobre Windows x64 con oss-cad-suite |
| Acceso USB del programador | Es lo que da pelea. Nativo puede necesitar WinUSB vía Zadig; bajo WSL2 hace falta `usbipd-win` para pasar el dispositivo |
| Estrategia sugerida | Build donde sea cómodo, carga JTAG desde donde el USB funcione sin pelear. No hace falta que sea el mismo entorno |
| Finales de línea | Git avisa en cada operación que los `.md` están en LF y los convertirá a CRLF. No rompe nada pero ensucia diffs. Se fija con un `.gitattributes` de una línea — **pendiente** |

---

## Bitácora de bring-up

Registro de hallazgos con el hardware real. Una fila por observación, con fecha. Este registro alimenta las correcciones a los documentos estructurados.

| Fecha | Paso | Observación | Resolución |
|---|---|---|---|
| — | — | *Sin entradas: el hardware todavía no se compró* | — |

### Qué conviene registrar

- Revisión serigrafiada de la placa recibida y cualquier diferencia contra `hardware_V<rev>.md` de chubby75.
- Resolución de las discrepancias listadas en [`12_referencias_tecnicas.md`](12_referencias_tecnicas.md) §7 — en particular el pin del LED de usuario (T6 según chubby75, P11 según weigu).
- **Modelo de IC driver leído de la serigrafía del panel**, y a qué familia pertenece.
- Mapeo de scan 1/8 descubierto, con el método usado.
- Clock de píxel máximo estable y a partir de dónde aparece ghosting.
- Comportamiento de los 74HC245T con entrada de 3,3 V al subir el clock.
- Refresco medido contra el calculado.
- Cualquier dato de ingeniería inversa que resulte estar mal.
