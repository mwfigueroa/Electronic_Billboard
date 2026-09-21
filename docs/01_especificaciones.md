# 01 — Especificaciones técnicas

## Pantalla

| Parámetro | Valor | Notas |
|---|---|---|
| Tipo | LYERAEEN P5-320x160-8S-1921, LED SMD outdoor full-color, HUB75 | Confirmar conector/pinout con la HD-WF4 |
| Paso de píxel | 5 mm (P5) | Distancia mín. de visión ~5 m |
| Tamaño módulo | 320 × 160 mm, 64 × 32 px | 0,0512 m² por módulo |
| Configuración | 4 columnas × 4 filas = 16 módulos | |
| Tamaño total | 1280 × 640 mm | Diagonal ≈ 1431 mm ≈ 56,3" |
| Resolución total | 256 × 128 px | 32.768 píxeles |
| Relación de aspecto | 2:1 | Diseñar contenido específicamente a 256×128 px |
| Brillo | > 4500 nits | Inferior al objetivo inicial de 5000 nits; validar en sol directo |
| Color | Full color RGB, SMD 3-in-1 | Scan 1/8 declarado por el vendedor |
| Refresco | A confirmar; objetivo ≥ 1920 Hz | Pedir valor y configuración de panel al vendedor |
| Protección frontal | Uso exterior declarado | Confirmar clasificación IP frontal del módulo; no asumir IP65 sin ficha |
| Protección gabinete | Objetivo IP54 (ventilado con filtros y capotas); grado a ensayar, no declarado desde el CAD — ver [`17`](17_montaje_y_proteccion.md) | |

## Criterios de diseño

- **Contenido objetivo**: logo de la empresa, mensajes promocionales, animaciones simples y reloj/fecha. Resolución 256×128 es adecuada para texto de ≥ 48 px de alto a distancia.
- **Uso exterior**: lluvia frontal y exposición solar. Confirmar IP y rango térmico; el módulo declara >4500 nits, por lo que se debe probar legibilidad a pleno sol antes de comprar el lote completo si 5000 nits es un requisito estricto.
- **Actualización de contenido**: WiFi local o USB mediante HD2020 / HDSign para la Huidu HD-WF4. El acceso remoto se definirá tras validar la red de instalación.
- **Mantenimiento**: acceso trasero (fachada con espacio de servicio) — puerta de gabinete abisagrada.

## Consumo estimado

| Estado | Por módulo | Total (16) | Notas |
|---|---|---|---|
| Promedio declarado | 15,36 W | 245,76 W | 300 W/m²; base de operación típica |
| Pico declarado | 40,96 W | 655,36 W | 800 W/m²; base para fuentes, fusibles y térmica |

## Cálculo de dimensiones (referencia)

- Diagonal: √(1280² + 640²) = √2.048.000 ≈ 1431 mm ≈ 56,3"
- Resolución: 4×64 = 256 px (ancho), 4×32 = 128 px (alto)
- Área expuesta al viento: 1,28 × 0,64 = 0,8192 m² (ver `04_estructura.md`)
