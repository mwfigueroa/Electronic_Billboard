# Electronic Billboard — Cartel LED Exterior 56"

Proyecto de fabricación de cartel electrónico LED full-color para exterior (fachada), destinado a promoción de una empresa de tecnología.

> Estado (2026-09-21): **diseño y anteproyecto completos** — software de contenido y emulador (147 tests), driver HDL validado contra vectores dorados, y mecánica de mástil con brazo (R2.1) verificada en CAD, todo sin hardware. **Pendiente**: muestra de Fase 0 (IC driver, fijación, IP del módulo), estudio de suelos, ordenanza y cálculo firmado, y el `scan_mapper` que necesita el panel — ver [`docs/05`](docs/05_fabricacion_fases.md), [`18`](docs/18_monoposte.md) y [`19`](docs/19_costos_argentina.md).

## Especificaciones resumidas

| Parámetro | Valor |
|---|---|
| Tamaño pantalla | 1280 × 640 mm (≈ 56,3" diagonal) |
| Configuración | 4 × 4 módulos P5 outdoor SMD (320×160 mm c/u) |
| Resolución | 256 × 128 px (32.768 px) |
| Brillo | > 4500 nits declarados; validar visibilidad a pleno sol |
| Protección | Uso exterior declarado; confirmar IP del panel. Gabinete: objetivo IP54, a ensayar (docs/17) |
| Distancia mín. de visualización | ~5 m |
| Contenido | Logo, texto, animaciones compatibles, reloj (programación por horarios) |
| Control (producción) | Huidu HD-WF4 (asíncrono, WiFi + USB, 4× HUB75) — HD2020 / HDSign |
| Control (driver propio) | Colorlight 5A-75B — FPGA Lattice ECP5-25, 8× HUB75, toolchain abierto |
| Alimentación | 220 V CA → 4× fuentes 5 V/60 A (Meanwell LRS-350-5), una por fila |
| Presupuesto | Materiales importables ~USD 574 FOB (docs/02); proyecto completo con mástil, fundación, instalación y honorarios: USD 5.450–6.590 al MEP de sept. 2026, suponiendo venta por corte de tubos (docs/19) |

## Arquitectura del sistema

```
                220 V CA
                   │
        Diferencial 30 mA → Breaker 2P 10A → bornera CA
                                      ├── SPD tipo 2 → PE
                   │
      ┌────────┬────────┬────────┐
      │        │        │        │
  LRS-350-5 LRS-350-5 LRS-350-5 LRS-350-5  (5 V / 60 A c/u)
      │        │        │        │
    fila 1   fila 2   fila 3   fila 4 + HD-WF4

   Huidu HD-WF4 ── HUB75 #1 → fila 1 (4 módulos)
   (WiFi/USB)   ── HUB75 #2 → fila 2 (4 módulos)
                 ── HUB75 #3 → fila 3 (4 módulos)
                 ── HUB75 #4 → fila 4 (4 módulos)
```

No unir las salidas positivas de fuentes distintas; compartir solo la referencia GND de datos y potencia.

## Dos rutas de control

El proyecto mantiene dos rutas deliberadamente separadas. La de producción no depende de la experimental.

| | Producción | Driver propio |
|---|---|---|
| Hardware | Huidu HD-WF4 | **Colorlight 5A-75B** (FPGA ECP5-25) |
| Software | HD2020 / HDSign | HDL propio + LiteX, toolchain abierto |
| Topología | 4 cadenas de 4 módulos | 8 cadenas de 2 módulos |
| Refresco | Según firmware Huidu | 5 bits/color a ~194 Hz (193,9 medidos en simulación) |
| Estado | Ruta de puesta en marcha | En diseño |

El cableado de potencia 5 V es idéntico en ambas: una fuente por fila con dos inyecciones. Solo cambia el reparto de las cadenas de datos. La elección de plataforma y los números que la sustentan están en [`docs/10_plataforma_driver.md`](docs/10_plataforma_driver.md).

## Estructura del repositorio

```
├── README.md                  (este archivo)
├── docs/
│   ├── 01_especificaciones.md   Especificaciones técnicas detalladas
│   ├── 02_bom.md                Lista de materiales y proveedores
│   ├── 03_electrico.md          Arquitectura eléctrica y cableado
│   ├── 04_estructura.md         Gabinete, montaje en fachada, viento
│   ├── 05_fabricacion_fases.md  Fases, ensamblado y pruebas
│   ├── 06_control_contenido.md  Configuración Huidu HD-WF4 y contenido
│   ├── 07_diagrama_bloques.md   Arquitectura funcional de potencia y control
│   ├── 08_hub75e_y_panel_p5.md  Señales HUB75E y ficha de compra del panel
│   ├── 09_firmware_propio_hd_wf4.md Análisis del firmware ESP-IDF sobre HD-WF4 (superado)
│   ├── 10_plataforma_driver.md  Elección de plataforma del driver — registro de decisión
│   ├── 11_arquitectura_colorlight_5a75b.md Arquitectura del driver sobre FPGA ECP5
│   ├── 12_referencias_tecnicas.md Datasheets, pinout, familias de IC y entorno de desarrollo
│   ├── 13_bom_desarrollo.md     Hardware de banco para desarrollar el driver
│   ├── 14_software_contenido.md Modelo del software de contenido (PC y cartel)
│   ├── 15_notas_tecnicas.md     Observaciones de diseño y bitácora de bring-up
│   ├── 16_cadena_completa.md    Cadena fuente → display de la ruta 5A-75B (integración)
│   ├── 17_montaje_y_proteccion.md Gabinete LED · revisión constructiva R2
│   ├── 18_monoposte.md          Mástil con brazo lateral, fundación y altura libre · R2.1
│   └── 19_costos_argentina.md   Estimación de costos en pesos, mercado argentino (sept. 2026)
├── simulator/                 App de contenido + simulador de panel (docs/14)
│   ├── README.md              Uso, esquema de playlist (con horarios) y convenciones
│   ├── Makefile               make test / app / demo / render / view / vectors
│   ├── content/               Lado app: playlist, composición, video y publicación en vivo
│   ├── panel_sim/             Lado panel: gamma, bitplanes, visor y vectores dorados
│   ├── examples/              Playlists de ejemplo, logo y escena
│   ├── tests/                 Tests del pipeline (pytest)
│   └── vectors/               Vectores dorados para los testbenches del HDL
├── .githooks/                 pre-commit: tests de simulator/ y driver-5a75b/
├── driver-5a75b/              Bloques HDL del driver propio (docs/11) + top de integración y bitstream
├── foto/                      Referencias: módulo P5 (máscara del simulador) y monoposte (docs/18)
└── hardware/cad/              CAD R2, verificaciones y ficha HTML/PDF (docs/17 y 18)
```

### Previa mecánica R2.1

R2.1 adopta tubos comerciales **120 × 120 × 6,35 mm para el mástil** y
**120 × 120 × 4,75 mm para el brazo**. El gabinete conserva su revisión R2.

La revisión constructiva del soporte y gabinete está en
[`docs/17`](docs/17_montaje_y_proteccion.md) y [`docs/18`](docs/18_monoposte.md).
Los entregables regenerables están en `hardware/cad/build/` (**no está en git**:
se genera localmente con los comandos de abajo): `especificaciones_cartel.{pdf,html,md}`,
`monoposte.FCStd`, `monoposte.step`, siete vistas y los documentos de costos
(`costos_cartel`, `bom_cartel` y `bom_desarrollo`, en MD/HTML/PDF).
Incluyen correcciones geométricas y observaciones pendientes; no son planos
estructurales liberados para fabricar.

Desde una terminal de Windows con FreeCAD 1.1 instalado:

```bat
"C:\Program Files\FreeCAD 1.1\bin\freecad.exe" P:\Billboard\hardware\cad\vistas.py
"C:\Program Files\FreeCAD 1.1\bin\python.exe" P:\Billboard\hardware\cad\medir.py
"C:\Program Files\FreeCAD 1.1\bin\python.exe" P:\Billboard\hardware\cad\verificar_step.py
"C:\Program Files\FreeCAD 1.1\bin\python.exe" P:\Billboard\hardware\cad\especificaciones.py
```

Esperar a que la GUI termine antes de ejecutar los pasos siguientes. La ficha
comprueba hashes del modelo y las vistas y no acepta un PDF viejo como resultado
de una generación fallida. El render de vistas usa Pillow; el PDF requiere Edge
o Chrome. `build/` está excluido de Git: se genera localmente.

Alternativa PDF portable (utilizada para la entrega R2): generar la ficha con
`especificaciones.py --sin-pdf` en Python de FreeCAD y, en un entorno Python con
WeasyPrint, ejecutar `python hardware/cad/render_pdf.py`. Dependencias en
`hardware/cad/requirements-pdf.txt`; en Linux se necesitan las bibliotecas del
sistema de Pango (en WSL: `python3 -m venv hardware/cad/.venv &&
hardware/cad/.venv/bin/pip install -r hardware/cad/requirements-pdf.txt`; el
`.venv` queda ignorado por git). El PDF se publica de forma atómica y su hash queda
en `build/revision_documental.json`. Con Edge/Chrome el PDF sale sin pie ni
numeración: Chromium ignora las cajas de margen `@page`.

Los documentos de costos se regeneran sin FreeCAD: `python hardware/cad/render_costos.py`
convierte `docs/19_costos_argentina.md`, `docs/02_bom.md` y
`docs/13_bom_desarrollo.md` a MD/HTML/PDF en `build/` (usa WeasyPrint si está
instalado; si no, Edge o Chrome headless) y deja los hashes de fuentes y
salidas en `build/costos_render.json`.

## Fases del proyecto

| # | Fase | Duración est. | Estado |
|---|---|---|---|
| 1 | Diseño y compras | 2–3 sem (envío AliExpress = camino crítico) | En curso |
| 2 | Fabricación estructura | 1 sem | Pendiente |
| 3 | Ensamblado y cableado en banco | 1 sem | Pendiente |
| 4 | Configuración controlador + contenido | 2–3 días | Pendiente |
| 5 | Fundación, izaje e instalación del mástil (docs/18) | 1–2 sem con curado | Pendiente |
| 6 | Test de estrés 24 h y puesta en marcha | 1 día | Pendiente |

### Track paralelo — driver propio

Se desarrolla sobre banco, sin bloquear las fases de arriba. Detalle en [`docs/11_arquitectura_colorlight_5a75b.md`](docs/11_arquitectura_colorlight_5a75b.md).

| # | Paso | Estado |
|---|---|---|
| 0 | Identificar revisión de placa y respaldar bitstream de fábrica | Pendiente |
| 1 | Un módulo, un puerto, 1 bit por color | Pendiente |
| 2 | Descubrir el mapeo de scan 1/8 del panel | Pendiente |
| 3 | BCM y profundidad de color | Pendiente |
| 4 | Ocho puertos, matriz completa | Pendiente |
| 5 | Contenido, red y horarios | Pendiente |
| 6 | Estrés 24 h | Pendiente |

## Pendientes administrativos

- [ ] Permiso municipal de publicidad / anunciante
- [ ] Conexión fija 220 V por electricista matriculado
- [ ] Seguro de responsabilidad civil (cartel da a vía pública)
