# 16 — Cadena completa: de la fuente al display

Vista de integración de la **ruta del driver propio** (Colorlight 5A-75B), desde el contenido hasta los módulos P5. No repite detalle: la potencia y el gabinete están en [`07`](07_diagrama_bloques.md), el driver y el plan de bring-up en [`11`](11_arquitectura_colorlight_5a75b.md), el software de contenido en [`14`](14_software_contenido.md). Acá está el mapa único que los une, con los nombres de señal, y la correspondencia con el simulador que ya validó los números.

Es la referencia de la fase "reproducir en electrónica lo que el simulador muestra".

## Datos: fuente → panel

```mermaid
flowchart TB
    subgraph Content["Fuente / contenido"]
        PC["PC de autoría<br/>video · playlist · composición<br/>gamma 2.2 + cuantización a 5 bits"]
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
        Conv["rgb_to_bitplane<br/>gamma 2.2"]
        Store["bitplane_store — BRAM 60 KB<br/>5 bits por color"]
        Seq["bcm_sequencer + scan_mapper<br/>lockstep · 2048 clocks por bitplane"]
        Ser["8 × hub75_serializer"]
        Buf["12 × 74HC245T<br/>3,3 V → 5 V"]
    end

    Panel["16 módulos P5 320×160<br/>8 cadenas × 2 · 64×32 px · scan 1/8"]

    PC -->|"contrato de wire: RGB888 o bitplanes (abierto)"| AP
    AP -->|"1000BASE-T"| PHY
    PHY -->|"RGMII"| MAC
    MAC -->|"AXI"| SoC
    SoC -->|"AXI"| DRAM
    Flash -. "bitstream + contenido" .-> SoC
    DRAM -->|"frame RGB888 (solo al cambiar contenido)"| Conv
    Conv -->|"bitplanes (bit · canal · y · x)"| Store
    Store -->|"dato serie"| Seq
    Seq -->|"A–E · CLK · LAT · OE"| Ser
    Ser -->|"R1 G1 B1 R2 G2 B2 por puerto (×8)"| Buf
    Buf -->|"HUB75E · 5 V"| Panel
```

Cada fila física de 4 módulos se reparte en dos cadenas de 2: los 8 puertos se usan todos y `A`–`E`, `CLK`, `LAT` y `OE` van compartidas (lockstep). Detalle en [`11`](11_arquitectura_colorlight_5a75b.md).

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
| `AXI` | interno LiteX | MAC · SoC · LiteDRAM |
| `frame RGB888` | SDRAM → conversor | 256×128; se mueve solo al cambiar contenido (~12 KB/s promedio) |
| `bitplanes[bit][canal][y][x]` | BRAM → secuenciador | 5 bits/color, 60 KB, **pre-mapeo de scan** |
| `R1 G1 B1 R2 G2 B2` | FPGA → panel, por puerto | 6 por puerto; ×8 = 48 |
| `A B C D E` | compartidas por los 8 puertos | dirección de fila, scan 1/8 |
| `CLK` · `LAT/STB` · `OE` | compartidas por los 8 puertos | lockstep obligatorio |
| `+5V0` | fuentes → filas | una fuente por fila, 2 inyecciones 12 AWG |
| `0V` | retorno común | punto estrella; referencia GND de datos |
| `PE` | gabinete y estructura | no se usa como retorno de 5 V |
| `F1L…F4R` · `FC` | protección | fusibles 20 A por rama · 2 A control |

## Correspondencia con el simulador

Lo ya verificado en [`../simulator/`](../simulator/README.md) es lo que hay que reproducir en hardware:

| Simulador | Bloque de hardware | Número verificado |
|---|---|---|
| `quantize` | `rgb_to_bitplane` | `duty = (v/255)^γ`, γ 2.2 |
| `bitplanes.py` (layout `[bit][canal][y][x]`) | `bitplane_store` (BRAM) | 5 bits/color · 60 KB = 48 % de BRAM |
| `timing.refresh_hz` | `bcm_sequencer` | 2048 clocks/bitplane → 197 Hz @ 12,5 MHz |
| máscara LED (gap 0.65, circular) | máscara física del módulo P5 | LED ≈ ⅓ del paso · pitch 5 mm |
| `viewing.py` | instalación | 5 m ↔ 416×208 px (monitor 32" 1080p a 60 cm) |

## Condicionantes abiertos

- **Contrato de wire**: ¿la PC manda RGB888 o bitplanes ya serializados? Cambia dónde vive la conversión. [`14`](14_software_contenido.md).
- **Familia del IC driver del módulo**: si es S-PWM interno (MBI5153/FM6353), el modelo BCM no aplica y el protocolo es otro. [`08`](08_hub75e_y_panel_p5.md).
- **Mapeo de scan 1/8**: la incógnita principal del driver; se resuelve en el Paso 2 del bring-up. [`11`](11_arquitectura_colorlight_5a75b.md).
- **Revisión de placa**: comprar 8.0 u 8.2; otra revisión implica otro pinout y otro archivo de plataforma LiteX.

## Fuentes

Las fuentes externas de esta cadena (chubby75, LiteX, YosysHQ) están en [`11_arquitectura_colorlight_5a75b.md`](11_arquitectura_colorlight_5a75b.md); no se duplican acá.
