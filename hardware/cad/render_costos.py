# -*- coding: utf-8 -*-
"""Documentos de costos regenerables en build/ (MD + HTML + PDF).

Fuentes en `docs/` y salidas en `hardware/cad/build/`:

    docs/19_costos_argentina.md  ->  costos_cartel.*
    docs/02_bom.md               ->  bom_cartel.*
    docs/13_bom_desarrollo.md    ->  bom_desarrollo.*

El PDF se renderiza con WeasyPrint si está instalado; si no, con Edge o Chrome
headless (es el mismo camino que usa `especificaciones.py` en Windows). Desde
WSL funciona invocando el navegador de Windows y traduciendo las rutas.

Uso:
    python hardware/cad/render_costos.py

No depende de FreeCAD. El manifiesto `costos_render.json` deja los SHA-256 de
fuentes y salidas para detectar documentos viejos.
"""
import hashlib
import html
import json
import os
import re
import shutil
import subprocess
import sys
import time
from pathlib import Path

try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except (AttributeError, ValueError):
    pass

BASE = Path(__file__).resolve().parent
RAIZ = BASE.parent.parent
OUT = BASE / "build"

DOCUMENTOS = (
    ("costos_cartel", RAIZ / "docs" / "19_costos_argentina.md", "BILLBOARD · Costos · mercado argentino"),
    ("bom_cartel", RAIZ / "docs" / "02_bom.md", "BILLBOARD · BOM de puesta en marcha"),
    ("bom_desarrollo", RAIZ / "docs" / "13_bom_desarrollo.md", "BILLBOARD · BOM de desarrollo"),
)

CSS = """
@page { size: A4; margin: 14mm 14mm 16mm;
  @bottom-left { content: '__PIE__'; font-size: 8pt; color: #627682; }
  @bottom-right { content: counter(page) ' / ' counter(pages); font-size: 8pt; color: #627682; }
}
body { font: 10pt/1.38 'Segoe UI', Arial, sans-serif; color: #24303a; max-width: 185mm; margin: auto; }
h1 { font-size: 24pt; line-height: 1.12; color: #143647; margin: 0 0 8pt; }
h2 { font-size: 14pt; color: #143647; margin: 17pt 0 7pt; border-bottom: 2px solid #388899; padding-bottom: 4pt; break-after: avoid; }
h3 { font-size: 11.5pt; color: #143647; margin: 12pt 0 5pt; break-after: avoid; }
p { margin: 5pt 0; overflow-wrap: anywhere; }
blockquote { margin: 9pt 0; padding: 8pt 10pt; background: #fff7e8; border-left: 4px solid #c58a28; break-inside: avoid; }
table { border-collapse: collapse; width: 100%; margin: 6pt 0 10pt; font-size: 9pt; table-layout: fixed; }
thead { display: table-header-group; }
th { color: white; background: #244f61; text-align: left; padding: 6pt; }
th:first-child,td:first-child { width: 34%; }
td { padding: 5pt 6pt; vertical-align: top; border-bottom: 1px solid #d9e2e6; overflow-wrap: anywhere; }
tr { break-inside: avoid; }
tbody tr:nth-child(even) { background: #f2f6f8; }
code { font: 8.5pt Consolas, monospace; overflow-wrap: anywhere; }
a { color: #1d4ed8; text-decoration: none; }
li { margin: 4pt 0; }
@media screen { body { padding: 24px; background: white; } html { background: #e8eef1; } }
"""


def inline(texto: str) -> str:
    texto = html.escape(texto, quote=False)
    texto = re.sub(r"\\\*", "*", texto)                       # \* literal
    texto = re.sub(r"\[(.+?)\]\((.+?)\)", r'<a href="\2">\1</a>', texto)
    texto = re.sub(r"\*\*(.+?)\*\*", r"<strong>\1</strong>", texto)
    texto = re.sub(r"~~(.+?)~~", r"<del>\1</del>", texto)
    return re.sub(r"`(.+?)`", r"<code>\1</code>", texto)


