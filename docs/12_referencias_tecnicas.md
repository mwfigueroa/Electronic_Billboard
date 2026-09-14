# 12 — Referencias técnicas: Colorlight 5A-75B, ECP5 y entorno de desarrollo

Índice de documentación técnica para el driver propio. Arquitectura y decisiones en [`11_arquitectura_colorlight_5a75b.md`](11_arquitectura_colorlight_5a75b.md) y [`10_plataforma_driver.md`](10_plataforma_driver.md).

> **La Colorlight 5A-75B no tiene documentación oficial del fabricante.** No hay datasheet, esquemático ni nota de aplicación publicada por Colorlight: es una placa comercial de cartelería, no una placa de desarrollo. Todo lo que se sabe proviene de **ingeniería inversa de la comunidad**, principalmente el proyecto [chubby75](https://github.com/q3k/chubby75).
>
> Consecuencia práctica: **cada dato de esta página se verifica contra la placa física antes de confiar en él.** Los componentes y el pinout cambian entre revisiones, y hay discrepancias documentadas entre fuentes.

---

## 1. La placa — revisiones

Cuatro revisiones documentadas. **No son intercambiables.**

| | V6.1 | V7.0 | V8.0 | V8.2 |
|---|---|---|---|---|
| FPGA | LFE5U-25F | LFE5U-25F | LFE5U-25F-6BG256C | LFE5U-25F |
| Encapsulado | **CABGA381** | CABGA256 | CABGA256 | CABGA256 |
| SDRAM | 2× 1M × 16 bit | 2× 1M × 16 bit | **M12L64322A** 2M × 32, 8 MB | similar a 8.0 |
| PHY Ethernet | Broadcom B50612D | B50612D | **Realtek RTL8211FD** | RTL8211FD |
| SPI flash | 25Q16 (2 MB) | 25Q16 | **25Q32JVSIQ (4 MB)** | 25Q32 |
| LiteDRAM en LiteX | No | No | **Sí** | **Sí** |

**Comprar 8.0 u 8.2.** Motivos, en orden: son las únicas con soporte de LiteDRAM en `litex-boards`; tienen más SDRAM y más flash; y la 6.1 usa otro encapsulado, así que ni el archivo de restricciones se puede reutilizar.

Al recibir la placa, lo primero es leer la serigrafía y contrastar con el archivo `hardware_V<rev>.md` de chubby75 que corresponda.

### Componentes de la V8.0

| Ref | Componente | Detalle |
|---|---|---|
| U33 | Lattice ECP5 **LFE5U-25F-6BG256C** | 24.300 LUT, 1.008 Kbit EBR, speed grade 6, CABGA256 |
| U29 | ESMT **M12L64322A** | SDRAM 2M × 32 bit, 200 MHz, 8 MB |
| — | Winbond **25Q32JVSIQ** | SPI flash 32 Mbit para configuración |
| U11, U13 | Realtek **RTL8211FD** ×2 | PHY Gigabit Ethernet |
| — | **74HC245T** ×12 | Buffers octales, 56 salidas bufferadas a 5 V |

## 2. Pinout de la V8.0

Base para escribir el archivo `.lpf`. Fuente: [chubby75 `hardware_V8.0.md`](https://github.com/q3k/chubby75/blob/master/5a-75b/hardware_V8.0.md).

### Señales compartidas por los ocho conectores

| Señal HUB75 | Pin FPGA |
|---|---|
| `A` | N5 |
| `B` | N3 |
| `C` | P3 |
| `D` | P4 |
| `E` | N4 |
| `CLK` | M3 |
| `STB` / `LAT` | N1 |
| `OE` | M4 |

### RGB por conector

chubby75 nombra las señales `R0/G0/B0` y `R1/G1/B1`. Corresponden a `R1/G1/B1` (mitad superior) y `R2/G2/B2` (mitad inferior) de la nomenclatura HUB75 estándar usada en [`08_hub75e_y_panel_p5.md`](08_hub75e_y_panel_p5.md). **Cuidado con el desfasaje de nombres al escribir el `.lpf`.**

| Conector | R0 | G0 | B0 | R1 | G1 | B1 |
|---|---|---|---|---|---|---|
| J1 | C4 | D4 | E4 | D3 | F5 | E3 |
| J2 | F1 | F2 | G2 | G1 | H2 | H3 |
| J3 | B1 | C2 | C1 | D1 | E2 | E1 |
| J4 | P5 | R3 | P2 | R2 | T2 | N6 |
| J5 | T13 | R12 | R13 | R14 | T14 | P12 |
| J6 | R15 | T15 | P13 | P14 | N14 | H15 |
| J7 | G16 | H14 | G15 | F15 | F16 | E16 |
| J8 | D16 | E15 | C16 | B16 | C15 | B15 |

### Sistema

| Señal | Pin | Nota |
|---|---|---|
| Clock 25 MHz | **P6** | Generado por el PHY U13, no por un oscilador dedicado |
| Botón | R7 | Activo bajo, con pull-up |
| LED usuario | **T6 o P11** | **Discrepancia entre fuentes** — chubby75 indica T6, la guía de weigu indica P11. Verificar en la placa antes de usarlo como testigo de bring-up |
| JTAG | Header de 4 pines sin poblar | TCK, TMS, TDI, TDO + header de 2 pines con 3,3 V y GND |
| PHY reset / MDC / MDIO | R6 / R5 / T4 | Compartidos entre los dos PHY |

### Ejemplo de `.lpf`

```
LOCATE COMP "clk25"   SITE "P6";
IOBUF  PORT "clk25"   IO_TYPE=LVCMOS33;
FREQUENCY PORT "clk25" 25 MHz;

LOCATE COMP "hub_a"   SITE "N5";
LOCATE COMP "hub_b"   SITE "N3";
LOCATE COMP "hub_c"   SITE "P3";
LOCATE COMP "hub_clk" SITE "M3";
LOCATE COMP "hub_lat" SITE "N1";
LOCATE COMP "hub_oe"  SITE "M4";

LOCATE COMP "j1_r0"   SITE "C4";
LOCATE COMP "j1_g0"   SITE "D4";
LOCATE COMP "j1_b0"   SITE "E4";
LOCATE COMP "j1_r1"   SITE "D3";
LOCATE COMP "j1_g1"   SITE "F5";
LOCATE COMP "j1_b1"   SITE "E3";

IOBUF PORT "hub_a"  IO_TYPE=LVCMOS33 DRIVE=8 SLEWRATE=FAST;
```

Todas las salidas HUB75 van a `LVCMOS33`; el paso a 5 V lo hacen los 74HC245T de la placa. Ajustar `DRIVE` y `SLEWRATE` según lo que muestre el analizador lógico — ver TN1262.

## 3. El FPGA — Lattice ECP5

### Documentación oficial

| Documento | Código | Contenido |
|---|---|---|
| [ECP5 and ECP5-5G Family Data Sheet](https://www.latticesemi.com/-/media/LatticeSemi/Documents/DataSheets/ECP5/FPGA-DS-02012-3-1-ECP5-ECP5G-Family-Data-Sheet.ashx?document_id=50461) | FPGA-DS-02012 (ex DS1044) | Arquitectura, recursos, características eléctricas, timing, encapsulados |
| [sysIO Usage Guide](https://www.latticesemi.com/-/media/LatticeSemi/Documents/ApplicationNotes/EH/TN1262.ashx) | TN1262 | **Clave para este proyecto.** Estándares de I/O, drive strength, slew rate, bancos |
| [sysCLOCK PLL/DLL Design and Usage Guide](https://www.latticesemi.com/~/media/LatticeSemi/Documents/ApplicationNotes/EH/TN1263.pdf) | TN1263 | **Clave.** Generación del clock de píxel desde los 25 MHz de entrada |
| [Memory Usage Guide](https://www.latticesemi.com/-/media/LatticeSemi/Documents/ApplicationNotes/EH/TN1264.ashx) | TN1264 | **Clave.** EBR, inferencia de BRAM, modos doble puerto |
| High-Speed I/O Interface | TN1265 | DDR I/O, interfaces fuente-síncronas |
| Power Consumption and Management | TN1266 | Estimación de consumo |
| sysDSP Usage Guide | TN1267 | Bloques DSP — poco relevante acá |
| [Hardware Checklist](https://www.latticesemi.com/-/media/LatticeSemi/Documents/ApplicationNotes/EH/FPGA-TN-02038.ashx?document_id=50482) | FPGA-TN-02038 | Alimentación, configuración, desacoplo |
| SERDES/PCS Usage Guide | TN1261 | **No aplica**: los LFE5U no tienen SERDES (sí los LFE5UM) |

### Recursos del LFE5U-25F

| Recurso | Cantidad | Uso previsto |
|---|---:|---|
| LUT4 | 24.300 | Serializadores, secuenciador BCM, SoC |
| EBR (sysMEM) | **1.008 Kbit = 126 KB** | Bitplanes — ver presupuesto en doc 11 |
| PLL (sysCLOCK) | 2 | Clock de píxel derivado de los 25 MHz |
| Multiplicadores DSP 18×18 | 28 | Corrección de gamma, si se hace en hardware |
| I/O de usuario (CABGA256) | ~197 | Sobran: se usan ~56 para los ocho puertos |

## 4. Datasheets de los componentes de placa

| Componente | Qué buscar | Nota |
|---|---|---|
| ESMT **M12L64322A** | Timing de SDRAM, comandos, refresh | Modelo ya definido en LiteDRAM — no hace falta escribir el controlador |
| Winbond **25Q32JVSIQ** | Comandos SPI, sectores, protección | Necesario para el respaldo del bitstream de fábrica |
| Realtek **RTL8211FD** | RGMII, MDIO, estrapeo | Solo si se usa Ethernet; LiteEth lo cubre |
| **74HC245** | Umbrales de entrada, propagación, drive | **Leer la tabla de V_IH.** Ver la advertencia en doc 11 |

## 5. Entorno de desarrollo

Flujo completamente abierto, sin licencias ni registro.

| Herramienta | Función | Fuente |
|---|---|---|
| **Yosys** | Síntesis Verilog → netlist JSON | [YosysHQ/yosys](https://github.com/YosysHQ/yosys) |
| **nextpnr-ecp5** | Place & route | [YosysHQ/nextpnr](https://github.com/YosysHQ/nextpnr) |
| **Project Trellis** | Base de datos del dispositivo y `ecppack` | [YosysHQ/prjtrellis](https://github.com/YosysHQ/prjtrellis) |
| **openFPGALoader** | Carga por JTAG a SRAM o a flash | [trabucayre/openFPGALoader](https://github.com/trabucayre/openFPGALoader) |
| **Verilator** | Simulación rápida y testbench | Incluido en oss-cad-suite |
| **cocotb** | Testbench en Python | Opcional, muy útil para el secuenciador BCM |
| **LiteX** + `litex-boards` | SoC, LiteEth, LiteDRAM | [enjoy-digital/litex](https://github.com/enjoy-digital/litex) |
| **GTKWave** / **Surfer** | Visor de waveforms | Incluido en oss-cad-suite |

### Instalación

La vía recomendada es **[oss-cad-suite](https://github.com/YosysHQ/oss-cad-suite-build/releases)**, que trae todo lo anterior compilado en un solo paquete con builds nocturnos. Hay binarios para **Windows x64**, Linux (x64, arm, arm64, riscv64) y macOS.

```
# Extraer y activar el entorno
source <ruta>/oss-cad-suite/environment
```

Sobre Windows 11 hay dos caminos:

- **Nativo (x64)**: funciona para síntesis, P&R y simulación. La parte que suele dar problemas es el acceso USB de openFPGALoader, que puede necesitar WinUSB/Zadig.
- **WSL2 con el build linux-x64**: más parejo con la documentación de la comunidad. Requiere `usbipd-win` para pasar el programador USB a la VM.

Sugerencia: síntesis y simulación donde resulte cómodo, y la carga por JTAG desde donde el USB funcione sin pelear.

### Flujo de build

```
yosys -p "read_verilog src/*.v; synth_ecp5 -json build/top.json"

nextpnr-ecp5 --25k --package CABGA256 --speed 6 \
             --json build/top.json \
             --lpf constraints/colorlight_5a75b_v8.lpf \
             --textcfg build/top.config

ecppack --compress build/top.config build/top.bit
```

`--25k` selecciona el LFE5U-25F, `--package CABGA256` y `--speed 6` corresponden al `-6BG256C` de la revisión 8.0. **Con una V6.1 hay que usar `CABGA381`.**

### Programador JTAG

La placa trae un **header de 4 pines sin poblar** con TCK, TMS, TDI y TDO, más uno de 2 pines con 3,3 V y GND. Hay que soldarles pines.

Opciones de adaptador, todas soportadas por openFPGALoader:

| Adaptador | Costo | Nota |
|---|---|---|
| **Raspberry Pi Pico con firmware DirtyJTAG** | ~USD 5 | Es lo que usa la guía de weigu para esta placa. Barato y probado |
| FT2232H mini-module | ~USD 12–15 | Más rápido, `-c ft2232` |
| FT232RL | ~USD 3 | Funciona en modo bit-bang, lento |

```
# Cargar a SRAM — se pierde al cortar la alimentación, ideal para iterar
openFPGALoader -c dirtyJtag build/top.bit

# Escribir a la SPI flash — persistente, arranca solo
openFPGALoader -c dirtyJtag build/top.bit -f --unprotect-flash
```

> **Durante todo el bring-up, cargar solo a SRAM.** Escribir la flash recién cuando el diseño esté estable, y siempre después de haber respaldado el bitstream de fábrica.

## 6. Referencias de la comunidad

| Recurso | Contenido |
|---|---|
| [q3k/chubby75](https://github.com/q3k/chubby75) | **Fuente primaria.** Ingeniería inversa de 5A-75B, 5A-75E y Linsn RV901T. Pinouts por revisión, fotos, notas de JTAG |
| [YosysHQ: Introducing the Colorlight 5A-75B](https://blog.yosyshq.com/p/colorlight-part-1/) | Presentación de la placa como plataforma de desarrollo |
| [weigu.lu — Using the Colorlight 5A-75B](https://www.weigu.lu/other_projects/fpga/fpga_ecp5_5a75b/index.html) | Guía práctica end-to-end sobre V8: programador, LPF, comandos, ejemplos |
| [kholia/Colorlight-5A-75B](https://github.com/kholia/Colorlight-5A-75B) | Notas y ejemplos |
| [tomverbeure — Colorlight i5 as FPGA dev board](https://tomverbeure.github.io/2021/01/22/The-Colorlight-i5-as-FPGA-development-board.html) | Placa hermana; mucho contexto aplicable |
| [litex-boards: plataforma](https://github.com/litex-hub/litex-boards/blob/master/litex_boards/platforms/colorlight_5a_75b.py) | Definición de pines por revisión, lista para reutilizar |
| [litex-boards: target](https://github.com/litex-hub/litex-boards/blob/master/litex_boards/targets/colorlight_5a_75x.py) | SoC completo con LiteEth y LiteDRAM |
| [prjtrellis examples](https://github.com/YosysHQ/prjtrellis/tree/master/examples) | Ejemplos mínimos del flujo ECP5 |

## 7. Verificar contra la placa física

Lista de lo que **no** debe darse por cierto hasta comprobarlo, por ser dato de ingeniería inversa o por haber discrepancias entre fuentes:

- [ ] Revisión serigrafiada, y que coincida con el `hardware_V<rev>.md` usado.
- [ ] Encapsulado del FPGA — determina `--package` en nextpnr.
- [ ] Parte exacta de SDRAM y de SPI flash (varían dentro de una misma revisión según lote).
- [ ] **Pin del LED de usuario**: T6 según chubby75, P11 según weigu. Resolver con un bitstream de parpadeo antes de usarlo como testigo.
- [ ] Continuidad de los pines del header JTAG antes de soldar.
- [ ] Que los 74HC245T conmuten limpio con entrada de 3,3 V al clock de trabajo elegido.
- [ ] Tamaño real de la SPI flash, leyéndola completa antes de escribir.

## 8. Orden de lectura sugerido

Para arrancar el driver sin leer 500 páginas:

1. `hardware_V8.0.md` de chubby75 — el pinout es lo único imprescindible al principio.
2. La guía de weigu — flujo completo funcionando sobre esta placa.
3. **TN1263** (PLL) — para generar el clock de píxel.
4. **TN1264** (memoria) — para inferir BRAM correctamente.
5. **TN1262** (sysIO) — cuando haya que ajustar drive y slew rate contra el analizador lógico.
6. El datasheet FPGA-DS-02012 — como consulta puntual, no de corrido.

LiteX recién entra en el Paso 5 del bring-up, cuando haya que sumar red y contenido.
