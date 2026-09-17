# 16 — Cadena completa: de la fuente al display

Vista de integración de la **ruta del driver propio** (Colorlight 5A-75B), desde el contenido hasta los módulos P5. No repite detalle: la potencia y el gabinete están en [`07`](07_diagrama_bloques.md), el driver y el plan de bring-up en [`11`](11_arquitectura_colorlight_5a75b.md), el software de contenido en [`14`](14_software_contenido.md). Acá está el mapa único que los une, con los nombres de señal, y la correspondencia con el simulador que ya validó los números.

Es la referencia de la fase "reproducir en electrónica lo que el simulador muestra".

## Vista de sistema

Mapa completo: contenido, contrato, control (las dos rutas), panel y potencia,
con el espejo virtual del banco de desarrollo. El detalle de cada bloque está
en las secciones siguientes y en [`07`](07_diagrama_bloques.md),
[`11`](11_arquitectura_colorlight_5a75b.md) y [`14`](14_software_contenido.md).

```mermaid
flowchart TB
    subgraph Contenido["Contenido · PC"]
        Editor["Editor de playlist<br/>panel_sim/editor.py · preview del pipeline"]
        App["App de contenido — content/app.py<br/>playlist JSON + horarios → composición 256×128<br/>/status · recarga en caliente"]
        HD2020["PC con HD2020 / HDSign<br/>contenido cargado en la controladora"]
    end

    Wire["contrato de wire v1 — RGB888 256×128 · 98.304 B por cuadro<br/>MJPEG/HTTP · UDP rawvideo · x11grab · socket Unix · ≤ 30 fps"]

    subgraph Banco["Banco · espejo virtual (sin hardware)"]
        Sim["panel_sim — gamma 2.2 · cuantización 5 bits<br/>bitplanes · máscara LED · distancia equivalente"]
        Vec["vectores dorados<br/>frame_rgb888.mem · gamma_lut_2p2_5b.mem · 15 planos"]
    end

    subgraph Control["Control — dos rutas (mismo panel, misma potencia)"]
        Huidu["Puesta en marcha: Huidu HD-WF4<br/>firmware de fábrica · 4× HUB75E"]
        subgraph FPGA["Driver propio: Colorlight 5A-75B — ECP5 LFE5U-25F"]
            SoC["LiteEth + LiteX SoC · playlist, horarios, NTP<br/>pendiente — Paso 5"]
            DRAM["LiteDRAM → SDRAM 8 MB · framebuffer RGB888<br/>pendiente — Paso 5"]
            Conv["rgb_to_bitplane · LUT gamma 2.2 → 5 bits"]
            Store["bitplane_store · BRAM 60 KB · 30/56 DP16KD"]
            Map["scan_mapper · mapeo del scan 1/8<br/>pendiente — Paso 2, necesita el panel"]
            Seq["bcm_sequencer + 8× hub75_serializer<br/>2.080 clocks/bitplane → 193,9 Hz @ 12,5 MHz"]
            Buf["12× 74HC245T · 3,3 V → 5 V"]
        end
    end

    Panel["16 módulos P5 320×160 (64×32 px, scan 1/8)<br/>4 filas × 4 columnas → 256×128 px · 1.280×640 mm<br/>IC driver sin confirmar: define el protocolo"]

    subgraph Potencia["Potencia (idéntica en ambas rutas)"]
        AC["220 V CA → seccionador → diferencial 30 mA → breaker 2P 10 A<br/>SPD tipo 2 → PE (gabinete y estructura)"]
        PSU["4 × LRS-350-5 · 5 V / 60 A (una por fila)<br/>2 ramas 12 AWG con fusible 20 A · 0 V en punto estrella"]
    end

    Editor -->|"guarda · la app ve el mtime"| App
    App --> Wire
    HD2020 -->|"WiFi / USB — no cruza el contrato"| Huidu
    Wire --> Sim
    Wire -.->|"mismo contrato, objetivo (Paso 5)"| SoC
    Sim -->|"genera"| Vec
    Vec -->|"valida el HDL · 1.920 comparaciones"| Conv
    SoC --> DRAM
    DRAM -->|"solo al cambiar de slide · ~12 KB/s"| Conv
    Conv --> Store
    Store -->|"lectura del refresco · desde BRAM"| Map
    Map --> Seq
    Seq -->|"los 8 puertos en lockstep"| Buf
    Huidu -->|"HUB75E · 4 cadenas de 4 módulos"| Panel
    Buf -->|"HUB75E · 8 cadenas de 2 módulos<br/>R1…B2 por puerto · A/B/C · CLK · LAT · OE (activo bajo)"| Panel
    AC --> PSU
    PSU -->|"+5 V por fila · hasta 655 W"| Panel
```