def convertir(lineas) -> str:
    """Markdown mínimo: títulos, tablas, listas, citas, énfasis y enlaces."""
    resultado, filas = [], []
    lista: str | None = None

    def cerrar_tabla():
        if filas:
            resultado.append("<table><thead><tr>" + "".join(
                "<th>" + inline(c) + "</th>" for c in filas[0]) + "</tr></thead><tbody>")
            resultado.extend("<tr>" + "".join(
                "<td>" + inline(c) + "</td>" for c in r) + "</tr>" for r in filas[1:])
            resultado.append("</tbody></table>")
            filas.clear()

    def cerrar_lista():
        nonlocal lista
        if lista:
            resultado.append("</" + lista + ">")
            lista = None

    for ln in lineas:
        if ln.startswith("|"):
            cols = [c.strip() for c in ln.strip("|").split("|")]
            if not all(set(c) <= set("-:") for c in cols):
                filas.append(cols)
            continue
        cerrar_tabla()
        if ln.startswith("- "):
            if lista != "ul":
                cerrar_lista()
                resultado.append("<ul>")
                lista = "ul"
            resultado.append("<li>" + inline(ln[2:]) + "</li>")
            continue
        if re.match(r"^\d+\.\s", ln):
            if lista != "ol":
                cerrar_lista()
                resultado.append("<ol>")
                lista = "ol"
            resultado.append("<li>" + inline(re.sub(r"^\d+\.\s", "", ln)) + "</li>")
            continue
        cerrar_lista()
        if ln.startswith("### "):
            resultado.append("<h3>" + inline(ln[4:]) + "</h3>")
        elif ln.startswith("## "):
            resultado.append("<h2>" + inline(ln[3:]) + "</h2>")
        elif ln.startswith("# "):
            resultado.append("<h1>" + inline(ln[2:]) + "</h1>")
        elif ln.startswith("> "):
            resultado.append("<blockquote>" + inline(ln[2:]) + "</blockquote>")
        elif ln:
            resultado.append("<p>" + inline(ln) + "</p>")
    cerrar_tabla()
    cerrar_lista()
    return "\n".join(resultado)


def a_documento(md: str, pie: str) -> str:
    return ('<!doctype html><html lang="es"><head><meta charset="utf-8">'
            '<meta name="viewport" content="width=device-width,initial-scale=1">'
            "<style>" + CSS.replace("__PIE__", pie) + "</style></head><body>"
            + convertir(md.splitlines()) + "</body></html>")


def _win_path(p: Path) -> str:
    """\\mnt\\c\\... -> C:\\... para pasar argumentos al navegador de Windows."""
    s = str(p)
    m = re.match(r"^/mnt/([a-zA-Z])/(.*)$", s)
    if m:
        return m.group(1).upper() + ":\\" + m.group(2).replace("/", "\\")
    return s


def _file_uri(p: Path) -> str:
    if os.name == "nt":
        return p.as_uri()
    wp = _win_path(p)
    if re.match(r"^[A-Za-z]:\\", wp):
        return "file:///" + wp.replace("\\", "/")
    return p.as_uri()


def _perfil_navegador() -> str:
    v = os.environ.get("BILLBOARD_PDF_PROFILE")
    if v:
        return v
    if os.name == "nt" and os.environ.get("LOCALAPPDATA"):
        return os.path.join(os.environ["LOCALAPPDATA"], "billboard_costos_profile")
    if Path("/mnt/c/Windows").is_dir():
        cmd_win = Path("/mnt/c/Windows/System32/cmd.exe")
        if cmd_win.is_file():
            try:
                res = subprocess.run([str(cmd_win), "/c", "echo", "%LOCALAPPDATA%"],
                                     capture_output=True, text=True, timeout=15)
                valor = (res.stdout or "").strip()
                if valor and "%" not in valor and re.match(r"^[A-Za-z]:\\", valor):
                    return valor + "\\billboard_costos_profile"
            except (OSError, subprocess.TimeoutExpired):
                pass
    return r"C:\Windows\Temp\billboard_costos_profile"


