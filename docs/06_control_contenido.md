# 06 — Controlador y sistema de contenido

## Huidu HD-WF4

Controladora gráfica asíncrona para módulos HUB75E. Reproduce programas cargados en su memoria; no requiere una PC conectada durante la operación normal.

## Modos de control del proyecto

| Modo | Hardware | Estado | Uso |
|---|---|---|---|
| Firmware Huidu + HD2020 / HDSign | Huidu HD-WF4 | Ruta inicial y de producción | Validar módulos, configurar scan, contenido, horarios y brillo. |
| Driver propio en FPGA | **Colorlight 5A-75B** | En diseño, track paralelo | HDL propio, control directo de la matriz, interfaz de contenido a medida. |
| ~~Firmware ESP-IDF sobre HD-WF4~~ | Huidu HD-WF4 | **Descartado** | Ver [`10_plataforma_driver.md`](10_plataforma_driver.md). |

Las dos rutas vigentes usan **placas distintas y no se pisan**: la HD-WF4 queda intacta con su firmware de fábrica mientras el driver propio se desarrolla en banco sobre la 5A-75B. Eso elimina el riesgo de quedarse sin controladora de producción durante el desarrollo.

La 5A-75B es una placa receptora: no tiene WiFi, RTC ni almacenamiento de playlist, así que el driver propio debe implementar su propia capa de contenido. Arquitectura en [`11_arquitectura_colorlight_5a75b.md`](11_arquitectura_colorlight_5a75b.md).

| Característica | Valor |
|---|---|
| Capacidad | La documentación de proveedor varía según revisión; este proyecto usa 256×128 px. Validar la capacidad efectiva en banco. |
| Puertos | 4× HUB75; un puerto por fila física de 4 módulos |
| Conectividad | WiFi integrado + USB |
| Software | HD2020 / HDSign |
| Sensor externo | Brillo, temperatura, humedad e IR mediante accesorios compatibles |
| Contenido base | Texto, imágenes, reloj/fecha, regiones y efectos de animación |

> La HD-WF4 es una controladora gráfica, no un reproductor multimedia genérico. No se debe asumir reproducción directa de MP4/AVI: validar el formato de animación admitido en banco antes de producir contenido comercial.

## Configuración HD2020 / HDSign (pasos)

1. **Crear pantalla**: ancho 256 px, alto 128 px y cuatro puertos HUB75.
2. **Mapeo**: puerto 1 = fila 1, puerto 2 = fila 2, puerto 3 = fila 3 y puerto 4 = fila 4; cada fila contiene 4 módulos en cadena.
3. **Configuración del módulo**: importar el archivo entregado por el proveedor. El panel declara scan 1/8; confirmar el IC driver y la compatibilidad HUB75/HUB75E antes de montar la pantalla completa.
4. **Refresco**: fijar ≥ 1920 Hz si la configuración del módulo lo permite.
5. **Brillo**: habilitar ajuste automático con el sensor de luz compatible.
6. **Horario**: programar apagado nocturno o reducción de brillo (cortesía, ahorro y normativa local de contaminación lumínica).

## Diseño de contenido a 256×128 px

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
| 1 | Logo animado | Logo + tagline, animación compatible con HD2020 / HDSign | 6 s |
| 2 | Promo principal | Servicio/producto estrella + precio | 6 s |
| 3 | Promo secundaria | Segundo mensaje | 5 s |
| 4 | Contacto | WhatsApp/web/redes | 5 s |
| 5 | Reloj + fecha | Cortesía, rotativo | 4 s |

### Flujo de trabajo de actualización

1. Diseñar en Canva/Figma/Photoshop a **256×128 px**; no partir de un lienzo 16:9 porque la pantalla es 2:1.
2. Exportar al formato admitido por HD2020 / HDSign; validar primero una animación corta en la pantalla real.
3. Subir por WiFi o USB con HD2020 / HDSign → agregar a la lista de programas → publicar.
4. Verificar visualmente desde la vereda (colores y legibilidad reales)

## Gestión remota (opcional)

- Base: actualización local por WiFi o USB, sin exponer la controladora a Internet.
- Si se requiere gestión remota: agregar un router con VPN y validar el acceso con la HD-WF4 antes de instalarlo en el gabinete.

## Alcance del driver propio

El objetivo es cartelería autónoma a 256 × 128 px: texto, imágenes, playlist, reloj, NTP, horarios, brillo y actualización remota. No es un receptor HDMI ni un decodificador de vídeo.

La primera versión prioriza la salida de panel correcta —mapeo de scan, profundidad de color y refresco estable— antes que cualquier función de contenido. El streaming de frames por red es una mejora posterior, y solo se incorpora una vez que la salida HUB75 esté estable.

La arquitectura, el punto de operación y los criterios de aceptación están en [`11_arquitectura_colorlight_5a75b.md`](11_arquitectura_colorlight_5a75b.md).