Los tres bloques marcados como pendientes son los que todavía no existen:
`LiteEth`/`LiteX` y `LiteDRAM` entran en el Paso 5, y el `scan_mapper` necesita
el panel físico (Paso 2). El enlace `App → SoC` va punteado por lo mismo: hoy
la app alimenta el panel virtual, y el HDL se valida contra los vectores que
ese mismo pipeline genera. La alimentación de la controladora —el ramal de
2 A— está en la sección de potencia de abajo y en [`07`](07_diagrama_bloques.md).

Estado de cada tramo:

| Elemento | Estado | Depende de |
|---|---|---|
| App de contenido (`content/`) | hecha: playlist, horarios, transporte y editor | — |
| Panel virtual (`panel_sim/`) | hecho y verificado | — |
| Bloques HDL del driver (5) | hechos y validados en simulación | — |
| `scan_mapper` | pendiente | el panel físico (Paso 2) |
| LiteX / LiteEth / LiteDRAM | pendiente | Paso 5 |
| Panel, fuentes y estructura | pendiente | compras de Fase 1 |

## Datos: fuente → panel

```mermaid
flowchart TB
    subgraph Content["Fuente / contenido"]
        PC["PC de autoría<br/>video · playlist · composición<br/>frames RGB888 256×128"]
    end

    subgraph Net["Enlace"]
        AP["Router / AP WiFi<br/>en el gabinete"]
    end

    subgraph Board["Colorlight 5A-75B — ECP5-25"]
        PHY["PHY RTL8211FD ×2"]
        MAC["LiteEth MAC"]
        SoC["LiteX SoC · VexRiscv<br/>playlist · horarios · NTP"]
        Flash["SPI flash 25Q32JVSIQ<br/>4 MB"]
        DRAM["LiteDRAM → SDRAM M12L64322A<br/>8 MB · framebuffer RGB888"]
        Conv["rgb_to_bitplane<br/>gamma 2.2 + cuantización"]
        Store["bitplane_store — BRAM 60 KB<br/>5 bits por color"]
        Seq["bcm_sequencer + scan_mapper<br/>lockstep · 2048 clocks de datos por bitplane"]
        Ser["8 × hub75_serializer"]
        Buf["12 × 74HC245T<br/>3,3 V → 5 V"]
    end

    Panel["16 módulos P5 320×160<br/>8 cadenas × 2 · 64×32 px · scan 1/8"]

    PC -->|"contrato de wire v1: RGB888 256×128"| AP
    AP -->|"1000BASE-T"| PHY
    PHY -->|"RGMII"| MAC
    MAC -->|"Wishbone"| SoC
    SoC -->|"Wishbone"| DRAM
    Flash -. "bitstream + contenido" .-> SoC
    DRAM -->|"frame RGB888 (solo al cambiar contenido)"| Conv
    Conv -->|"bitplanes (bit · canal · y · x)"| Store
    Store -->|"dato serie"| Seq
    Seq -->|"A/B/C (D/E sin uso) · CLK · LAT · OE"| Ser
    Ser -->|"R1 G1 B1 R2 G2 B2 por puerto (×8)"| Buf
    Buf -->|"HUB75E · 5 V"| Panel
```

Cada fila física de 4 módulos se reparte en dos cadenas de 2: los 8 puertos se usan todos y `A`–`E`, `CLK`, `LAT` y `OE` van compartidas (lockstep). Solo `A`/`B`/`C` llevan información —el scan 1/8 necesita 2³ = 8 pasos—; `D` y `E` quedan disponibles de la placa pero sin uso. Detalle en [`11`](11_arquitectura_colorlight_5a75b.md).

## Potencia

Idéntica a la ruta de producción ([`07`](07_diagrama_bloques.md)): solo cambia el reparto de los cables de datos y la alimentación de la controladora.

