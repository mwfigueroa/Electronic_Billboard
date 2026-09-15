# Toolchain FPGA — instalación de OSS CAD Suite

**Fecha:** 2026-09-15
**Máquina:** WSL2 (Ubuntu 24.04, x86_64), usuario `laboratorio`

Se reemplazó la cadena FPGA de los repos de Ubuntu por la distribución binaria
oficial de YosysHQ, **OSS CAD Suite**, build `20260915`.

---

## 1. Instalación

Origen: `YosysHQ/oss-cad-suite-build`, release `2026-09-15`
Asset: `oss-cad-suite-linux-x64-20260915.tgz` (708 MB, HTTP 200)

```bash
curl -L -o oss-cad-suite.tgz \
  https://github.com/YosysHQ/oss-cad-suite-build/releases/download/2026-09-15/oss-cad-suite-linux-x64-20260915.tgz
cd ~ && tar xzf oss-cad-suite.tgz
```

Destino: `~/oss-cad-suite` (2.5 GB). Se instaló en `$HOME` y no en `/opt` para
evitar `sudo` y porque la suite es autocontenida (no toca el sistema).
El tarball se borró tras extraer.

> La suite **no es reubicable a ciegas**: los scripts calculan su prefijo desde
> la ruta del propio ejecutable. Si se mueve el directorio, hay que regenerar
> los wrappers del punto 3.

## 2. Desinstalación de lo anterior

Paquetes apt eliminados con `remove --purge`:

```
yosys nextpnr-ice40 nextpnr-ecp5 fpga-icestorm fpga-trellis
openfpgaloader iverilog verilator gtkwave
ghdl ghdl-common ghdl-mcode
```

Huérfanos específicos de FPGA purgados después:

```
fpga-icestorm-chipdb fpga-trellis-database
nextpnr-ice40-chipdb nextpnr-ecp5-chipdb
yosys-abc libsystemc libsystemc-dev
```

Se simuló cada borrado con `apt-get -s` antes de ejecutarlo: no se arrastró
ningún paquete del sistema y no quedaron reglas udev sueltas en
`/etc/udev/rules.d/`.

**Pendiente opcional:** quedan marcados como auto-removibles otros huérfanos de
gtkwave/verilator (`gir1.2-*`, `python3-gi-cairo`, `python3-cairo`, `xdot`,
`libftdi1`, `fonts-font-awesome`, `sphinx-rtd-theme-common`, `libjudydebian1`,
`libboost-iostreams1.83.0`, …). **No** se ejecutó `apt autoremove` porque esos
paquetes GTK/Python pueden hacer falta para otras cosas. Revisar antes de correrlo.

## 3. Integración en el PATH

Se crearon **148 wrappers** en `~/.local/bin` (ya estaba en el PATH), uno por
herramienta:

```sh
#!/bin/sh
exec "/home/laboratorio/oss-cad-suite/bin/yosys" "$@"
```

Regenerarlos si se mueve la suite:

```bash
SUITE=$HOME/oss-cad-suite
SKIP="bwrap dot lsusb openocd xdot"
for f in "$SUITE"/bin/*; do
  b=$(basename "$f")
  case " $SKIP " in *" $b "*) continue;; esac
  printf '#!/bin/sh\nexec "%s/bin/%s" "$@"\n' "$SUITE" "$b" > ~/.local/bin/"$b"
  chmod +x ~/.local/bin/"$b"
done
```

### Por qué wrappers y no symlinks

Los ejecutables de `oss-cad-suite/bin/` son scripts que resuelven su prefijo con
`dirname "${BASH_SOURCE[0]}"`, sin `readlink` sobre el propio archivo. Con un
symlink en `~/.local/bin`, `BASH_SOURCE` es la ruta del enlace y el script busca
su loader en `~/.local/lib`:

```
/home/laboratorio/.local/bin/yosys: line 9:
  /home/laboratorio/.local/lib/ld-linux-x86-64.so.2: No such file or directory
```

El wrapper con `exec` a la ruta real evita el problema. Se probó: los symlinks
fallan, los wrappers funcionan.

### Herramientas omitidas del PATH global

`bwrap`, `dot`, `lsusb`, `openocd`, `xdot` — la suite trae su versión y
`~/.local/bin` precede a `/usr/bin`, así que habrían tapado utilidades del
sistema (`bwrap` lo usa flatpak, `dot` es graphviz). Siguen disponibles dentro
de `ossenv`.

## 4. Entorno completo (`ossenv`)

Añadido a `~/.bashrc`:

```bash
ossenv() { . "$HOME/oss-cad-suite/environment"; }
```

`ossenv` activa el entorno completo estilo virtualenv (Python 3.11 propio con
amaranth, `VERILATOR_ROOT`, `GHDL_PREFIX`, prompt modificado); `deactivate` lo
revierte.

**No se sourceó `environment` en el `.bashrc`** a propósito: ese script antepone
`oss-cad-suite/py3bin` al PATH, que contiene `python3`, `pip3`, `pydoc3`, etc., y
reemplazaría silenciosamente el Python del sistema en todas las shells.

