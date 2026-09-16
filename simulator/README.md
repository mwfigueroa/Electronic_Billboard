# Simulador de panel y app de contenido

Software del cartel ([`docs/14_software_contenido.md`](../docs/14_software_contenido.md)),
separado en dos paquetes por la **frontera del contrato de wire v1**:

- **`content/`** — lado app: playlist declarativa → composición → frames RGB888
  de 256×128. Incluye la app de publicación en vivo (`content/app.py`).
- **`panel_sim/`** — lado panel: gamma, cuantización, bitplanes, temporización
  BCM y máscara de LED. Incluye el visor del panel virtual y los **vectores
  dorados** contra los que se valida el HDL
  ([`../driver-5a75b/`](../driver-5a75b/README.md)).

La cadena de hardware que estos números validan está en
[`docs/16_cadena_completa.md`](../docs/16_cadena_completa.md).

## Qué es y qué no es

Es software puro. Responde *"cómo se vería esto en la pantalla"* y nada más:

- **Sí:** composición de texto/imagen/reloj, corrección de gamma, costo visible
  de la profundidad de color (4/5/6 bits), simulador de bitplanes para el HDL.
- **No:** el panel físico, ni circuitería de estímulo, ni los artefactos del
  refresco (ghosting, flicker de bits bajos, latencia de scan). Eso es hardware
  o simulación HDL — ver [`docs/15_notas_tecnicas.md`](../docs/15_notas_tecnicas.md).

## Instalación y uso

```bash
cd simulator
make test        # pytest
make hooks       # activa el pre-commit del repo (tests si el commit toca simulator/)
make app         # publica la playlist como fuente viva (MJPEG en 127.0.0.1:8080)
make editor      # editor web con preview en vivo (http://127.0.0.1:8090)
make render      # out/00_text.png, out/01_text.png, … con píxeles visibles
make view        # visor animado (requiere display)
make vectors     # regenera vectors/ para los testbenches
```

`make hooks` deja activo el pre-commit de `.githooks/`: corre la suite del
simulador cuando el commit toca `simulator/` y los testbenches HDL cuando toca
`driver-5a75b/`. Sin venv aborta con instrucciones (o `--no-verify` si el
cambio no toca código).

Los vectores incluyen los 15 planos esperados, el frame de entrada
(`frame_rgb888.mem`) y la LUT de gamma (`gamma_lut_*.mem`) que consume el
bloque HDL de [`../driver-5a75b/`](../driver-5a75b/README.md).

O directamente:

```bash
.venv/bin/python -m panel_sim.render examples/playlist.json -o out --scale 4
.venv/bin/python -m panel_sim.render examples/playlist.json --depth 4   # comparar 4 bits
.venv/bin/python -m panel_sim.viewer examples/playlist.json --scale 5
.venv/bin/python -m panel_sim.viewer examples/playlist.json --start 3  # arrancar en la escena
.venv/bin/python -m panel_sim.vectors -o vectors
```

El visor abre una ventana con el canvas ampliado a píxeles cuadrados con
**máscara de LED** (un gap negro entre píxeles, como el panel real), y una
barra de estado debajo del panel con el refresco BCM estimado, la distancia
equivalente y las teclas. Teclas:
`SPACE` pausa · `←/→` slide · `4/5/6` profundidad · `G` gamma 2.2 ↔ 1.0 ·
`+/-` distancia simulada · `R` reinicia · `S` captura PNG · `Q`/`ESC` salir.

La máscara se dibuja cuando cada píxel de panel ocupa ≥ 5 px de pantalla
(escala 5 o más, que es el default): con menos, el LED quedaría de 2 px y la
superficie encendida casi triplicaría la del módulo real (37 % a celda 3
contra el ~12 % medido). `--gap-frac` ajusta su fracción del paso (0.65 por
defecto, medido sobre la foto del módulo P5: el LED ocupa ~⅓ del paso, ~12 %
del área; `0` la desactiva) y `--led-shape round` (por defecto) dibuja el LED
circular con borde suavizado, como la lente del módulo real — `--led-shape
square` deja los píxeles cuadrados. El LED nunca baja de 2 px: con 1 px el
panel se vería más apagado que el real. A la distancia de emulación (p. ej.
5 m) el LED real es sub-píxel en el monitor: el visor lo avisa y muestra el
panel sin máscara, que es lo físicamente correcto.

En WSLg el visor fuerza `SDL_VIDEODRIVER=x11` con render por software: SDL se
cuelga al abrir la ventana sin `/dev/dri`. Si el entorno define esas variables
a mano, el visor no las pisa. Además, si `DISPLAY` apunta a la IP del host
(modo mirrored) y ese camino no responde, cae al socket local `:0` — es el
mismo servidor —, y si X no contesta en 20 s sale con un mensaje en vez de
quedarse colgado en silencio.

## Playlist

JSON estricto: una clave desconocida o un campo mal tipado es un error al
cargar (no un render a medias). Cada slide tiene `type` y `duration` (segundos).

