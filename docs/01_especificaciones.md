# 01 — Especificaciones técnicas

## Pantalla

| Parámetro | Valor | Notas |
|---|---|---|
| Tipo | Módulos LED SMD outdoor, protocolo HUB75E | Epoxy encapsulado, máscara IP65 |
| Paso de píxel | 5 mm (P5) | Distancia mín. de visión ~5 m |
| Tamaño módulo | 160 × 160 mm, 32 × 32 px | |
| Configuración | 7 columnas × 4 filas = 28 módulos | |
| Tamaño total | 1120 × 640 mm | Diagonal ≈ 1290 mm ≈ 50,8" |
| Resolución total | 224 × 128 px | 28.672 píxeles |
| Relación de aspecto | 1,75:1 (≈ 16:9,1) | Compatible con diseño 16:9 con recorte |
| Brillo | ≥ 5000 nits | Medición típica de fábrica 5500–6000 cd/m² |
| Color | Full color RGB, SMD 3-in-1 | 1/8 scan típico en P5 outdoor |
| Refresco | ≥ 1920 Hz configurado en controlador | Evita flicker en cámara/video |
| Protección frontal | IP65 | Módulos con epoxy + máscara |
| Protección gabinete | IP54 (trasero ventilado con filtro) | |

## Criterios de diseño

- **Contenido objetivo**: logo de la empresa, mensajes promocionales, animaciones simples, reloj/fecha. Resolución 224×128 es adecuada para texto de ≥ 3 módulos de alto (≥ 48 px de alto para texto cómodo a distancia).
- **Uso exterior**: sol directo (brillo ≥ 5000 nits), lluvia frontal (IP65), rango térmico −20 °C a +60 °C.
- **Actualización remota**: WiFi local con app/web del controlador (LEDVISION / VNNOX según modelo).
- **Mantenimiento**: acceso trasero (fachada con espacio de servicio) — puerta de gabinete abisagrada.

## Consumo estimado

| Estado | Por módulo | Total (28) | Notas |
|---|---|---|---|
| Negro / idle | ~3 W | ~85 W | |
| Promedio (contenido mixto) | ~12 W | ~340 W | Base para dimensionar fuentes |
| Pico (blanco full) | ~17 W | ~480 W | Base para breaker y cableado CA |

## Cálculo de dimensiones (referencia)

- Diagonal: √(1120² + 640²) = √1.664.000 ≈ 1290 mm ≈ 50,8"
- Resolución: 7×32 = 224 px (ancho), 4×32 = 128 px (alto)
- Área expuesta al viento: 1,12 × 0,64 = 0,72 m² (ver `04_estructura.md`)
