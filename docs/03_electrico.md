# 03 — Arquitectura eléctrica y cableado

## Diagrama general

```
  Red 220 V CA (línea fija desde tablero)
        │
        ▼
  [Diferencial 2P 25A/30mA]
        │
        ▼
  [Breaker 2P 10A curva C]
        │
        ▼
  [SPD tipo 2, 275 V] ──── a tierra
        │
        ├──► [LRS-350-5 #1] 5V/60A ──► filas 1-2 (14 módulos) + controlador
        ├──► [LRS-350-5 #2] 5V/60A ──► filas 3-4 (14 módulos)
        └──► [LRS-350-5 #3] 5V/60A ──► respaldo/inyección de refuerzo
```

## Distribución 5 V

**Principio**: cada módulo P5 consume hasta ~0,6 A por píxel blanco... valor práctico: hasta ~3,4 A pico por módulo (17 W). Reglas:

1. **Cable 12 AWG** mínimo para troncales de 5 V. Caída máxima aceptada: 0,2 V en el módulo más lejano.
2. **Inyección en ambos extremos de cada fila** (7 módulos = 1,12 m por fila): la cadena de conectores del módulo no está pensada para transportar 20 A de punta a punta.
3. Balance de fuentes (config recomendada):
   - Fuente 1: filas 1 y 2 (14 módulos, ~24 A promedio / 48 A pico)
   - Fuente 2: filas 3 y 4 (14 módulos, ídem)
   - Fuente 3: refuerzo de extremos de fila + controlador A35 (deja margen del ~30 %)
4. **Fusible o polyfuse por fila** (5 A) opcional pero recomendado: un corto en un módulo no debe tirar toda la pantalla.

## Topología de datos (HUB75E)

```
  Colorlight A35
    ├── Puerto HUB75 #1 ──► fila 1 (7 módulos en cadena) ──┐
    │                                    (continúa) ────────┴──► fila 2 (7 módulos)
    └── Puerto HUB75 #2 ──► fila 3 (7 módulos) ──┐
                                     (continúa) ──┴──► fila 4 (7 módulos)
```

- 2 cadenas de 14 módulos (7+7 en serie por puerto) → refresco cómodo, flat cables cortos.
- Flat cables de 30–40 cm con clip: evitar los de 20 cm tensos y los de 50+ cm (integridad de señal).
- El **GND de datos y de potencia deben ser comunes** (lo son por el conector del módulo). Verificar continuidad GND entre fuente y controlador.
- Configurar el layout en LEDVISION: 2 receptores virtuales, scan 1/8 (típico P5 outdoor), mapeo fila por fila. Confirmar el scan real del módulo con el vendedor (varía: 1/8, 1/16).

## Mediciones de puesta en marcha

| Medición | Punto | Valor esperado |
|---|---|---|
| Tensión CA | entrada breaker | 220–240 V |
| Tensión 5 V sin carga | bornes de cada LRS | 5,0–5,2 V (ajustar a 5,1 V) |
| Tensión 5 V a full blanco | módulo más lejano de cada fuente | ≥ 4,85 V |
| Corriente por fuente | pinza amperométrica DC | ≤ 45 A (pico) |
| Temperatura de fuentes | 1 h a full blanco | ≤ 60 °C (LRS-350 límite 70 °C) |

## Seguridad eléctrica (obligatorio)

- [ ] Línea fija 220 V con diferencial 30 mA **instalada por electricista matriculado**
- [ ] Puesta a tierra del gabinete y estructura (continuidad < 5 Ω a barra de tierra)
- [ ] SPD tipo 2 (cartel exterior = exposición a rayos/sobretensiones de red)
- [ ] Prensacables IP68 en todas las pasadas de gabinete
- [ ] Sellado de bornes de fuente con termocontraíl (5 V/60 A = riesgo de arco si afloja)
- [ ] Esquema de cableado etiquetado dentro del gabinete (foto + plano pegado en puerta)

## Cálculo del breaker

- Pico total: 480 W (pantalla) + 15 W (controlador) ≈ 495 W
- Corriente CA a 220 V con eficiencia 0,82 de las fuentes: 495/0,82/220 ≈ 2,7 A
- **Breaker 2P 10 A curva C**: margen ×3,7 para inrush de arranque de fuentes conmutadas
