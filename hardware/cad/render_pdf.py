# -*- coding: utf-8 -*-
"""Render PDF portable con WeasyPrint; no necesita FreeCAD ni navegador.

Preparación: python -m pip install -r hardware/cad/requirements-pdf.txt
Uso: python hardware/cad/render_pdf.py
Antes: ejecutar especificaciones.py --sin-pdf con Python de FreeCAD.
"""
import hashlib
import json
import os
from pathlib import Path
import tempfile

from weasyprint import HTML

base = Path(__file__).resolve().parent
out = base / "build"
html_path = out / "especificaciones_cartel.html"
pdf_path = out / "especificaciones_cartel.pdf"
revision_path = out / "revision_documental.json"
revision = json.loads(revision_path.read_text(encoding="utf-8"))
assert hashlib.sha256(html_path.read_bytes()).hexdigest() == revision["html_sha256"], "HTML cambiado: regenerar ficha"
assert hashlib.sha256((base / "monoposte.py").read_bytes()).hexdigest() == revision["fuente_sha256"], "Geometría cambiada: regenerar modelo/ficha"
manifest = json.loads((out / "vistas_manifest.json").read_text(encoding="utf-8"))
assert manifest["fuente_sha256"] == revision["geometria_sha256"], "Vistas desactualizadas"
for nombre, digest in manifest["imagenes"].items():
    assert hashlib.sha256((out / nombre).read_bytes()).hexdigest() == digest, "Imagen cambiada: " + nombre

with tempfile.NamedTemporaryFile(suffix=".pdf", dir=out, delete=False) as temporal:
    nuevo = Path(temporal.name)
try:
    rendered = HTML(filename=str(html_path)).render()
    assert rendered.pages, "Documento sin páginas"
    rendered.write_pdf(str(nuevo))
    assert nuevo.read_bytes().startswith(b"%PDF-") and nuevo.stat().st_size > 1000
    os.replace(nuevo, pdf_path)
finally:
    nuevo.unlink(missing_ok=True)
revision.update(pdf_estado="actualizado", pdf_bytes=pdf_path.stat().st_size,
                pdf_sha256=hashlib.sha256(pdf_path.read_bytes()).hexdigest(),
                pdf_motor="WeasyPrint", pdf_paginas=len(rendered.pages))
revision_path.write_text(json.dumps(revision, ensure_ascii=False, indent=2), encoding="utf-8")
print(f"PDF actualizado: {pdf_path} · {len(rendered.pages)} páginas · {pdf_path.stat().st_size} bytes")
