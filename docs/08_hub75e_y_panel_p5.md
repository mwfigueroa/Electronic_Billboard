# 08 — Interfaz HUB75E y especificación del panel P5

## Origen de las señales HUB75E

En operación normal, la **Huidu HD-WF4** genera todas las señales HUB75E. El contenido cargado desde HD2020 / HDSign se guarda en la controladora; su firmware lo convierte continuamente en datos RGB, direcciones de fila y señales de temporización para los módulos.

La placa HD-WF4 usa un **ESP32-S3**, lógica de aislamiento/buffer y cuatro conectores HUB75E. El panel P5 no genera vídeo ni datos: recibe la trama serial, selecciona la fila activa y sus IC drivers regulan la corriente de los LED.

### Señales lógicas

| Señal | Función |
|---|---|
| `R1`, `G1`, `B1` | Datos RGB seriales para la mitad superior del grupo de filas activo. |
| `R2`, `G2`, `B2` | Datos RGB seriales para la mitad inferior del grupo de filas activo. |
| `A`, `B`, `C`, `D`, `E` | Dirección binaria de la fila multiplexada. La `E` es la línea adicional característica de HUB75E. |
| `CLK` | Desplaza los bits RGB hacia los registros de los IC drivers del panel. |
| `LAT` / `STB` | Transfiere el dato desplazado a las salidas de los drivers. |
| `OE` | Habilita o apaga momentáneamente las salidas; se usa durante el desplazamiento y para PWM de brillo. |
| `GND` | Referencia eléctrica de las señales. Debe ser común entre controladora y fuentes de los módulos. |

El cable HUB75E transporta **señales lógicas**, no la potencia de los paneles. La alimentación de 5 V se inyecta por las ramas de potencia previstas en `03_electrico.md`.

### Particularidad de la HD-WF4

En el firmware Huidu de fábrica, los cuatro puertos se administran correctamente como cuatro salidas. Para firmware propio, la placa tiene dos bancos de salida:

- `X1` y `X2` se habilitan mediante una compuerta controlada por GPIO45.
- `X3` y `X4` se habilitan mediante una compuerta controlada por GPIO14.
- Las líneas `A`–`E`, `CLK`, `LAT` y `OE` son compartidas entre los conectores; los pares `X1`/`X3` y `X2`/`X4` comparten grupos RGB.

Por eso no se debe tratar la placa como cuatro salidas HUB75 independientes de un ESP32 genérico. Esta limitación —dos buses serializados en vez de cuatro paralelos— es la que llevó a descartar la HD-WF4 como base del driver propio y adoptar la **Colorlight 5A-75B**, que expone ocho puertos simultáneos. El análisis comparativo con números está en [`10_plataforma_driver.md`](10_plataforma_driver.md).

La HD-WF4 sigue siendo la controladora de producción con su firmware de fábrica, donde los cuatro puertos se administran correctamente.

## Panel seleccionado para validación

