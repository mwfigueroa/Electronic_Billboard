# 06 — Controlador y sistema de contenido

## Colorlight A35

Controlador asíncrono (reproduce contenido desde memoria propia, no necesita PC conectado).

| Característica | Valor |
|---|---|
| Capacidad | Hasta 650.000 píxeles (este proyecto usa 28.672 → 4 % de la capacidad) |
| Puertos | 2× HUB75E |
| Alimentación | 5 V / 2 A (desde bus del gabinete con regulación propia) |
| Conectividad | WiFi integrado + Ethernet |
| Software | LEDVISION (PC) / VNNOX o app móvil (gestión remota opcional) |
| Formatos soportados | MP4, AVI, imágenes, texto, reloj, temperatura, animaciones |

## Configuración LEDVISION (pasos)

1. **Crear pantalla**: ancho 224 px, alto 128 px, 2 receptores (uno por puerto HUB75)
2. **Mapeo**: receptor 1 = filas 1–2 (7+7 módulos cadena), receptor 2 = filas 3–4
3. **Scan del módulo**: confirmar con vendedor (típicamente 1/8 en P5 outdoor 32×32) — si la imagen sale partida o desplazada, es el scan mal configurado
4. **Refresco**: fijar ≥ 1920 Hz
5. **Brillo**: habilitar ajuste automático con sensor de luz ambiente
6. **Horario**: programar apagado nocturno o reducción de brillo (cortesía + ahorro + normativa local de contaminación lumínica)

## Diseño de contenido a 224×128 px

### Reglas prácticas

- **Distancia de lectura**: a 5 m, cada píxel ≈ 5 mm → texto legible mínimo ~15 cm de alto (30 px). Recomendado: texto principal ≥ 40 px de alto
- **Contraste**: texto claro sobre fondo oscuro rinde mejor de día (menos consumo además)
- **Tiempo por slide**: 4–7 segundos (lectura cómoda a distancia)
- **Transiciones**: fade rápido; evitar desplazamientos muy rápidos (parpadeo perceptible de cerca)
- **Paleta**: evitar azules puros oscuros al atardecer con sol rasante — favorecer blanco/ámbar para texto de día
- **Logo**: versión simplificada, formas gruesas; una marca compleja pierde detalle a 224 px de ancho

### Plantilla de playlist inicial (empresa de tecnología)

| # | Slide | Contenido | Duración |
|---|---|---|---|
| 1 | Logo animado | Logo + tagline, animación de entrada | 6 s |
| 2 | Promo principal | Servicio/producto estrella + precio | 6 s |
| 3 | Promo secundaria | Segundo mensaje | 5 s |
| 4 | Contacto | WhatsApp/web/redes | 5 s |
| 5 | Reloj + fecha | Cortesía, rotativo | 4 s |

### Flujo de trabajo de actualización

1. Diseñar en Canva/Figma/Photoshop a **224×128 px** (o 16:9 y escalar en exportación)
2. Exportar PNG o MP4 (H.264, ≤ 1080p irrelevante, bitrate bajo)
3. Subir por WiFi con LEDVISION/app → agregar a playlist → publicar
4. Verificar visualmente desde la vereda (colores y legibilidad reales)

## Gestión remota (opcional)

- Si la ubicación queda fuera del alcance del WiFi de la oficina: agregar mini-router 4G al gabinete (~USD 30 + SIM) y gestionar por VNNOX Cloud
- Alternativa gratuita: Tailscale en un router con soporte (acceso remoto seguro sin exponer nada a internet)
