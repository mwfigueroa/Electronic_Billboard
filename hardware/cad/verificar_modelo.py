# -*- coding: utf-8 -*-
"""Verificación geométrica; no sustituye cálculo estructural ni de estanqueidad."""
import itertools
import hashlib
from pathlib import Path
import FreeCAD as App
import Part


def hash_fuentes():
    base = Path(__file__).resolve().parent
    h = hashlib.sha256()
    for nombre in ("monoposte.py", "verificar_modelo.py"):
        h.update(nombre.encode("utf-8"))
        h.update((base / nombre).read_bytes())
    return h.hexdigest()


def verificar(doc, puertas=(), lado=-1):
    objetos = [o for o in doc.Objects if o.TypeId == "Part::Feature" and not o.Referencia]
    informe = {"revision": doc.getObject("Revision").Codigo,
               "fuente_sha256": doc.getObject("Revision").FuenteSHA256,
               "lado_mastil": lado, "objetos": len(objetos),
               "interferencias": [], "embebidos_hormigon": [], "errores": [],
               "puertas": [], "pasos_cable": []}
    for o in objetos:
        if o.Shape.isNull() or not o.Shape.isValid() or not o.Shape.Solids:
            informe["errores"].append("Forma inválida: " + o.Label)
    for a, b in itertools.combinations(objetos, 2):
        if not a.Shape.BoundBox.intersect(b.Shape.BoundBox):
            continue
        vol = a.Shape.common(b.Shape).Volume
        if vol <= 1.0:
            continue
        dato = {"a": a.Label, "b": b.Label, "volumen_mm3": round(vol, 3)}
        # Solo se admite embebido explícito contra hormigón. No se ocultan
        # interferencias de pernos con acero, ni de elementos de un mismo grupo.
        if (a.Embebida and b.Material == "hormigon") or (b.Embebida and a.Material == "hormigon"):
            informe["embebidos_hormigon"].append(dato)
        else:
            informe["interferencias"].append(dato)
            print("CHOQUE", dato)
    if informe["interferencias"]:
        informe["errores"].append(f"{len(informe['interferencias'])} interferencias inesperadas")

    # Barrido discreto del conjunto móvil completo: hoja, ventilador, filtro,
    # capotas. Junta y mecanismos aún no seleccionados no certifican cinemática.
    for puerta, x, y, signo in puertas:
        numero = "#1" if "#1" in puerta.Label else "#2"
        moviles = [o for o in objetos if o == puerta or
                   (numero in o.Label and o.Label.startswith(("Ventilador", "Filtro", "Capota")))]
        fijos = [o for o in objetos if o not in moviles and not o.Label.startswith("Junta EPDM puerta")]
        if lado > 0:
            x, signo = -x, -signo
        choques = []
        for ang in range(5, 111, 5):
            for movil in moviles:
                s = movil.Shape.copy()
                s.rotate(App.Vector(x, y, 0), App.Vector(0, 0, 1), signo * ang)
                for fijo in fijos:
                    if s.BoundBox.intersect(fijo.Shape.BoundBox) and s.common(fijo.Shape).Volume > 1:
                        choques.append({"angulo": ang, "movil": movil.Label, "contra": fijo.Label})
        informe["puertas"].append({"hoja": puerta.Label, "angulos_grados": "5..110, paso 5", "choques": choques})
        if choques:
            print("CHOQUES APERTURA", choques[:5])
            informe["errores"].append("Barrido de puerta con choques: " + puerta.Label)

    # Se prueban los pasos modelados; no la flexibilidad ni radio de curvatura del cable real.
    def libre(nombre, sonda, prefijos):
        if lado > 0:
            sonda = sonda.mirror(App.Vector(), App.Vector(1, 0, 0))
        volumen = sum(o.Shape.common(sonda).Volume for o in objetos if o.Label.startswith(prefijos))
        informe["pasos_cable"].append({"paso": nombre, "sonda_diametro_mm": 24, "obstruccion_mm3": round(volumen, 5)})
        if volumen > 1:
            informe["errores"].append("Paso obstruido: " + nombre)
    placa = next(o for o in objetos if o.Label.startswith("Placa base"))
    bridas = [o for o in objetos if o.Label.startswith("Brida")]
    for nombre, z0, h, prefijos in (
        ("Base y grout", 0, placa.Shape.BoundBox.ZMax + 1, ("Placa base", "Grout")),
        ("Brida doble", min(o.Shape.BoundBox.ZMin for o in bridas) - 1, 26, ("Brida", "Brazo")),
    ):
        libre(nombre, Part.makeCylinder(12, h, App.Vector(0, 0, z0)), prefijos)
    bast = next(o for o in objetos if o.Label.startswith("Bastidor"))
    b = bast.Shape.BoundBox
    x0 = b.XMin if lado < 0 else -b.XMax
    zc = (next(o for o in objetos if o.Label.startswith("Módulo P5 f1 c1")).Shape.BoundBox.ZMin +
          next(o for o in objetos if o.Label.startswith("Módulo P5 f4 c1")).Shape.BoundBox.ZMax) / 2
    libre("Montante de borde", Part.makeCylinder(12, 102, App.Vector(x0 - 1, 0, zc), App.Vector(1, 0, 0)), ("Bastidor",))
    return informe
