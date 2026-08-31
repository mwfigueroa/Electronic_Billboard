# Electronic Billboard — Cartel LED Exterior 50"

Proyecto de fabricación de cartel electrónico LED full-color para exterior (fachada), destinado a promoción de una empresa de tecnología.

> Estado: **Fase 1 — Diseño y compras** · Documentación inicial v1.0

## Especificaciones resumidas

| Parámetro | Valor |
|---|---|
| Tamaño pantalla | 1120 × 640 mm (≈ 50,8" diagonal) |
| Configuración | 7 × 4 módulos P5 outdoor SMD (160×160 mm c/u) |
| Resolución | 224 × 128 px (28.672 px) |
| Brillo | ≥ 5000 nits (visible a pleno sol) |
| Protección | Frontal IP65, gabinete IP54 |
| Distancia mín. de visualización | ~5 m |
| Contenido | Logo, texto, animaciones, video corto, reloj (playlist programada) |
| Control | Colorlight A35 (async, WiFi) — software LEDVISION |
| Alimentación | 220 V CA → 3× fuentes 5 V/60 A (Meanwell LRS-350-5) |
| Presupuesto objetivo | USD 500–1000 (estimado: ~795) |

## Arquitectura del sistema

```
                220 V CA
                   │
        Diferencial 30 mA → Breaker 2P 10A → SPD
                   │
      ┌────────────┼────────────┐
      │            │            │
  LRS-350-5    LRS-350-5    LRS-350-5     (5 V / 60 A c/u)
      │            │            │
      └──────── 5 V bus ────────┘
         │         │         │
      ~10 módulos ~10 módulos ~10 módulos  (cable 12 AWG)

  Colorlight A35 ── puerto HUB75 #1 → filas 1–2 (14 módulos)
  (WiFi/app)   ──── puerto HUB75 #2 → filas 3–4 (14 módulos)
```

## Estructura del repositorio

```
├── README.md                  (este archivo)
├── docs/
│   ├── 01_especificaciones.md   Especificaciones técnicas detalladas
│   ├── 02_bom.md                Lista de materiales y proveedores
│   ├── 03_electrico.md          Arquitectura eléctrica y cableado
│   ├── 04_estructura.md         Gabinete, montaje en fachada, viento
│   ├── 05_fabricacion_fases.md  Fases, ensamblado y pruebas
│   └── 06_control_contenido.md  Configuración A35 / LEDVISION y contenido
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

## Pendientes administrativos

- [ ] Permiso municipal de publicidad / anunciante
- [ ] Conexión fija 220 V por electricista matriculado
- [ ] Seguro de responsabilidad civil (cartel da a vía pública)