```jsonc
{
  "version": 1,
  "display": { "width": 256, "height": 128, "depth": 5, "gamma": 2.2,
               "background": "#000000" },
  "slides": [
    { "type": "text",  "text": "HOLA", "size": 24, "color": "#ffffff",
      "align": "center", "valign": "middle", "duration": 4 },
    { "type": "text",  "text": "texto que se desplaza", "size": 16,
      "scroll": "left", "speed_px_s": 30, "duration": 12 },
    { "type": "image", "path": "logo.png", "duration": 4 },
    { "type": "clock", "format": "%H:%M:%S", "size": 48,
      "color": "#ffe040", "duration": 8 },
    { "type": "color", "color": "#102040", "duration": 1.5 }
  ]
}
```

- `text`: `size`, `color`, `background`, `font` (familia DejaVu o ruta `.ttf`),
  `align` (`left|center|right`), `valign` (`top|middle|bottom`),
  `scroll` (`left|right`), `speed_px_s`.
- `image`: `path` relativo a la playlist. Sin `scroll` entra en el canvas sin
  agrandarse; con `scroll` solo se limita por altura, para conservar el ancho
  de un banner y tener algo que desplazar. Acepta `speed_px_s`.
- `video`: `path` (MP4/WebM), `loop` (default `true`) y `fps` de decodificación
  (default 30). Se decodifica con ffmpeg (del sistema o `imageio-ffmpeg`) y se
  ajusta al canvas con letterbox negro. `make video` baja un clip de ejemplo
  (Sintel © Blender Foundation, CC-BY 3.0) y
  `make view PLAYLIST=examples/playlist_video.json` lo reproduce en el panel.
  El clip se eligió por su **paleta oscura**: ~40 % de sus subpíxeles cae bajo
  sRGB 39, el umbral donde 5 bits apaga (mediana sRGB ≈68) — es el peor caso a
  propósito, no reemplazar por material más brillante.
- `live`: fuente viva (contrato de wire v1, [`docs/14`](../docs/14_software_contenido.md)).
  `url` es la entrada de ffmpeg; `fps` la cadencia; y según el transporte,
  `format` (`rawvideo`, `x11grab`, `v4l2`, `mjpeg`), `pixel_format` y `size`.
  Si el panel se atrasa descarta cuadros y sigue el último. `make app` publica
  una fuente de ejemplo y `make view PLAYLIST=examples/playlist_live.json` la
  muestra en el panel.
- `clock`: `format` estilo `strftime`; se re-renderiza en cada frame con la
  hora local (o con `--time` en el render).
- `color`: `color` plano.

Cualquier slide acepta además un **horario** opcional:

```jsonc
{ "type": "text", "text": "Pleno día", "duration": 8,
  "desde": "08:00", "hasta": "22:00",
  "dias": ["lun", "mar", "mie", "jue", "vie"] }
```

- `desde`/`hasta`: `HH:MM`, con `hasta` exclusivo. Si `desde` es mayor que
  `hasta` la ventana cruza la medianoche (`22:00` → `06:00`).
- `dias`: subconjunto de `lun mar mie jue vie sab dom`; por defecto, todos.
- Fuera de la ventana el slide no se emite: el visor y la app lo saltan, y si
  no queda ninguno vigente se publica negro.
- Ejemplo completo: `examples/playlist_horarios.json`.

## Fuente viva: contrato de wire v1

La app de PC manda frames **RGB888 de 256×128** y el panel hace el resto
(gamma, cuantización, bitplanes, máscara): la app no sabe nada de LED. El
contrato y los transportes están en [`docs/14`](../docs/14_software_contenido.md).

```bash
make app                                          # MJPEG en 127.0.0.1:8080
make view PLAYLIST=examples/playlist_live.json    # el panel lo consume
```

| Transporte | Campos del slide `live` |
|---|---|
| MJPEG/HTTP (autodetectado) | `{"url": "http://host/stream.mjpg"}` |
| rawvideo sobre UDP | `{"url": "udp://127.0.0.1:5000", "format": "rawvideo", "size": "256x128"}` |
| Ventana X11 | `{"url": ":0.0+0,0", "format": "x11grab", "size": "256x128"}` |

La **app de referencia** es `content/app.py` (`make app`, con
`PLAYLIST=...` opcional): compone la playlist con el mismo `Timeline` del
simulador, respeta los horarios, recarga el archivo en caliente si cambia y
expone estado para supervisión:

| Ruta | Qué devuelve |
|---|---|
| `/stream.mjpg` | el stream MJPEG que consume el panel |
| `/status` | JSON: frames, errores, slide actual, antigüedad del último cuadro |
| `/` | texto con las rutas |

`examples/app_ejemplo.py` (`make demo`) es la **demo mínima del transporte**:
dibuja con Pillow crudo a propósito, para mostrar que cualquier lenguaje o
framework puede publicar el contrato sin conocer el proyecto. No es la app.
Si el stream se corta, el panel reintenta la conexión cada 2 s.

## Editor de playlist

