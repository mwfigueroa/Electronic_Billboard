# 14 — Modelo del software de contenido

> **Estado: núcleo implementado.** El pipeline descrito acá vive en [`../simulator/`](../simulator/README.md): playlist → canvas → gamma y cuantización → PNG, visor animado y vectores dorados de bitplanes. Las decisiones abiertas de la sección final siguen abiertas. Complementa a [`11_arquitectura_colorlight_5a75b.md`](11_arquitectura_colorlight_5a75b.md), que cubre el lado FPGA.

## Alcance

Todo lo que está por encima del driver de panel: qué corre en la PC, qué corre en el cartel, y cuál es el contrato entre ambos.

## Reparto PC / cartel

El cartel debe ser **autónomo** — [`06_control_contenido.md`](06_control_contenido.md) ya lo establece: no hay PC conectada en operación normal. Eso fuerza un reparto deliberadamente asimétrico.

| Responsabilidad | PC | Cartel |
|---|---|---|
| Diseño y layout | Sí | No |
| Render de texto, fuentes e imágenes | **Sí** | No |
| Cuantización y corrección de gamma | No | **Sí** |
| Playlist y horarios | Define | **Ejecuta** |
| Composición de elementos dinámicos | No | Sí (reloj) |

**Principio rector: la PC manda píxeles, no instrucciones de dibujo.** El cartel es un reproductor tonto y confiable; la gamma y la cuantización quedan de su lado porque dependen del panel, no del contenido (contrato de wire v1).

Nada de motores de layout, decodificación de imágenes ni rasterizado de fuentes corriendo sobre un VexRiscv. Es donde estos proyectos se empantanan, y no compra nada: el contenido de cartelería cambia cada varios segundos, no cada frame.

### La excepción: el reloj

El reloj cambia cada segundo, así que algo tiene que componerse en el dispositivo. Se resuelve con el mínimo render posible: la PC manda un **sprite sheet de los diez dígitos ya rasterizados**, y el cartel hace blit sobre un fondo estático.

Componer sprites es trivial. Rasterizar fuentes no. La frontera se traza ahí.

## Capas del pipeline

```
Playlist declarativa (JSON)               ┐
        ↓                                 │
Composición → canvas RGB888 256 × 128     │ app de PC
        ↓                                 │
[ contrato de wire v1: RGB888 ]  ←────────┘ frontera PC ↔ panel
        ↓
Gamma + cuantización a N bits             ┐
Serialización a bitplanes                 │ panel
        ↓                                 │ (el simulador implementa el lado
FPGA                                      ┘  panel y es la referencia)
```

Cada capa es una **función pura**: sin reloj, sin red, sin estado global. Eso las hace testeables sin hardware, que es la propiedad que permite construir todo esto antes de que llegue nada de China. Con el contrato v1, gamma, cuantización y bitplanes corren en el panel; el simulador los implementa para el preview y para generar los vectores dorados del HDL.

### La serialización existe dos veces

La conversión RGB → bitplanes aparece en el pipeline de software **y** en el HDL, como `rgb_to_bitplane` en [`11_arquitectura_colorlight_5a75b.md`](11_arquitectura_colorlight_5a75b.md).

Escribirla primero en software da una **implementación de referencia contra la cual validar el Verilog** en testbench. Los bugs de bitplanes en HDL son horribles de diagnosticar mirando un panel; contra un vector dorado generado en software son triviales.

Es una duplicación deliberada, no un descuido. Conviene que ambas versiones compartan los mismos vectores de prueba.

## Por dónde empezar: el simulador de panel

La primera pieza a construir es un **simulador**, no la UI ni el transporte:

1. Lee una playlist declarativa.
2. Compone cada slide a un canvas de 256 × 128.
3. Aplica gamma y cuantiza a 4, 5 o 6 bits por color.
4. Emite PNG **escalado con píxeles cuadrados visibles**, simulando el paso P5.