```mermaid
flowchart LR
    Grid["220 V CA L/N"] --> RCD["Diferencial 2P<br/>30 mA"] --> MCB["Breaker 2P<br/>10 A curva C"] --> AC["Bornera L/N"]
    AC -. "desvío de sobretensión" .-> SPD["SPD tipo 2<br/>275 V"]
    SPD --> PE["Barra PE<br/>gabinete y estructura"]
    AC --> PS["4 × LRS-350-5<br/>5 V / 60 A · una por fila"]
    PS --> F["2 ramas 12 AWG<br/>fusible 20 A c/u"]
    F --> Rows["4 módulos de la fila"]
    PS -. "+5 V · fusible 2 A" .-> Board["5A-75B"]
    PS -. "0 V" .-> Star["Punto estrella<br/>referencia común de datos y potencia"]
```

`PE` no se usa como retorno de 5 V y las salidas positivas de las fuentes no se unen entre filas.

## Señales

| Señal | Enlace | Tipo / nota |
|---|---|---|
| `1000BASE-T` | PC/AP ↔ RTL8211FD | Ethernet 1 Gb, par trenzado Cat5e |
| `RGMII` | RTL8211FD ↔ FPGA | TXD/RXD[3:0] + TX_CTL/RX_CTL + clocks |
| `Wishbone` | interno LiteX | MAC · SoC · LiteDRAM (el bus por defecto de litex-boards; AXI existe como adaptador) |
| `frame RGB888` | SDRAM → conversor | 256×128; se mueve solo al cambiar contenido (~12 KB/s promedio) |
| `bitplanes[bit][canal][y][x]` | BRAM → secuenciador | 5 bits/color, 60 KB, **pre-mapeo de scan** |
| `R1 G1 B1 R2 G2 B2` | FPGA → panel, por puerto | 6 por puerto; ×8 = 48 |
| `A/B/C` · `D/E` | compartidas por los 8 puertos | `A`/`B`/`C`: paso de dirección (scan 1/8) · `D`/`E`: sin uso, a nivel bajo |
| `CLK` · `LAT/STB` · `OE` | compartidas por los 8 puertos | lockstep obligatorio · `OE` activo bajo ([`08`](08_hub75e_y_panel_p5.md)) |
| `+5V0` | fuentes → filas | una fuente por fila, 2 inyecciones 12 AWG |
| `0V` | retorno común | punto estrella; referencia GND de datos |
| `PE` | gabinete y estructura | no se usa como retorno de 5 V |
| `F1L…F4R` · `FC` | protección | fusibles 20 A por rama · 2 A control |

## Correspondencia con el simulador

Lo ya verificado en [`../simulator/`](../simulator/README.md) es lo que hay que reproducir en hardware:

| Simulador | Bloque de hardware | Número verificado |
|---|---|---|
| `quantize` | `rgb_to_bitplane` (FPGA, contrato v1) | `duty = (v/255)^γ`, γ 2.2 |
| `bitplanes.py` (layout `[bit][canal][y][x]`) | `bitplane_store` (BRAM) | 5 bits/color · 60 KB = 48 % de BRAM |
| `timing.refresh_hz` | `bcm_sequencer` | 2080 clocks/bitplane (2048 de datos + blanking) → 193,9 Hz @ 12,5 MHz, medido |
| máscara LED (gap 0.65, circular) | máscara física del módulo P5 | LED ≈ ⅓ del paso · pitch 5 mm |
| `viewing.py` | instalación | 5 m ↔ 416×208 px (monitor 32" 1080p a 60 cm) |

## Condicionantes abiertos

- ~~**Contrato de wire**: ¿la PC manda RGB888 o bitplanes ya serializados?~~ — resuelto en v1: la PC manda **RGB888 de 256×128** y la conversión (gamma, cuantización y armado de bitplanes) vive en el FPGA. Mandar bitplanes queda como posible v2. [`14`](14_software_contenido.md).
- **Familia del IC driver del módulo**: si es S-PWM interno (MBI5153/FM6353), el modelo BCM no aplica y el protocolo es otro. [`08`](08_hub75e_y_panel_p5.md).
- **Mapeo de scan 1/8**: la incógnita principal del driver; se resuelve en el Paso 2 del bring-up. [`11`](11_arquitectura_colorlight_5a75b.md).
- **Revisión de placa**: comprar 8.0 u 8.2; otra revisión implica otro pinout y otro archivo de plataforma LiteX.

## Fuentes

Las fuentes externas de esta cadena (chubby75, LiteX, YosysHQ) están en [`11_arquitectura_colorlight_5a75b.md`](11_arquitectura_colorlight_5a75b.md); no se duplican acá.