`make editor` levanta un editor web local (sin dependencias) sobre la
playlist: lista los slides con sus campos, permite agregar/mover/borrar,
subir imágenes, previsualizar el **pipeline real del panel** (gamma +
cuantización) por MJPEG —incluso un slide puntual con el botón `ver`— y
guardar **validado** (un documento inválido se puede seguir editando, pero no
se escribe).

El circuito completo queda cerrado sin reiniciar nada: el editor guarda → la
app ve el mtime y recarga en caliente → el panel virtual lo muestra. El
preview del editor no dibuja la máscara de LED ni emula distancia: para eso
está el visor (`make view`).

## Convenciones

**Gamma.** Hay dos gammas distintas y conviene no mezclarlas:

- La de la **playlist** (`quantize`): lleva el valor codificado al ciclo de
  trabajo del panel, `duty = (v/255)**gamma`. El panel BCM es lineal en luz,
  así que 2.2 reproduce la respuesta sRGB; `gamma = 1` es el panel crudo.
- La del **monitor** (`to_display`, fija en `DISPLAY_GAMMA = 2.2`): para que
  el PNG y el visor muestren la luz que emitiría el panel, el nivel se
  re-codifica con `duty ** (1/2.2)`. Sin este paso todo preview sale mucho más
  oscuro que el panel real y la cuantización parece peor de lo que es.

Con el par completo, el toggle `G` demuestra lo que afirma: gamma 2.2 → el
gris medio aparece como ~130, igual que en el panel; gamma 1.0 → como ~189, el
"demasiado brillante" típico de un panel sin corregir.

**Bitplanes.** `[bit, canal, y, x]`, bit 0 = LSB, pre-mapeo de scan. El mapeo
1/8 del panel es específico del hardware y vive en `scan_mapper`
([`docs/11`](../docs/11_arquitectura_colorlight_5a75b.md)); acá no se inventa.

**Refresco.** `refresh_hz = f_clock / (2080 × (2^depth − 1))`, el modelo de
[`docs/11`](../docs/11_arquitectura_colorlight_5a75b.md): 2048 clocks de datos
por bitplane más 4 de blanking por cada uno de los 8 pasos de dirección, como
implementa `driver-5a75b/bcm_sequencer`. Con 12,5 MHz: 4 bits → 401 Hz,
5 bits → 194 Hz, 6 bits → 95 Hz.

## Emular la distancia real

El panel del proyecto mide 256 px × 5 mm = 1280 mm de ancho ([`docs/01`](../docs/01_especificaciones.md)).
Con una calibración de tu monitor, el visor dimensiona la ventana para
reproducir el **ángulo visual** de mirar el cartel desde una distancia dada:

```bash
# como estar a 5 m del cartel (distancia mínima de diseño)
.venv/bin/python -m panel_sim.viewer examples/playlist.json --panel-distance 5

# con tu monitor y tu distancia a la pantalla
.venv/bin/python -m panel_sim.viewer examples/playlist.json \
    --monitor-inch 27 --monitor-px 2560 --eye-cm 70 --panel-distance 5

# o vía make, con los mismos argumentos
make view ARGS="--panel-distance 5 --monitor-inch 32 --monitor-px 1920 --eye-cm 60"
```

La calibración por defecto es 24", 1920 px, ojos a 60 cm: **hay que ajustarla
al equipo real** o la emulación mide otra cosa. Con `+`/`-` la distancia
simulada se ajusta en vivo (la ventana se redimensiona) y el HUD muestra
siempre la distancia equivalente. Sin `--panel-distance`, la ventana mantiene
el zoom de `--scale` y el HUD indica a qué distancia real equivale.

Referencia rápida (24" 1080p a 60 cm): escala 2 ≈ 5,4 m · escala 3 ≈ 3,6 m ·
escala 4 ≈ 2,7 m.

## Estructura

```
content/             lado app (termina en RGB888)
├── playlist.py      carga y validación del JSON (con horarios)
├── canvas.py        primitivas Pillow: texto, imágenes, grilla
├── timeline.py      composición determinista slide → frame (horarios incluidos)
├── video.py         decodificación de video y streams vía ffmpeg
└── app.py           CLI: publica la playlist como fuente viva

panel_sim/           lado panel (empieza en RGB888)
├── quantize.py      gamma y cuantización a N bits
├── bitplanes.py     RGB → bitplanes (referencia de oro del HDL)
├── timing.py        tasa de refresco del modelo BCM
├── viewing.py       emulación de distancia (calibración del monitor)
├── render.py        CLI: PNG por slide
├── viewer.py        CLI: visor pygame animado
├── editor.py        CLI: editor web con preview (editor.html)
└── vectors.py       CLI: vectores dorados para testbenches
```

## Pendientes

- Mapeo de scan del panel: es hardware, no simulador.
- UI de autoría: hay un editor mínimo que cumple lo que pedía
  [`docs/14`](../docs/14_software_contenido.md) (edita el archivo y
  previsualiza el pipeline); una UI completa sigue postergada.
- Supervisión del proceso en producción: la app corre en primer plano y
  `/status` es la señal para vigilarla (el supervisor —systemd, kiosco— queda
  fuera de este repo).