> Implementado en [`../simulator/`](../simulator/README.md) (paquete `panel_sim`): el mismo pipeline, con salida PNG, visor animado en tiempo real y vectores dorados de bitplanes para los testbenches del HDL. La estimación de ~200 líneas quedó corta: son ~1.100 de código más ~540 de tests.

Rinde cuatro cosas de una sola vez:

- **Responde una pregunta de diseño hoy abierta.** [`06_control_contenido.md`](06_control_contenido.md) afirma que un logo complejo pierde detalle a esta resolución, pero es una suposición: nadie lo vio todavía.
- **Hace visible el costo de la profundidad de color.** El punto de operación de [`11`](11_arquitectura_colorlight_5a75b.md) elige 5 bits sobre una tabla de refresco, sin haber mirado qué se pierde entre 8 y 5 bits.
- **Construye el pipeline real**, no un prototipo descartable.
- Queda como **arnés de regresión permanente** y como referencia dorada del HDL.

Es el único componente del proyecto que puede estar funcionando sin comprar nada — ver [`13_bom_desarrollo.md`](13_bom_desarrollo.md).

## El contrato de wire

Se define inmediatamente después del simulador, y es **lo único que se trata como contrato serio**: versionado explícito desde la primera versión.

Todo lo que está por encima se puede reescribir libremente mientras el contrato aguante. El contrato en cambio es caro de cambiar, porque vive simultáneamente en el HDL, en el firmware de contenido y en la herramienta de la PC.

### v1 — frames RGB888 por transporte estándar (decidido)

La app de PC manda **frames RGB888 de 256×128**, uno detrás del otro, y el panel hace gamma, cuantización, bitplanes y refresco. La profundidad de color y la gamma quedan del lado del panel: la app no necesita saber nada de LED.

| | |
|---|---|
| Frame | 256×128 px, RGB888 entrelazado por píxel (R,G,B), fila por fila = 98.304 bytes |
| Cadencia | hasta 30 fps; si el panel se atrasa descarta cuadros y sigue el último |
| Transporte 1 | **MJPEG sobre HTTP** (estándar de cámaras IP): la app sirve `multipart/x-mixed-replace` |
| Transporte 2 | **rawvideo sobre UDP**: `-f rawvideo -pixel_format rgb24 -video_size 256x128 -i udp://host:puerto` |
| Transporte 3 | **X11**: la app dibuja en una ventana de 256×128 y el panel captura con `x11grab` |
| Implementación de referencia | slide `live` del simulador (`../simulator/`, app de ejemplo incluida) |

Por qué RGB y no bitplanes: la app no debe cambiar cuando se mueve la profundidad de color del panel, y el presupuesto de red es trivial para cartelería (98 KB por frame, ~24 Mbit/s en el peor caso a 30 fps). Mandar bitplanes queda como posible v2 si algún enlace lo pide.

## Qué no hacer todavía

**La UI de autoría.** Es lo más visible y lo más tentador, pero es lo más barato de cambiar y lo último que se necesita. Mientras la playlist sea un archivo declarativo editable a mano, la UI es un lujo. Si aparece, que sea un editor de ese archivo con preview del simulador — nunca una aplicación con su propio modelo de datos paralelo.

**El transporte de red y LiteX.** Entran en el Paso 5 del bring-up, cuando ya haya algo que transportar.

## Decisiones abiertas

- ~~Si el wire transporta RGB y el FPGA serializa, o si la PC manda bitplanes ya armados~~ — **resuelto para v1: la PC manda RGB888**; bitplanes queda como posible v2.
- Formato de la playlist declarativa.
- Si el cartel guarda la playlist en la SPI flash o en la SDRAM con respaldo.
- Cómo se maneja la conmutación de contenido sin tearing — se relaciona con el doble buffer del presupuesto de memoria de [`11`](11_arquitectura_colorlight_5a75b.md).
