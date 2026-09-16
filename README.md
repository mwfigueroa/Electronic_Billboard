# Electronic Billboard — Cartel LED Exterior 56"

Proyecto de fabricación de cartel electrónico LED full-color para exterior (fachada), destinado a promoción de una empresa de tecnología.

> Estado: **Fase 1 — Diseño y compras** · Documentación v1.1 — plataforma del driver propio decidida ([`docs/10_plataforma_driver.md`](docs/10_plataforma_driver.md))

## Especificaciones resumidas

| Parámetro | Valor |
|---|---|
| Tamaño pantalla | 1280 × 640 mm (≈ 56,3" diagonal) |
| Configuración | 4 × 4 módulos P5 outdoor SMD (320×160 mm c/u) |
| Resolución | 256 × 128 px (32.768 px) |
| Brillo | > 4500 nits declarados; validar visibilidad a pleno sol |
| Protección | Uso exterior declarado; confirmar IP del panel. Gabinete IP54 |
| Distancia mín. de visualización | ~5 m |
| Contenido | Logo, texto, animaciones compatibles, reloj (programación por horarios) |
| Control (producción) | Huidu HD-WF4 (asíncrono, WiFi + USB, 4× HUB75) — HD2020 / HDSign |
| Control (driver propio) | Colorlight 5A-75B — FPGA Lattice ECP5-25, 8× HUB75, toolchain abierto |
| Alimentación | 220 V CA → 4× fuentes 5 V/60 A (Meanwell LRS-350-5), una por fila |
| Presupuesto objetivo | USD 500–1000 (estimado: ~754 puesta en marcha, ~807 con driver propio; sin envío ni impuestos) |

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
│   └── 16_cadena_completa.md    Cadena fuente → display de la ruta 5A-75B (integración)
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
└── hardware/                    (futuro: planos, CAD, fotos)
```

## Fases del proyecto

| # | Fase | Duración est. | Estado |
|---|---|---|---|
| 1 | Diseño y compras | 2–3 sem (envío AliExpress = camino crítico) | En curso |
| 2 | Fabricación estructura | 1 sem | Pendiente |
| 3 | Ensamblado y cableado en banco | 1 sem | Pendiente |
| 4 | Configuración controlador + contenido | 2–3 días | Pendiente |
| 5 | Sellado e instalación en fachada | 1–2 días | Pendiente |
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
