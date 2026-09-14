# 03 — Arquitectura eléctrica y cableado

Ver el diagrama funcional completo en [`07_diagrama_bloques.md`](07_diagrama_bloques.md).

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
  [Bornera de distribución L/N] ──► [SPD tipo 2, 275 V] ──► tierra
        │
        ├──► [LRS-350-5 #1] 5V/60A ──► fila 1 (4 módulos)
        ├──► [LRS-350-5 #2] 5V/60A ──► fila 2 (4 módulos)
        ├──► [LRS-350-5 #3] 5V/60A ──► fila 3 (4 módulos)
        └──► [LRS-350-5 #4] 5V/60A ──► fila 4 (4 módulos) + HD-WF4
```

## Distribución 5 V

**Principio**: el anuncio declara 800 W/m² máximo. Para un módulo de 0,0512 m², el diseño debe soportar 40,96 W o 8,19 A a 5 V por módulo. Confirmar que el módulo admite 5 V antes de comprar. Reglas:

1. **Cable 12 AWG** mínimo para cada rama de inyección de 5 V. Caída máxima aceptada: 0,2 V en el módulo más lejano.
2. **Dos inyecciones independientes por fila**, una en cada extremo. Cada rama se protege con fusible de 20 A y transporta aproximadamente la mitad de los 32,77 A máximos de una fila.
3. Balance de fuentes (config recomendada):
    - Fuente 1: fila 1 (4 módulos, hasta 32,77 A pico).
    - Fuente 2: fila 2 (ídem).
    - Fuente 3: fila 3 (ídem).
    - Fuente 4: fila 4 (ídem) y HD-WF4/ventilación mediante un fusible independiente de 2 A.
4. **No unir salidas positivas de fuentes distintas**. Las cuatro salidas negativas se unen en un punto estrella de 0 V para compartir la referencia de datos.

## Topología de datos (HUB75 / HUB75E)

```
   Huidu HD-WF4
     ├── Puerto HUB75 #1 ──► fila 1 (4 módulos en cadena)
     ├── Puerto HUB75 #2 ──► fila 2 (4 módulos en cadena)
     ├── Puerto HUB75 #3 ──► fila 3 (4 módulos en cadena)
     └── Puerto HUB75 #4 ──► fila 4 (4 módulos en cadena)
```

- 4 cadenas de 4 módulos (una por puerto) → trazado simple, menor longitud de cadena y diagnóstico por fila.
- Flat cables de 30–40 cm con clip: evitar los de 20 cm tensos y los de 50+ cm (integridad de señal).
- El **GND de datos y de potencia deben ser comunes** (lo son por el conector del módulo). Verificar continuidad GND entre fuente y controlador.
- Configurar el layout en HD2020 / HDSign: 256×128 px, cuatro puertos HUB75 y una fila física por puerto. El módulo declara scan 1/8; importar el archivo de configuración suministrado por el vendedor antes de energizar todas las filas.
### Topología alternativa — Colorlight 5A-75B

El driver propio usa otra placa y **otro reparto de cadenas**. Ver [`11_arquitectura_colorlight_5a75b.md`](11_arquitectura_colorlight_5a75b.md).

```
   Colorlight 5A-75B
     ├── J1 ──► fila 1, módulos 1–2        ├── J5 ──► fila 3, módulos 1–2
     ├── J2 ──► fila 1, módulos 3–4        ├── J6 ──► fila 3, módulos 3–4
     ├── J3 ──► fila 2, módulos 1–2        ├── J7 ──► fila 4, módulos 1–2
     └── J4 ──► fila 2, módulos 3–4        └── J8 ──► fila 4, módulos 3–4
```

- 8 cadenas de 2 módulos. Los ocho puertos transmiten **simultáneamente**, no alternados: es lo que baja el trabajo por bitplane de 8.192 a 2.048 clocks.
- **El cableado de potencia 5 V no cambia**: sigue siendo una fuente LRS-350-5 por fila con dos inyecciones de 12 AWG. Solo cambia el reparto de los cables de datos.
- La cantidad total de cables flat tampoco cambia: 16 en ambas topologías.
- Cadenas más cortas mejoran la integridad de señal y permiten bajar el clock de píxel manteniendo el refresco.

## Mediciones de puesta en marcha

| Medición | Punto | Valor esperado |
|---|---|---|
| Tensión CA | entrada breaker | 220–240 V |
| Tensión 5 V sin carga | bornes de cada LRS | 5,0–5,2 V (ajustar a 5,1 V) |
| Tensión 5 V a full blanco | módulo más lejano de cada fuente | ≥ 4,85 V |
| Corriente por fuente | pinza amperométrica DC | ≤ 35 A (pico por fila) |
| Temperatura de fuentes | 1 h a full blanco | ≤ 60 °C (LRS-350 límite 70 °C) |

## Seguridad eléctrica (obligatorio)

- [ ] Línea fija 220 V con diferencial 30 mA **instalada por electricista matriculado**
- [ ] Puesta a tierra del gabinete y estructura (continuidad < 5 Ω a barra de tierra)
- [ ] SPD tipo 2 (cartel exterior = exposición a rayos/sobretensiones de red)
- [ ] Prensacables IP68 en todas las pasadas de gabinete
- [ ] Sellado de bornes de fuente con termocontraíl (5 V/60 A = riesgo de arco si afloja)
- [ ] Esquema de cableado etiquetado dentro del gabinete (foto + plano pegado en puerta)

## Cálculo del breaker

- Pico total: 655 W (pantalla) + 10 W (controladora/ventilación) ≈ 665 W
- Corriente CA a 220 V con eficiencia 0,82 de las fuentes: 665/0,82/220 ≈ 3,7 A
- **Breaker 2P 10 A curva C**: margen suficiente para operación continua e inrush de cuatro fuentes conmutadas
