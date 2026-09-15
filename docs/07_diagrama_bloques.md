# 07 — Diagrama de bloques funcional

Este diagrama define la arquitectura de referencia para el cartel de 256×128 px con controladora Huidu HD-WF4 y 16 módulos P5 de 320×160 mm. Las fuentes de 5 V no comparten sus salidas positivas.

```mermaid
flowchart TB
    Grid["Red 220 V CA"] --> Isolator["Seccionador 2P"]
    Isolator --> RCD["Diferencial 2P<br/>30 mA"]
    RCD --> MCB["Breaker 2P<br/>10 A curva C"]
    MCB --> AC["Bornera de distribución<br/>L / N"]
    AC -. "desvío de sobretensión" .-> SPD["SPD tipo 2<br/>275 V"]
    SPD --> PE["Barra PE<br/>tierra de protección"]

    PE --> Chassis["Gabinete y estructura<br/>metálica"]
    PE --> PS1
    PE --> PS2
    PE --> PS3
    PE --> PS4

    AC --> PS1["Fuente 1<br/>5 V / 60 A"]
    AC --> PS2["Fuente 2<br/>5 V / 60 A"]
    AC --> PS3["Fuente 3<br/>5 V / 60 A"]
    AC --> PS4["Fuente 4<br/>5 V / 60 A"]

    PS1 --> F1L["Fusible 20 A<br/>fila 1, extremo izquierdo"]
    PS1 --> F1R["Fusible 20 A<br/>fila 1, extremo derecho"]
    PS2 --> F2L["Fusible 20 A<br/>fila 2, extremo izquierdo"]
    PS2 --> F2R["Fusible 20 A<br/>fila 2, extremo derecho"]
    PS3 --> F3L["Fusible 20 A<br/>fila 3, extremo izquierdo"]
    PS3 --> F3R["Fusible 20 A<br/>fila 3, extremo derecho"]
    PS4 --> F4L["Fusible 20 A<br/>fila 4, extremo izquierdo"]
    PS4 --> F4R["Fusible 20 A<br/>fila 4, extremo derecho"]
    PS4 --> FC["Fusible 2 A<br/>control y ventilación"]

    F1L -->|"+5 V"| Row1["Fila 1<br/>4 módulos P5 outdoor"]
    F1R -->|"+5 V"| Row1
    F2L -->|"+5 V"| Row2["Fila 2<br/>4 módulos P5 outdoor"]
    F2R -->|"+5 V"| Row2
    F3L -->|"+5 V"| Row3["Fila 3<br/>4 módulos P5 outdoor"]
    F3R -->|"+5 V"| Row3
    F4L -->|"+5 V"| Row4["Fila 4<br/>4 módulos P5 outdoor"]
    F4R -->|"+5 V"| Row4

    FC --> Controller["Huidu HD-WF4<br/>256 × 128 px"]
    FC --> Fans["Ventilación 5 V<br/>termostatada"]
    Controller -->|"HUB75 puerto 1"| Row1
    Controller -->|"HUB75 puerto 2"| Row2
    Controller -->|"HUB75 puerto 3"| Row3
    Controller -->|"HUB75 puerto 4"| Row4

    Sensor["Sensor Huidu HD-S107<br/>o compatible"] --> Controller
    PC["PC o teléfono<br/>HD2020 / HDSign"] <-->|"WiFi local o USB"| Controller
    VPN["Router con VPN<br/>opcional"] -. "solo tras validar compatibilidad" .-> Controller

    PS1 -. "0 V" .-> ZeroV["Punto estrella 0 V<br/>referencia común de potencia y datos"]
    PS2 -. "0 V" .-> ZeroV
    PS3 -. "0 V" .-> ZeroV
    PS4 -. "0 V" .-> ZeroV
    ZeroV -. "referencia GND" .-> Controller
```

## Conexiones obligatorias

| Enlace | Implementación |
|---|---|
| Red CA | Línea fija desde tablero, instalada y verificada por electricista matriculado. |
| Protección | El SPD se conecta en paralelo entre L/N y PE, con conductores a tierra lo más cortos posible. |
| Tierra de protección | PE une gabinete, estructura y bornes de tierra de cada fuente. No se usa como retorno de 5 V. |
| Fuentes 1 a 3 | Cada fuente alimenta una sola fila mediante dos ramas 12 AWG, cada una con fusible de 20 A, inyectadas en extremos opuestos. |
| Fuente 4 | Alimenta la fila 4 con dos ramas de 20 A y, mediante un fusible de 2 A independiente, la HD-WF4 y ventilación 5 V. |
| 0 V | Las salidas negativas de las cuatro fuentes se unen en un único punto estrella; la HD-WF4 y los GND de HUB75 toman ahí su referencia. |
| +5 V | No unir positivas de fuentes diferentes. Cada fila recibe potencia exclusivamente de su rama protegida. |
| Datos | Cada salida HUB75 de la HD-WF4 alimenta una única fila de cuatro módulos, encadenados según la dirección `OUT` de cada módulo. |
| Sensor | Usar un sensor compatible con el puerto de la HD-WF4; confirmar modelo y conector con el proveedor de la controladora. |

## Secuencia de puesta en marcha

1. Con el gabinete sin tensión, verificar continuidad de PE y ausencia de continuidad entre PE y los positivos de 5 V.
2. Energizar cada fuente sin carga y ajustar su salida a 5,1 V.
3. Verificar las ocho ramas de inyección de 20 A y la rama de 2 A de control/ventilación.
4. Conectar la HD-WF4, el sensor y una sola fila; importar el archivo de configuración entregado por el proveedor del módulo.
5. Repetir con las otras tres filas y comprobar el mapeo de cada puerto HUB75.
6. Medir 5 V en el módulo más lejano de cada fila a blanco completo; debe mantenerse en 4,85 V o más.
7. Ejecutar prueba de estrés de 24 h antes de cerrar y montar el gabinete en fachada.

## Límites de esta arquitectura

- No hay una fuente de reserva instalada. Para reducir la indisponibilidad, mantener una LRS-350-5 de repuesto fuera del gabinete.
- La HD-WF4 se utiliza para texto, imágenes, reloj y animaciones compatibles con HD2020/HDSign. Validar una animación real en banco antes de producir contenido comercial.
- El anuncio declara HUB75 y scan 1/8. El archivo de configuración, pinout, IC de manejo y compatibilidad con la salida HUB75E de la HD-WF4 deben confirmarse con el vendedor antes de comprar el lote completo.
- Este diagrama corresponde a la ruta de producción con HD-WF4. El driver propio usa **Colorlight 5A-75B** con 8 cadenas de 2 módulos en lugar de 4 cadenas de 4. **El bloque de potencia de este diagrama no cambia** —diferencial, breaker, SPD, las cuatro fuentes y las ocho ramas fusibleadas son idénticos—; solo se reparten distinto los cables de datos y la alimentación de la controladora. Ver [`10_plataforma_driver.md`](10_plataforma_driver.md) y [`11_arquitectura_colorlight_5a75b.md`](11_arquitectura_colorlight_5a75b.md). La vista integrada de esa ruta, de la fuente al display, está en [`16_cadena_completa.md`](16_cadena_completa.md).
