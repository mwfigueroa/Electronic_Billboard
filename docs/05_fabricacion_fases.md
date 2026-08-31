# 05 — Fases de fabricación, ensamblado y pruebas

## Fase 1 — Diseño y compras (2–3 semanas)

- [x] Especificaciones definidas
- [ ] Cotizar módulos P5 outdoor (28 + 2 de repuesto) — mismo lote/vendedor
- [ ] Comprar controlador Colorlight A35
- [ ] Comprar fuentes LRS-350-5 (distribuidor autorizado)
- [ ] Comprar protección CA (diferencial, breaker, SPD)
- [ ] Comprar estructura (perfiles, chapa, juntas, inox)
- [ ] Iniciar trámite de permiso municipal (en paralelo)

## Fase 2 — Estructura (1 semana)

- [ ] Corte de perfiles según plano del `04_estructura.md`
- [ ] Armado de bastidor (escuadras + tornillería inox, verificar escuadre con diagonal)
- [ ] Fijación de rieles de módulos (paso 160 mm entre centros de fila)
- [ ] Montaje de puerta trasera con bisagras y junta
- [ ] Marco frontal con junta EPDM
- [ ] Rejillas de ventilación con filtro y drenajes
- [ ] Pintura/anodizado si corresponde

## Fase 3 — Ensamblado y cableado en banco (1 semana)

> **Nunca montar módulos en fachada sin probarlos antes en banco.**

- [ ] Test individual de los 28 módulos con fuente de laboratorio + patrón de colores (rojo/verde/azul/blanco/negro): detectar LEDs muertos, filas caídas, uniformidad
- [ ] Reclamo a vendedor por módulos fallados (dentro del plazo de protección de compra)
- [ ] Montaje de módulos al gabinete con juntas
- [ ] Cableado 5 V: troncales 12 AWG + inyección en extremos de fila
- [ ] Cableado de datos HUB75: puerto 1 → filas 1–2, puerto 2 → filas 3–4
- [ ] Instalación de fuentes, diferencial, breaker, SPD, borneras
- [ ] Medición de aislación y continuidad de tierra antes de energizar

## Fase 4 — Configuración y contenido (2–3 días)

- [ ] Configuración del A35 en LEDVISION: layout receptores, scan, gamma, refresco
- [ ] Calibración de brillo con sensor de luz ambiente
- [ ] Playlist inicial: logo + promos + reloj/fecha (ver `06_control_contenido.md`)
- [ ] Configuración WiFi y acceso remoto

## Fase 5 — Sellado e instalación (1–2 días)

- [ ] Re-torque de tornillería de módulos y fuentes
- [ ] Sellado final de pasacables y fijaciones
- [ ] Instalación de subestructura y gabinete en fachada (6× anclajes M10)
- [ ] Conexión de línea fija 220 V — **electricista matriculado**
- [ ] Verificación de puesta a tierra (< 5 Ω)

## Fase 6 — Puesta en marcha (1 día)

- [ ] Test de estrés **24 h a patrón blanco full** monitoreando:
  - [ ] Temperatura de las 3 fuentes (≤ 60 °C)
  - [ ] Temperatura interior del gabinete (≤ 15 °C sobre ambiente)
  - [ ] Tensión 5 V en módulo más lejano (≥ 4,85 V)
  - [ ] Olor/humo, conectores calientes (termografía si hay disponible)
- [ ] Test de estanqueidad: simulación de lluvia con manguera suave frontal 15 min → inspección interior
- [ ] Fotos finales, checklist firmado, entrega

## Registro de incidencias

Mantener una fila por problema detectado con fecha, descripción y resolución. Este registro alimenta la garantía con proveedores.
