# -*- coding: utf-8 -*-
"""Abre el modelo en la GUI de FreeCAD, en isométrica y encuadrado, y lo deja abierto.

    "C:\\Program Files\\FreeCAD 1.1\\bin\\freecad.exe" P:\\Billboard\\hardware\\cad\\abrir.py

Si build/monoposte.FCStd no existe, lo genera primero con monoposte.py.
"""
import os

import FreeCAD as App
import FreeCADGui as Gui

base = os.path.dirname(os.path.abspath(__file__))
fcstd = os.path.join(base, "build", "monoposte.FCStd")
if not os.path.exists(fcstd):
    gen = os.path.join(base, "monoposte.py")
    with open(gen, encoding="utf-8") as f:
        exec(compile(f.read(), gen, "exec"), {"__file__": gen, "__name__": "__main__"})
else:
    App.openDocument(fcstd)

view = Gui.ActiveDocument.ActiveView
view.viewIsometric()
view.fitAll()
