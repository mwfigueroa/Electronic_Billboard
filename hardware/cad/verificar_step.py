# -*- coding: utf-8 -*-
"""Reimporta build/monoposte.step y reporta sólidos y caja envolvente (ida y vuelta)."""
import os
import sys

import FreeCAD as App
import Part

try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except (AttributeError, ValueError):
    pass

ruta = os.path.join(os.path.dirname(os.path.abspath(__file__)), "build", "monoposte.step")
s = Part.read(ruta)
assert not s.isNull() and s.isValid() and s.Solids, "STEP vacío o inválido"
doc = App.openDocument(os.path.join(os.path.dirname(ruta), "monoposte.FCStd"))
fisicos = [o for o in doc.Objects if o.TypeId == "Part::Feature" and not o.Referencia]
volumen = sum(o.Shape.Volume for o in fisicos)
assert abs(s.Volume - volumen) < max(1, volumen * 1e-7), "STEP y FCStd tienen volúmenes distintos"
bb = s.BoundBox
print(f"STEP OK: {len(s.Solids)} sólidos · caja {bb.XLength:.0f} × {bb.YLength:.0f} × {bb.ZLength:.0f} mm "
       f"· z de {bb.ZMin:.0f} a {bb.ZMax:.0f} · {os.path.getsize(ruta) / 1024:.0f} KB")
App.closeDocument(doc.Name)
