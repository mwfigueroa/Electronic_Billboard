# -*- coding: utf-8 -*-
"""Verifica el FCStd guardado contra lo que dice el código: sin constantes a mano.

Reconstruye el modelo en memoria (GENERAR_SALIDA=False, ~5 s) para derivar las
cotas y masas esperadas de los parámetros de `monoposte.py`, y las contrasta con
el `build/monoposte.FCStd` en disco. Así un cambio legítimo de parámetro (otra
altura libre, otro espesor) no rompe la verificación: solo falla si el FCStd
quedó viejo o si la geometría no cumple lo que el código promete.

    "C:\\Program Files\\FreeCAD 1.1\\bin\\python.exe" P:\\Billboard\\hardware\\cad\\medir.py
"""
from pathlib import Path
import sys

import FreeCAD as App
import Part

try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except (AttributeError, ValueError):
    pass

base = Path(__file__).resolve().parent
gen = base / "monoposte.py"
P = {"__file__": str(gen), "__name__": "medir", "GENERAR_SALIDA": False}
exec(compile(gen.read_text(encoding="utf-8"), str(gen), "exec"), P)
App.closeDocument(P["doc"].Name)

doc = App.openDocument(str(base / "build" / "monoposte.FCStd"))
objetos = [o for o in doc.Objects if o.TypeId == "Part::Feature"]
fallas = []


def conjunto(prefijo):
    seleccion = [o for o in objetos if o.Label.startswith(prefijo)]
    assert seleccion, prefijo
    b = seleccion[0].Shape.BoundBox
    for o in seleccion[1:]:
        b = b.united(o.Shape.BoundBox)
    return b


def medir(nombre, valores, esperados, tolerancia=0.01):
    ok = len(valores) == len(esperados) and all(abs(a - b) < tolerancia for a, b in zip(valores, esperados))
    print(("OK " if ok else "✗  ") + nombre, tuple(round(v, 3) for v in valores),
          "" if ok else f"esperado {tuple(round(e, 3) for e in esperados)}")
    if not ok:
        fallas.append(nombre)


# --- el FCStd es el de este código -----------------------------------------------
rev = doc.getObject("Revision")
if rev.FuenteSHA256 != P["VALIDACION"]["fuente_sha256"] or rev.LadoMastil != P["LADO_MASTIL"]:
    fallas.append("FCStd desactualizado respecto de monoposte.py: regenerar con vistas.py")
    print("✗  FCStd desactualizado respecto de monoposte.py")
else:
    print("OK FCStd generado por este mismo código (" + rev.Codigo + ")")

# --- el cartel ------------------------------------------------------------------
display_w, display_h = P["MOD_W"] * P["MOD_COLS"], P["MOD_H"] * P["MOD_FILAS"]
matriz = conjunto("Módulo P5")
medir("display ancho × alto", (matriz.XLength, matriz.ZLength), (display_w, display_h))
medir("display de … a … de altura", (matriz.ZMin, matriz.ZMax), (P["MOD_Z0"], P["MOD_Z0"] + display_h))
medir("píxeles a 5 mm de paso", (matriz.XLength / 5, matriz.ZLength / 5), (256, 128))
marco = conjunto("Marco frontal")
medir("frente del gabinete", (marco.XLength, marco.ZLength), (P["GAB_W"], P["GAB_H"]))
medir("borde alrededor del display", ((marco.XLength - display_w) / 2, (marco.ZLength - display_h) / 2), (30, 30))
# fondo del cuerpo: cara de chapa de la puerta, no los nudillos de la bisagra
caras_puerta = [f for o in objetos if o.Label.startswith("Puerta trasera") for f in o.Shape.Faces
                if f.BoundBox.YLength < 1e-6 and f.Area > 100000]
medir("fondo del cuerpo (marco → cara de puerta)", (max(f.BoundBox.YMax for f in caras_puerta) - marco.YMin,), (P["GAB_D"],))
capotas = conjunto("Capota")
medir("fondo con capotas", (capotas.YMax - marco.YMin,), (P["GAB_D"] + 60,))
sonda = Part.makeBox(matriz.XLength, 3, matriz.ZLength, App.Vector(matriz.XMin, matriz.YMin - 3, matriz.ZMin))
frontal = next(o for o in objetos if o.Label.startswith("Marco frontal"))
medir("marco sobre la cara de los LED (mm³)", (frontal.Shape.common(sonda).Volume,), (0,))
riel_kg = sum(o.Masa_kg for o in objetos if o.Label.startswith("Riel tubular"))
riel_area = P["RIEL_B"] * P["RIEL_H"] - (P["RIEL_B"] - 2 * P["RIEL_E"]) * (P["RIEL_H"] - 2 * P["RIEL_E"])
medir("masa de los 5 rieles tubulares (kg)", (riel_kg,), ((P["MOD_FILAS"] + 1) * display_w * riel_area * P["DENS"]["aluminio"],))

# --- el soporte -----------------------------------------------------------------
B, e = P["POSTE_B"], P["POSTE_E"]
mastil = next(o for o in objetos if o.Label.startswith("Mástil"))
seccion = mastil.Shape.common(Part.makeBox(2 * B, 2 * B, 1, App.Vector(-B, -B, 450)))
medir(f"sección íntegra del mástil a 0,45 m (mm²) — {B:g}×{B:g}×{e:g}", (seccion.Volume,), (B * B - (B - 2 * e) ** 2,))
mb = mastil.Shape.BoundBox
medir("mástil de … a … (mm)", (mb.ZMin, mb.ZMax), (P["POSTE_Z0"], P["POSTE_Z1"]))
brazo = next(o for o in objetos if o.Label.startswith("Brazo "))
bb = brazo.Shape.BoundBox
x_med = bb.XMin + (bb.XMax - bb.XMin) / 2 if P["LADO_MASTIL"] < 0 else bb.XMax - (bb.XMax - bb.XMin) / 2
z_med = (P["BRIDA_Z1"] + P["GAB_ZC"]) / 2
paredes = brazo.Shape.common(Part.makeLine(App.Vector(x_med, -200, z_med), App.Vector(x_med, 200, z_med)))
medir(f"dos paredes del brazo en Y (mm) — espesor {P['BRAZO_E']:g}", (paredes.Length,), (2 * P["BRAZO_E"],))
medir("altura libre bajo el cartel (mm)", (marco.ZMin,), (P["ALTURA_LIBRE"],))
tornillos = [o for o in objetos if o.Label.startswith("Tornillo brida")]
medir("tornillos de la brida", (len(tornillos),), (len(P["BRIDA_PUNTOS"]),))
invalidas = [o.Label for o in objetos if not o.Shape.isValid()]
if invalidas:
    fallas.append("formas inválidas: " + ", ".join(invalidas))
print(f"{'OK' if not invalidas else '✗ '} {len(objetos)} formas, {len(invalidas)} inválidas")
App.closeDocument(doc.Name)

if fallas:
    print("\nFALLAS:", *fallas, sep="\n  - ")
    raise SystemExit(1)
print("\nmedir.py: todo coincide con monoposte.py")