## 5. Versiones

| Herramienta | Antes (apt) | Ahora (suite) |
|---|---|---|
| Yosys | 0.33 | 0.69+59 (`d85872386`) |
| nextpnr | 0.6 | 0.11.1-27 (`6030081a`) |
| Verilator | 5.020 | 5.053-devel |
| Icarus Verilog | 12.0 | 14.0-devel |
| GHDL | 4.1.0 | 7.0.0-dev + plugin Yosys |
| openFPGALoader | 0.12.0 | 1.1.1 |
| SymbiYosys | — | 0.69 |

También incluye icestorm, prjtrellis, prjoxide, apicula, himbaechel, GTKWave y
solvers SMT (yices, boolector, z3).

## 6. Verificación

Blinky iCE40 HX1K sintetizado en shell limpia (`env -i`, solo `~/.local/bin`),
sin sourcear nada:

```bash
yosys -q -p 'synth_ice40 -top top -json blink.json' blink.v
nextpnr-ice40 --hx1k --package tq144 --json blink.json --pcf blink.pcf --asc blink.asc -q
icepack blink.asc blink.bin      # -> 32220 bytes
iverilog -o blink.vvp blink.v    # OK
verilator --lint-only blink.v    # OK
```

`yosys` emite `Warning: Feature 'write_xaiger2' is experimental` durante
`synth_ice40`; es informativo y no afecta el bitstream.

### Proyecto de prueba permanente

Hay dos proyectos de prueba que ejercitan el flujo completo y sirven para
revalidar el toolchain tras cualquier actualización:

| Proyecto | Target | Flujo | Comprobación |
|---|---|---|---|
| `blinky-icestick/` | iCE40HX1K-TQ144 | `synth_ice40` → `nextpnr-ice40` → `icepack` | `make clean && make all sim lint timing stats` |
| `blinky-5a75b/` | ECP5 LFE5U-25F-6BG256C | `synth_ecp5` → `nextpnr-ecp5` → `ecppack` | `make clean && make all sim lint stats` |

Todos los objetivos pasan en ambos. Ver el `README.md` de cada uno.

`blinky-5a75b/` no es solo una prueba de toolchain: es el **Paso 0 del bring-up**
de [`docs/11_arquitectura_colorlight_5a75b.md`](docs/11_arquitectura_colorlight_5a75b.md)
y está diseñado para resolver sobre la placa la discrepancia del pin del LED de
usuario (T6 vs P11) que la sección 7 de `docs/12_referencias_tecnicas.md` deja
abierta.

## 7. Pendiente para trabajar con hardware

- ~~El usuario está en `plugdev` pero no en `dialout`~~ — **hecho el 2026-09-15**:
  `sudo usermod -aG dialout laboratorio`. Efectivo en sesiones nuevas; para WSL,
  `wsl --shutdown` desde Windows.
- En WSL2 el USB no se ve por defecto: hace falta `usbipd attach` desde Windows
  para exponer la placa a la distro.
- ~~Reglas udev de openFPGALoader~~ — **hecho el 2026-09-15**. La suite solo
  trae las de OpenOCD (`~/oss-cad-suite/share/openocd/contrib/60-openocd.rules`),
  así que se tomaron del upstream (`trabucayre/openFPGALoader`, rama `master`):

  ```bash
  curl -sSL -o 99-openfpgaloader.rules \
    https://raw.githubusercontent.com/trabucayre/openFPGALoader/master/99-openfpgaloader.rules
  sudo install -m 0644 -o root -g root 99-openfpgaloader.rules /etc/udev/rules.d/
  sudo udevadm control --reload-rules
  sudo udevadm trigger --subsystem-match=usb --action=change
  ```

  23 reglas `idVendor`, todas con `GROUP="plugdev"` + `TAG+="uaccess"`; el usuario
  ya está en `plugdev`. Validadas con `udevadm verify` (Success: 1, Fail: 0).
  WSL2 corre systemd con `systemd-udevd` activo, así que las reglas se aplican.

  Se bajaron de `master` y no del tag `v1.1.1` (la versión de openFPGALoader que
  trae la suite). Comprobado: ambos archivos son **idénticos** — 72 líneas,
  `diff` vacío —, porque `v1.1.1` es el tag más reciente del repo y `master` no
  ha tocado ese archivo desde la release. Si en el futuro se reinstalan las
  reglas, conviene volver a comparar contra el tag que corresponda al binario:

  ```bash
  openFPGALoader --Version   # -> versión instalada, p. ej. v1.1.1
  curl -sSL -o /tmp/rules-tag \
    https://raw.githubusercontent.com/trabucayre/openFPGALoader/v1.1.1/99-openfpgaloader.rules
  diff /tmp/rules-tag /etc/udev/rules.d/99-openfpgaloader.rules
  ```

  Ya existía `52-digilent-usb.rules`, que no se tocó: numera más bajo, así que
  las de openFPGALoader se evalúan después y ganan en caso de solaparse en algún
  VID:PID de Digilent.