El candidato es el [LYERAEEN P5-320x160-8S-1921](https://es.aliexpress.com/item/1005010560338789.html). Los datos siguientes provienen de su anuncio; se deben validar con una muestra antes de comprar el lote.

| Propiedad | Requisito de diseño | Estado |
|---|---|---|
| Modelo / marca | P5-320x160-8S-1921 / LYERAEEN | Declarado por el anuncio |
| Tipo | Panel LED P5 outdoor full-color, SMD RGB 3-en-1 | Declarado |
| Paso de píxel | 5,0 mm | Declarado |
| Tamaño del módulo | 320 × 160 mm | Declarado |
| Resolución por módulo | 64 × 32 px = 2.048 píxeles | Declarado |
| Densidad | 40.000 píxeles/m² | Declarado |
| Configuración | 4 × 4 módulos = 16 módulos | Diseño adoptado |
| Resolución total | 256 × 128 px = 32.768 píxeles | Derivado |
| Tamaño visible | 1.280 × 640 mm | Derivado |
| Interfaz de datos | HUB75 | Declarado; confirmar pinout y adaptación a la salida HUB75E de la HD-WF4 |
| Alimentación | 5 V CC | Requisito de diseño; confirmar tensión permitida con vendedor |
| Brillo | > 4.500 cd/m² (nits) | Declarado; por debajo del objetivo inicial de 5.000 nits |
| Refresco | No declarado | Pedir valor y configuración para HD2020 / HDSign |
| Protección | Uso exterior | Confirmar IP frontal, trasera y temperatura de operación |
| Scan | 1/8 | Declarado |
| IC driver | No declarado | El sufijo `1921` no confirma que el driver sea ICN2038S; pedir modelo de IC |
| Compatibilidad de control | Huidu, Novastar, Colorlight y Linsn | Declarado; pedir archivo de configuración Huidu |
| Tasa de puntos ciegos | 0,0001 | Declarado |

## Potencia del panel

El anuncio declara 300 W/m² promedio y 800 W/m² máximo. Un módulo ocupa 0,320 × 0,160 = 0,0512 m²:

```
P_panel_avg = 300 W/m² × 0,0512 m² = 15,36 W
P_panel_max = 800 W/m² × 0,0512 m² = 40,96 W
I_panel_max = 40,96 W / 5 V = 8,19 A
P_total_max = 16 × 40,96 W = 655,36 W
I_total_max = 655,36 W / 5 V = 131,07 A
```

El valor de 8,19 A es por **módulo completo**, no por píxel. La corriente instantánea de cada LED depende del scan y del PWM; no se dimensiona la fuente multiplicando una corriente fija por píxel.

Cada fila de cuatro módulos puede requerir hasta 163,84 W o 32,77 A. Por eso el diseño usa una fuente LRS-350-5 por fila y dos inyecciones 12 AWG, cada una protegida con fusible de 20 A.

## Compatibilidad física y eléctrica

1. No comprar cables flat por cantidad de pines anunciada sin verificar los conectores físicos de la HD-WF4 y del módulo. El anuncio declara HUB75, mientras que la HD-WF4 ofrece HUB75E; confirmar pinout, polaridad y si hace falta adaptador.
2. Confirmar la orientación `IN` / `OUT` y el sentido de encadenamiento de cada módulo antes de montar una fila completa.
3. Confirmar que la configuración del fabricante funciona con la HD-WF4, no solo con otra marca de controladora.
4. No alimentar módulos desde el cable de datos ni conectar dos salidas positivas de fuente a una misma fila.
5. No conectar directamente un microcontrolador de 3,3 V a un panel outdoor sin verificar niveles lógicos, buffers y calidad de señal. La HD-WF4 incorpora su propia etapa de interfaz.

## Información que debe pedirse al vendedor

> **Prioridad 1: el modelo de IC driver.** Define qué driver hay que escribir, no solo cómo configurarlo. Si el módulo usa un IC de desplazamiento simple (clase ICN2038S), vale el modelo de bitplanes BCM de [`10_plataforma_driver.md`](10_plataforma_driver.md). Si usa un IC con **S-PWM interno** (MBI5153, FM6353 y similares), el protocolo de carga es otro y el presupuesto de refresco deja de aplicar. Junto con el archivo de configuración, es lo que más condiciona el cronograma del driver.

- Hoja de datos del módulo y fotografía del frente, dorso y conectores.
- **Modelo exacto de IC driver**, refresco y brillo medido; el anuncio solo declara scan 1/8.
- Tensión permitida, corriente típica/máxima a 5 V e inyección de potencia recomendada.
- Pinout, cantidad de pines y sentido `IN` / `OUT` del conector HUB75.
- Archivo de configuración para Huidu HD2020 / HDSign y confirmación de que fue probado en una HD-WF4.
- IP frontal/trasera, temperatura de operación y condiciones de garantía.
- 16 módulos del mismo lote más dos repuestos compatibles.
