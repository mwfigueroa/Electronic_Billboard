# -*- coding: utf-8 -*-
"""Regenera CAD, siete vistas R2 y registro de ejecución en una GUI aislada."""
import contextlib
import hashlib
import json
import os
import traceback

import FreeCAD as App
import FreeCADGui as Gui
from PySide import QtCore, QtWidgets
from PIL import Image, ImageChops, ImageOps
from pivy import coin  # registra los wrappers antes de getCameraNode()

base = os.path.dirname(os.path.abspath(__file__))
out = os.path.join(base, "build")
os.makedirs(out, exist_ok=True)


def generar():
    gen = os.path.join(base, "monoposte.py")
    ns = {"__file__": gen, "__name__": "__main__"}
    with open(gen, encoding="utf-8") as f:
        exec(compile(f.read(), gen, "exec"), ns)
    doc = App.ActiveDocument
    Gui.setActiveDocument(doc.Name)
    Gui.updateGui()
    QtWidgets.QApplication.processEvents()
    view = Gui.getDocument(doc.Name).activeView()
    view.setCameraType("Orthographic")
    objetos = [o for o in doc.Objects if o.TypeId == "Part::Feature"]
    gab = doc.getObjectsByLabel("Cartel — gabinete LED")[0]
    iso = App.Rotation(App.Vector(1, 1, 0), App.Vector(-1, 1, 2), App.Vector(1, -1, 1), "ZXY")
    rear_iso = App.Rotation(App.Vector(-1, 1, 0), App.Vector(-1, -1, 2), App.Vector(1, 1, 1), "ZXY")
    front = App.Rotation(App.Vector(1, 0, 0), 90)
    rear = App.Rotation(App.Vector(0, 0, 1), 180).multiply(front)
    right = App.Rotation(App.Vector(0, 0, 1), 90).multiply(front)

    def capturar(nombre, rotacion, seleccion):
        for o in objetos:
            o.ViewObject.Visibility = o in seleccion
        # Cámara Coin explícita: fitAll durante una transición de vistas de
        # FreeCAD puede conservar planos de recorte y producir PNG blancos.
        bounds = seleccion[0].Shape.BoundBox
        for o in seleccion[1:]:
            bounds = bounds.united(o.Shape.BoundBox)
        centro = bounds.Center
        inversa = rotacion.inverted()
        esquinas = [inversa.multVec(App.Vector(x, y, z) - centro)
                    for x in (bounds.XMin, bounds.XMax)
                    for y in (bounds.YMin, bounds.YMax)
                    for z in (bounds.ZMin, bounds.ZMax)]
        ancho = max(p.x for p in esquinas) - min(p.x for p in esquinas)
        alto = max(p.y for p in esquinas) - min(p.y for p in esquinas)
        altura_camara = max(alto, ancho / 1.5) * 1.12
        distancia = max(bounds.DiagonalLength * 3, 100)
        posicion = centro + rotacion.multVec(App.Vector(0, 0, distancia))
        camera = view.getCameraNode()
        camera.orientation.setValue(*rotacion.Q)
        camera.position.setValue(posicion.x, posicion.y, posicion.z)
        camera.height.setValue(altura_camara)
        camera.focalDistance.setValue(distancia)
        camera.nearDistance.setValue(distancia / 10)
        camera.farDistance.setValue(distancia * 3)
        Gui.updateGui()
        QtWidgets.QApplication.processEvents()
        ruta = os.path.join(out, f"vista_{nombre}.png")
        view.saveImage(ruta, 1800, 1200, "White")
        # Elimina margen blanco excesivo: detalles legibles también en el PDF.
        with Image.open(ruta) as im:
            rgb = im.convert("RGB")
            limites = ImageChops.difference(rgb, Image.new("RGB", rgb.size, "white")).getbbox()
            if not limites or limites[3] - limites[1] < 100:
                raise RuntimeError("Vista vacía o recortada: " + nombre)
            recorte = ImageOps.expand(rgb.crop(limites), border=32, fill="white")
            recorte.save(ruta)
        print("vista:", nombre)

    estructura = [o for o in objetos if not o.Referencia and not o.Label.startswith("Jabalina")]
    for nombre, rot in (("iso", iso), ("frente", front), ("dorso", rear), ("perfil", right)):
        capturar(nombre, rot, estructura)
    interior = [o for o in gab.Group if not o.Label.startswith(("Carcasa", "Puerta", "Capota", "Filtro", "Ventilador", "Junta EPDM puerta"))]
    capturar("gabinete_interior", rear_iso, interior)
    brida = [o for o in objetos if o.Label.startswith(("Brida", "Tornillo brida", "Cabeza brida", "Arandela brida", "Tuerca brida"))]
    capturar("detalle_brida", iso, brida)

    originales = {}
    try:
        for puerta, x, y, signo in ns["PUERTAS"]:
            numero = "#1" if "#1" in puerta.Label else "#2"
            if ns["LADO_MASTIL"] > 0:
                x, signo = -x, -signo
            for o in gab.Group:
                if o != puerta and not (numero in o.Label and o.Label.startswith(("Ventilador", "Filtro", "Capota"))):
                    continue
                originales[o.Name] = o.Shape.copy()
                s = o.Shape.copy()
                s.rotate(App.Vector(x, y, 0), App.Vector(0, 0, 1), signo * 100)
                o.Shape = s
        doc.recompute()
        capturar("puertas_abiertas", rear_iso, list(gab.Group))
    finally:
        for nombre, s in originales.items():
            doc.getObject(nombre).Shape = s
        doc.recompute()
    capturar("iso", iso, estructura)
    doc.save()
    manifest = {"fuente_sha256": doc.getObject("Revision").FuenteSHA256,
                "lado_mastil": ns["LADO_MASTIL"], "imagenes": {}}
    for nombre in ("iso", "frente", "dorso", "perfil", "gabinete_interior", "detalle_brida", "puertas_abiertas"):
        archivo = f"vista_{nombre}.png"
        with open(os.path.join(out, archivo), "rb") as f:
            manifest["imagenes"][archivo] = hashlib.sha256(f.read()).hexdigest()
    with open(os.path.join(out, "vistas_manifest.json"), "w", encoding="utf-8") as f:
        json.dump(manifest, f, ensure_ascii=False, indent=2)
    print("OK: CAD y siete vistas actualizados; documento guardado con puertas cerradas")


def main():
    try:
        with open(os.path.join(out, "vistas.log"), "w", encoding="utf-8") as log:
            with contextlib.redirect_stdout(log), contextlib.redirect_stderr(log):
                try:
                    generar()
                except Exception:
                    traceback.print_exc()
    finally:
        QtWidgets.QApplication.quit()


# Las macros pasadas por CLI pueden cargarse antes de existir una vista GUI.
QtCore.QTimer.singleShot(500, main)
