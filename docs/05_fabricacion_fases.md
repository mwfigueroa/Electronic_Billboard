# 05 — Fases de fabricación, ensamblado y pruebas

## Fase 0 — Muestra y compatibilidad (antes del lote completo)

- [ ] Comprar 2× módulos LYERAEEN P5-320x160-8S-1921, una HD-WF4, cables flat compatibles y una fuente de 5 V / 60 A.
- [ ] Pedir al vendedor pinout, tipo de IC driver, archivo de configuración Huidu y confirmación escrita de compatibilidad con HD-WF4.
- [ ] Probar cada módulo individualmente en los cuatro puertos de la HD-WF4.
- [ ] Encadenar ambos módulos y comprobar `IN` / `OUT`, scan 1/8, rojo/verde/azul/blanco/negro, texto y animación.
- [ ] Medir tensión en ambos módulos a blanco completo; verificar que no haya conectores o cables calientes.
- [ ] Evaluar brillo a pleno sol y confirmar que >4500 nits sea aceptable para la ubicación.
- [ ] **Pedir al vendedor el modelo exacto de IC driver del panel** — define la arquitectura del driver propio, ver [`08_hub75e_y_panel_p5.md`](08_hub75e_y_panel_p5.md).
- [ ] Si se desarrollará el driver propio: los dos módulos de muestra sirven también para el bring-up de la Colorlight 5A-75B, según [`11_arquitectura_colorlight_5a75b.md`](11_arquitectura_colorlight_5a75b.md). La HD-WF4 no se toca.
- [ ] Comprar los 14 módulos restantes más 2 de repuesto solo después de aprobar esta muestra.

## Fase 1 — Diseño y compras (2–3 semanas)

- [x] Especificaciones definidas
- [ ] Cotizar módulos LYERAEEN P5-320x160-8S-1921 (16 + 2 de repuesto) — mismo lote/vendedor
- [ ] Comprar controlador Huidu HD-WF4 y sensor de brillo compatible
- [ ] Comprar 4× fuentes LRS-350-5, una por fila (distribuidor autorizado)
- [ ] Comprar protección CA (diferencial, breaker, SPD)
- [ ] Comprar estructura (perfiles, chapa, juntas, inox)
- [ ] Iniciar trámite de permiso municipal (en paralelo)

## Fase 2 — Estructura (1 semana)

> Configuración vigente: gabinete R2 y mástil con brazo R2.1
> ([`17`](17_montaje_y_proteccion.md), [`18`](18_monoposte.md)). Los pasos de
> abajo describen el gabinete de fachada original; el orden de obra real es:
> muestra del módulo → cálculo firmado y estudio de suelos → taller (bastidor de
> acero, envolvente, brazo soldado al montante, brida) → prueba de extracción de
> módulos en banco.

- [ ] Corte de perfiles según plano del `04_estructura.md`
- [ ] Armado de bastidor (escuadras + tornillería inox, verificar escuadre con diagonal)
- [ ] Fijación de rieles de módulos (paso 160 mm entre centros de fila, longitud 1280 mm)
- [ ] Montaje de puerta trasera con bisagras y junta
- [ ] Marco frontal con junta EPDM
- [ ] Ventiladores termostatados, entradas filtradas, salidas superiores y drenajes
- [ ] Pintura/anodizado si corresponde

## Fase 3 — Ensamblado y cableado en banco (1 semana)

> **Nunca montar módulos en fachada sin probarlos antes en banco.**

- [ ] Test individual de los 16 módulos con fuente de laboratorio + patrón de colores (rojo/verde/azul/blanco/negro): detectar LEDs muertos, filas caídas, uniformidad
- [ ] Reclamo a vendedor por módulos fallados (dentro del plazo de protección de compra)
- [ ] Montaje de módulos al gabinete con juntas
- [ ] Cableado 5 V: dos ramas 12 AWG con fusible de 20 A en cada extremo de cada fila
- [ ] Cableado de datos HUB75: un puerto HD-WF4 por fila, cuatro módulos encadenados
- [ ] Instalación de fuentes, diferencial, breaker, SPD, borneras
- [ ] Medición de aislación y continuidad de tierra antes de energizar

## Fase 4 — Configuración y contenido (2–3 días)

- [ ] Configuración de la HD-WF4 en HD2020 / HDSign: 4 puertos, scan, gamma y refresco
- [ ] Calibración de brillo con sensor de luz ambiente
- [ ] Playlist inicial: logo + promos + reloj/fecha (ver `06_control_contenido.md`)
- [ ] Configuración WiFi y acceso remoto
- [ ] Mantener HD2020 / HDSign como ruta de puesta en marcha. El driver propio se desarrolla en banco sobre una **Colorlight 5A-75B** independiente, sin tocar la HD-WF4 de producción. Ver [`11_arquitectura_colorlight_5a75b.md`](11_arquitectura_colorlight_5a75b.md).

## Fase 5 — Sellado e instalación (1–2 días)

> Con mástil ([`18`](18_monoposte.md)): fundación con plantilla de pernos y reserva
> de conducto → curado según procedimiento de obra → izar el mástil, aplomar con
> las tuercas y grout → izar el conjunto gabinete + brazo (≈ 90 kg) con medios de
> elevación y bulonar la brida → PE, jabalina, acometida y mediciones. Los
> anclajes M10 de abajo son de la alternativa a fachada.

- [ ] Re-torque de tornillería de módulos y fuentes
- [ ] Sellado final de pasacables y fijaciones
- [ ] Instalación de subestructura y gabinete en fachada (6× anclajes M10)
- [ ] Conexión de línea fija 220 V — **electricista matriculado**
- [ ] Verificación de puesta a tierra (< 5 Ω)

## Fase 6 — Puesta en marcha (1 día)

- [ ] Test de estrés **24 h a patrón blanco full** monitoreando:
  - [ ] Temperatura de las 4 fuentes (≤ 60 °C)
  - [ ] Temperatura interior del gabinete (≤ 15 °C sobre ambiente)
  - [ ] Tensión 5 V en módulo más lejano (≥ 4,85 V)
  - [ ] Olor/humo, conectores calientes (termografía si hay disponible)
- [ ] Test de estanqueidad: simulación de lluvia con manguera suave frontal 15 min → inspección interior
- [ ] Fotos finales, checklist firmado, entrega

## Registro de incidencias

Mantener una fila por problema detectado con fecha, descripción y resolución. Este registro alimenta la garantía con proveedores.