def _navegadores():
    candidatos = []
    if os.name == "nt":
        candidatos += [
            r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe",
            r"C:\Program Files\Microsoft\Edge\Application\msedge.exe",
            r"C:\Program Files\Google\Chrome\Application\chrome.exe",
        ]
    else:
        candidatos += [
            "/mnt/c/Program Files (x86)/Microsoft/Edge/Application/msedge.exe",
            "/mnt/c/Program Files/Microsoft/Edge/Application/msedge.exe",
            "/mnt/c/Program Files/Google/Chrome/Application/chrome.exe",
        ]
        candidatos += [shutil.which(n) for n in ("google-chrome", "chromium", "chromium-browser", "microsoft-edge")]
    return [Path(c) for c in candidatos if c and Path(c).is_file()]


def render_con_weasyprint(html_path: Path, pdf_path: Path) -> bool:
    try:
        from weasyprint import HTML
    except ImportError:
        return False
    rendered = HTML(filename=str(html_path)).render()
    rendered.write_pdf(str(pdf_path))
    return True


def render_con_navegador(html_path: Path, pdf_path: Path) -> bool:
    for navegador in _navegadores():
        pdf_path.unlink(missing_ok=True)
        cmd = [
            str(navegador), "--headless=new", "--disable-gpu", "--no-first-run",
            "--disable-extensions", "--no-pdf-header-footer",
            "--allow-file-access-from-files",
            "--user-data-dir=" + _perfil_navegador(),
            "--print-to-pdf=" + (_win_path(pdf_path) if os.name != "nt" else str(pdf_path)),
            _file_uri(html_path),
        ]
        try:
            subprocess.run(cmd, timeout=90, capture_output=True, text=True, errors="replace")
        except (OSError, subprocess.TimeoutExpired):
            continue
        for _ in range(60):
            if (pdf_path.is_file() and pdf_path.stat().st_size > 1000
                    and pdf_path.read_bytes().startswith(b"%PDF-")):
                return True
            time.sleep(0.5)
        pdf_path.unlink(missing_ok=True)
    return False


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main() -> int:
    OUT.mkdir(parents=True, exist_ok=True)
    manifiesto = {"generado": time.strftime("%Y-%m-%dT%H:%M:%S%z"), "documentos": {}}
    fallos = 0
    for nombre, fuente, pie in DOCUMENTOS:
        if not fuente.is_file():
            print(f"falta la fuente: {fuente}")
            fallos += 1
            continue
        md = fuente.read_text(encoding="utf-8")
        md_destino = OUT / f"{nombre}.md"
        html_destino = OUT / f"{nombre}.html"
        pdf_destino = OUT / f"{nombre}.pdf"
        md_destino.write_text(md, encoding="utf-8")
        html_destino.write_text(a_documento(md, pie), encoding="utf-8")
        pdf_destino.unlink(missing_ok=True)   # un PDF viejo no es un resultado válido

        motor = "WeasyPrint" if render_con_weasyprint(html_destino, pdf_destino) else ""
        if not motor:
            motor = "navegador" if render_con_navegador(html_destino, pdf_destino) else ""
        if not motor:
            print(f"{nombre}: HTML actualizado, sin motor de PDF (¿WeasyPrint o Edge/Chrome?)")
            fallos += 1
            continue

        manifiesto["documentos"][nombre] = {
            "fuente": str(fuente.relative_to(RAIZ)).replace("\\", "/"),
            "fuente_sha256": sha256(fuente),
            "md": md_destino.name, "html": html_destino.name, "pdf": pdf_destino.name,
            "pdf_bytes": pdf_destino.stat().st_size, "pdf_motor": motor,
        }
        print(f"{nombre}: MD + HTML + PDF ({motor}, {pdf_destino.stat().st_size} bytes)")
    (OUT / "costos_render.json").write_text(
        json.dumps(manifiesto, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return 1 if fallos else 0


if __name__ == "__main__":
    raise SystemExit(main())
