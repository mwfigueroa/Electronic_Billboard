# -*- coding: utf-8 -*-
"""Cartel LED con brazo lateral — R2.1, tubos comerciales del soporte.

Unidades mm; X hacia el vuelo, cara hacia -Y, Z vertical, suelo Z=0.
Ejecutar con el Python de FreeCAD o con freecadcmd.exe. GENERAR_SALIDA=False
construye y verifica en memoria. Los detalles estructurales son una propuesta:
la revisión geométrica no certifica uniones, anclajes ni fundación.
"""
import math
import os
import sys

import FreeCAD as App
import Part

try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except (AttributeError, ValueError):
    pass

V = App.Vector
REVISION = "R2.1 — tubos comerciales del soporte; gabinete R2"
LADO_MASTIL = globals().get("LADO_MASTIL", -1)
GAB_W, GAB_H, GAB_D = 1340.0, 700.0, 230.0  # cuerpo; capotas sobresalen 60 mm
ALTURA_LIBRE = 2500.0                     # bajo gabinete, NO gálibo de todo el brazo
GAB_Z0, GAB_Z1 = ALTURA_LIBRE, ALTURA_LIBRE + GAB_H
GAB_ZC = (GAB_Z0 + GAB_Z1) / 2
MOD_W, MOD_H, MOD_D = 320.0, 160.0, 20.0
MOD_COLS, MOD_FILAS = 4, 4
MARCO_E, MARCO_HOLGURA = 3.0, 1.0
JUNTA_E, JUNTA_D = 4.2, 6.0              # envolvente del EPDM Ø6 comprimido 30 %
CHAPA_E, PUERTA_E = 2.0, 2.0
BORDE_B, BORDE_W, BORDE_E = 120.0, 100.0, 4.0
PERIM_B, PERIM_H, PERIM_E = 60.0, 40.0, 3.0
CENTRAL_B, CENTRAL_E = 40.0, 2.0
RIEL_B, RIEL_H, RIEL_E = 30.0, 20.0, 2.0
FUENTE_L, FUENTE_A, FUENTE_H = 215.0, 30.0, 115.0
FUENTE_SEP = 40.0
BRAZO_RUN, BRAZO_RISE = 500.0, 500.0
BRAZO_B, BRAZO_E = 120.0, 4.75          # medida comercial seleccionada, solo soporte
POSTE_B, POSTE_E = 120.0, 6.35         # medida comercial seleccionada, solo soporte
BRIDA_L, BRIDA_W, BRIDA_E = 280.0, 220.0, 12.0
BRIDA_TORN_D, BRIDA_AGUJERO = 12.0, 14.0
BRIDA_PUNTOS = tuple((x, y) for x in (-105.0, 0.0, 105.0) for y in (-85.0, 85.0))
PASO_CABLE_D = 32.0
POSTE_Z1 = GAB_ZC - BRAZO_RISE - 2 * BRIDA_E
PLACA_B, PLACA_E, GROUT_E = 350.0, 16.0, 30.0
CARTELA_L, CARTELA_E = 100.0, 10.0
PERNO_D, PERNO_PATRON = 20.0, 280.0
PERNO_EMBEBIDO, PERNO_SOBRESALE = 500.0, 80.0
ZAPATA_A, ZAPATA_T = 1600.0, 600.0
JABALINA_D, JABALINA_L = 16.0, 1500.0
MASA_MODULO, MASA_FUENTE = 1.2, 0.93       # módulo pendiente de muestra
RESERVA_EQUIPAMIENTO_KG = 5.0            # cables, control, auxiliar, cierres, soldaduras
DENS = {"acero": 7850e-9, "aluminio": 2700e-9, "hormigon": 2400e-9,
        "EPDM": 1200e-9, "aislante": 1150e-9}

GAB_X0 = BRAZO_RUN
GAB_XC = GAB_X0 + GAB_W / 2
GAB_FRENTE = -120.0
GAB_Y1 = GAB_FRENTE + GAB_D
MOD_Y0 = GAB_FRENTE + MARCO_E
MOD_Y1 = MOD_Y0 + MOD_D
MOD_X0 = GAB_XC - MOD_W * MOD_COLS / 2
MOD_Z0 = GAB_Z0 + (GAB_H - MOD_H * MOD_FILAS) / 2
BAST_Y0 = MOD_Y1 + RIEL_B + 2.0
BORDE_X0 = GAB_X0 + CHAPA_E
BRIDA_Z1 = POSTE_Z1 + 2 * BRIDA_E
PLACA_Z0, POSTE_Z0 = GROUT_E, GROUT_E + PLACA_E
BRAZO_ANGULO = math.degrees(math.atan2(BRAZO_RISE, BORDE_X0))


def caja(l, w, h, x, y, z):
    return Part.makeBox(l, w, h, V(x, y, z))


def hueco(l, w, h, e, x, y, z, eje):
    if min(l, w, h) <= 0 or e <= 0:
        raise ValueError("Perfil con dimensiones no positivas")
    exterior = caja(l, w, h, x, y, z)
    if eje == "x":
        interior = caja(l + 2, w - 2 * e, h - 2 * e, x - 1, y + e, z + e)
    elif eje == "y":
        interior = caja(l - 2 * e, w + 2, h - 2 * e, x + e, y - 1, z + e)
    else:
        interior = caja(l - 2 * e, w - 2 * e, h + 2, x + e, y + e, z - 1)
    return exterior.cut(interior)


def cilindro(d, h, x, y, z, eje=V(0, 0, 1)):
    return Part.makeCylinder(d / 2, h, V(x, y, z), eje)


def centro_x(shape):
    return sum(s.Volume * s.CenterOfMass.x for s in shape.Solids) / shape.Volume


def inclinado(x1, z1, x2, z2, b, e):
    largo = math.hypot(x2 - x1, z2 - z1)
    ang = math.degrees(math.atan2(z2 - z1, x2 - x1))
    s = hueco(largo + 2 * b, b, b, e, -b, -b / 2, -b / 2, "x")
    s.rotate(V(0, 0, 0), V(0, 1, 0), -ang)
    s.translate(V(x1, 0, z1))
    bb = s.BoundBox
    s = s.cut(caja(bb.XLength + 2, b + 2, z1 - bb.ZMin + 1,
                  bb.XMin - 1, -b / 2 - 1, bb.ZMin - 1))
    bb = s.BoundBox
    return s.cut(caja(bb.XMax - x2 + 1, b + 2, bb.ZLength + 2,
                      x2, -b / 2 - 1, bb.ZMin - 1))


def arandela(d, agujero, e, x, y, z):
    return cilindro(d, e, x, y, z).cut(cilindro(agujero, e + 2, x, y, z - 1))


def tuerca(af, agujero, h, x, y, z):
    r = af / math.sqrt(3)
    pts = [V(x + r * math.cos(i * math.pi / 3), y + r * math.sin(i * math.pi / 3), z)
           for i in range(7)]
    return Part.Face(Part.makePolygon(pts)).extrude(V(0, 0, h)).cut(
        cilindro(agujero, h + 2, x, y, z - 1))


doc = App.newDocument("Monoposte")
meta = doc.addObject("App::FeaturePython", "Revision")
meta.addProperty("App::PropertyString", "Codigo").Codigo = REVISION
meta.addProperty("App::PropertyString", "Estado").Estado = "Propuesta; cálculo estructural local pendiente"
masas, centros = {}, []
ACERO, ALU = (0.32, 0.35, 0.40), (0.76, 0.79, 0.82)
HORMIGON = (0.62, 0.60, 0.56)
COLORES = {"acero": ACERO, "aluminio": ALU, "hormigon": HORMIGON,
           "EPDM": (0.08, 0.09, 0.10), "aislante": (0.8, 0.75, 0.5)}


def grupo(nombre):
    g = doc.addObject("App::DocumentObjectGroup", nombre.replace(" ", "_"))
    g.Label = nombre
    return g


def pieza(g, nombre, shape, material=None, color=None, masa_fija=None, transp=0,
          embebida=False, referencia=False):
    if LADO_MASTIL > 0:
        shape = shape.mirror(V(0, 0, 0), V(1, 0, 0))
    obj = doc.addObject("Part::Feature", nombre.replace(" ", "_"))
    obj.Label, obj.Shape = nombre, shape
    g.addObject(obj)
    kg = shape.Volume * DENS.get(material, 0) + (masa_fija or 0)
    obj.addProperty("App::PropertyString", "Material").Material = material or "componentes"
    obj.addProperty("App::PropertyFloat", "Masa_kg").Masa_kg = kg
    obj.addProperty("App::PropertyBool", "Embebida").Embebida = embebida
    obj.addProperty("App::PropertyBool", "Referencia").Referencia = referencia
    masas[(g.Label, material or "componentes")] = masas.get((g.Label, material or "componentes"), 0) + kg
    if kg:
        centros.append((g.Label, kg, centro_x(shape)))
    if App.GuiUp:
        obj.ViewObject.ShapeColor = color or COLORES.get(material, ACERO)
        obj.ViewObject.Transparency = transp
    return obj


# Fundación: dimensiones provisionales; pernos con placas de anclaje explícitas.
g = grupo("Fundación")
acometida = Part.Wire([
    Part.makeLine(V(0, 0, 1), V(0, 0, -350)),
    Part.Arc(V(0, 0, -350), V(0, -29.2893218813, -420.710678119), V(0, -100, -450)).toShape(),
    Part.makeLine(V(0, -100, -450), V(0, -ZAPATA_A / 2 - 1, -450)),
])
reserva_conducto = acometida.makePipeShell([Part.Wire([Part.makeCircle(25, V(0, 0, 1))])], True, False)
pieza(g, "Zapata 1,60 × 1,60 × 0,60 — propuesta",
      caja(ZAPATA_A, ZAPATA_A, ZAPATA_T, -ZAPATA_A / 2, -ZAPATA_A / 2, -ZAPATA_T).cut(reserva_conducto), "hormigon")
grout = caja(390, 390, GROUT_E, -195, -195, 0)
grout = grout.cut(cilindro(PASO_CABLE_D, GROUT_E + 2, 0, 0, -1))
pieza(g, "Grout 30 mm con paso central", grout, "hormigon")
for i, (sx, sy) in enumerate(((1, 1), (-1, 1), (-1, -1), (1, -1)), 1):
    x, y = sx * PERNO_PATRON / 2, sy * PERNO_PATRON / 2
    pieza(g, f"Perno M20 #{i} — rosca simplificada", cilindro(PERNO_D, PERNO_EMBEBIDO + POSTE_Z0 + PERNO_SOBRESALE,
          x, y, -PERNO_EMBEBIDO), "acero", embebida=True)
    ancla = caja(80, 80, 10, x - 40, y - 40, -PERNO_EMBEBIDO).cut(
        cilindro(PERNO_D, 12, x, y, -PERNO_EMBEBIDO - 1))
    pieza(g, f"Placa de anclaje 80 × 80 × 10 #{i} — dimensionar", ancla, "acero", embebida=True)
    pieza(g, f"Tuerca nivelación M20 #{i}", tuerca(30, 20, 16, x, y, PLACA_Z0 - 19), "acero", embebida=True)
    pieza(g, f"Arandela inferior M20 #{i}", arandela(37, 20, 3, x, y, PLACA_Z0 - 3), "acero", embebida=True)
    pieza(g, f"Arandela superior M20 #{i}", arandela(37, 20, 3, x, y, POSTE_Z0), "acero")
    pieza(g, f"Tuerca superior M20 #{i}", tuerca(30, 20, 16, x, y, POSTE_Z0 + 3), "acero")
pieza(g, "Jabalina Ø16 × 1500 — exterior a la zapata",
      cilindro(JABALINA_D, JABALINA_L, ZAPATA_A / 2 + 200, 0, -JABALINA_L), "acero", (0.72, 0.45, 0.20))
piso = caja(4000, 3000, 10, -1200, -1500, -10).cut(
    caja(ZAPATA_A, ZAPATA_A, 30, -ZAPATA_A / 2, -ZAPATA_A / 2, -20))
pieza(g, "Nivel de piso (referencia)", piso, color=(0.55, 0.62, 0.45), transp=75, referencia=True)

g = grupo("Mástil")
placa = caja(PLACA_B, PLACA_B, PLACA_E, -PLACA_B / 2, -PLACA_B / 2, PLACA_Z0)
for sx, sy in ((1, 1), (-1, 1), (-1, -1), (1, -1)):
    placa = placa.cut(cilindro(22, PLACA_E + 2, sx * 140, sy * 140, PLACA_Z0 - 1))
placa = placa.cut(cilindro(PASO_CABLE_D, PLACA_E + 2, 0, 0, PLACA_Z0 - 1))
pieza(g, "Placa base 350 × 350 × 16 con paso Ø32", placa, "acero")
pieza(g, f"Mástil {POSTE_B:g} × {POSTE_B:g} × {POSTE_E:g} SIN registro lateral".replace(".", ","),
      hueco(POSTE_B, POSTE_B, POSTE_Z1 - POSTE_Z0, POSTE_E,
            -POSTE_B / 2, -POSTE_B / 2, POSTE_Z0, "z"), "acero")
tri = [V(-5, -60, POSTE_Z0), V(-5, -160, POSTE_Z0),
       V(-5, -60, POSTE_Z0 + 100), V(-5, -60, POSTE_Z0)]
cartela = Part.Face(Part.makePolygon(tri)).extrude(V(10, 0, 0))
for i, ang in enumerate((0, 90, 180, 270), 1):
    s = cartela.copy()
    s.rotate(V(0, 0, 0), V(0, 0, 1), ang)
    pieza(g, f"Cartela base #{i}", s, "acero")


def brida(z):
    s = caja(BRIDA_L, BRIDA_W, BRIDA_E, -BRIDA_L / 2, -BRIDA_W / 2, z)
    for x, y in BRIDA_PUNTOS:
        s = s.cut(cilindro(BRIDA_AGUJERO, BRIDA_E + 2, x, y, z - 1))
    return s.cut(cilindro(PASO_CABLE_D, BRIDA_E + 2, 0, 0, z - 1))


pieza(g, "Brida inferior 280 × 220 × 12 — cálculo pendiente", brida(POSTE_Z1), "acero")
g = grupo("Brazo y unión desmontable")
pieza(g, "Brida superior 280 × 220 × 12 — cálculo pendiente", brida(POSTE_Z1 + BRIDA_E), "acero")
brazo = inclinado(0, BRIDA_Z1, BORDE_X0, GAB_ZC, BRAZO_B, BRAZO_E)
pieza(g, f"Brazo {BRAZO_B:g} × {BRAZO_B:g} × {BRAZO_E:g} — mitrado".replace(".", ","), brazo, "acero")
for i, (x, y) in enumerate(BRIDA_PUNTOS, 1):
    pieza(g, f"Tornillo brida M12 8.8 #{i} — vástago", cilindro(12, 45, x, y, POSTE_Z1 - 3), "acero")
    pieza(g, f"Cabeza brida M12 #{i}", cilindro(20, 8, x, y, POSTE_Z1 - 11), "acero")
    pieza(g, f"Arandela brida inferior #{i}", arandela(24, 12, 3, x, y, POSTE_Z1 - 3), "acero")
    pieza(g, f"Arandela brida superior #{i}", arandela(24, 12, 3, x, y, BRIDA_Z1), "acero")
    pieza(g, f"Tuerca brida M12 #{i}", tuerca(19, 12, 10, x, y, BRIDA_Z1 + 3), "acero")

g = grupo("Cartel — gabinete LED")
for f in range(MOD_FILAS):
    for c in range(MOD_COLS):
        pieza(g, f"Módulo P5 f{f + 1} c{c + 1}",
              caja(MOD_W, MOD_D, MOD_H, MOD_X0 + c * MOD_W, MOD_Y0, MOD_Z0 + f * MOD_H),
              color=(0.10, 0.11, 0.13) if (f + c) % 2 == 0 else (0.16, 0.17, 0.19), masa_fija=MASA_MODULO)

# Marco con retorno próximo al módulo: asiento EPDM a 4,2 mm, sin tapar LED.
ala = caja(GAB_W, MARCO_E, GAB_H, GAB_X0, GAB_FRENTE, GAB_Z0).cut(
    caja(1280 + 2 * MARCO_HOLGURA, MARCO_E + 2, 640 + 2 * MARCO_HOLGURA,
         MOD_X0 - MARCO_HOLGURA, GAB_FRENTE - 1, MOD_Z0 - MARCO_HOLGURA))
retorno = hueco(1280 + 2 * (JUNTA_E + MARCO_E), 15, 640 + 2 * (JUNTA_E + MARCO_E), MARCO_E,
                MOD_X0 - JUNTA_E - MARCO_E, MOD_Y0, MOD_Z0 - JUNTA_E - MARCO_E, "y")
pieza(g, "Marco frontal con retorno de asiento EPDM", ala.fuse(retorno), "aluminio")
pieza(g, "Junta frontal EPDM — envolvente comprimida 4,2 mm",
      hueco(1280 + 2 * JUNTA_E, 6, 640 + 2 * JUNTA_E, JUNTA_E,
            MOD_X0 - JUNTA_E, MOD_Y0 + 2, MOD_Z0 - JUNTA_E, "y"), "EPDM")

# Perfiles a tope, sin tubos interpenetrados. La piel queda fuera del bastidor.
steel_z0, steel_z1 = GAB_Z0 + 12, GAB_Z1 - CHAPA_E
bast = hueco(BORDE_W, BORDE_B, steel_z1 - steel_z0, BORDE_E,
             BORDE_X0, -BORDE_B / 2, steel_z0, "z")
paso_borde = cilindro(PASO_CABLE_D, BORDE_W + 2, BORDE_X0 - 1, 0, GAB_ZC, V(1, 0, 0))
bast = bast.cut(paso_borde)
inicio = BORDE_X0 + BORDE_W
largo = GAB_X0 + GAB_W - CHAPA_E - inicio
for z in (steel_z0, steel_z1 - PERIM_H):
    bast = bast.fuse(hueco(largo, PERIM_B, PERIM_H, PERIM_E, inicio, BAST_Y0, z, "x"))
for x, w, d, e in ((GAB_X0 + GAB_W - CHAPA_E - PERIM_H, PERIM_H, PERIM_B, PERIM_E),
                    (GAB_XC - CENTRAL_B / 2, CENTRAL_B, CENTRAL_B, CENTRAL_E)):
    bast = bast.fuse(hueco(w, d, steel_z1 - steel_z0 - 2 * PERIM_H, e,
                          x, BAST_Y0, steel_z0 + PERIM_H, "z"))
pieza(g, "Bastidor de acero a tope con pasos Ø32", bast, "acero")
for f in range(MOD_FILAS + 1):
    z = MOD_Z0 + f * MOD_H
    pieza(g, f"Riel tubular Al 30 × 20 × 2 #{f + 1}",
          hueco(1280, RIEL_B, RIEL_H, RIEL_E, MOD_X0, MOD_Y1, z - RIEL_H / 2, "x"), "aluminio")
    for j, (x, w, yfin) in enumerate(((GAB_X0 + 52, 20, -BORDE_B / 2),
                                     (GAB_XC - 10, 20, BAST_Y0),
                                     (MOD_X0 + 1270, 10, BAST_Y0)), 1):
        pieza(g, f"Apoyo aislante riel {f + 1}.{j} — fijación por definir",
              caja(w, yfin - (MOD_Y1 + RIEL_B), 10, x, MOD_Y1 + RIEL_B, z - 5), "aislante")

# Bandeja extraíble: fuentes dentro del volumen libre, sin atravesar el montante.
bandeja_x = BORDE_X0 + BORDE_W + 15
bandeja_y, bandeja_z = 0.0, GAB_Z0 + PERIM_H + FUENTE_SEP - 2
pieza(g, "Bandeja de fuentes desmontable 2 mm",
      caja(GAB_X0 + GAB_W - 30 - bandeja_x, 65, 2, bandeja_x, bandeja_y, bandeja_z), "aluminio")
for i, x in enumerate((bandeja_x + 5, bandeja_x + 285, bandeja_x + 565, bandeja_x + 845), 1):
    pieza(g, f"LRS-350-5 #{i}", caja(FUENTE_L, FUENTE_A, FUENTE_H, x, 8, bandeja_z + 2), masa_fija=MASA_FUENTE)
for i, x in enumerate((bandeja_x + 20, GAB_XC - 230, GAB_XC + 110, GAB_X0 + GAB_W - 120), 1):
    z = steel_z0 + PERIM_H
    esc = caja(20, 50, 2, x, -30, z)
    esc = esc.fuse(caja(20, 2, bandeja_z - z - 2, x, 18, z + 2))
    esc = esc.fuse(caja(20, 18, 2, x, 0, bandeja_z - 2))
    pieza(g, f"Escuadra soporte bandeja #{i} — sobre travesaño inferior", esc, "aluminio")

# Carcasa lateral y techo, con ventana de paso para el brazo (holgura 3 mm).
piel = caja(CHAPA_E, GAB_D - MARCO_E - PUERTA_E, GAB_H, GAB_X0, MOD_Y0, GAB_Z0)
piel = piel.fuse(caja(CHAPA_E, GAB_D - MARCO_E - PUERTA_E, GAB_H,
                     GAB_X0 + GAB_W - CHAPA_E, MOD_Y0, GAB_Z0))
piel = piel.fuse(caja(GAB_W - 2 * CHAPA_E, GAB_D - MARCO_E - PUERTA_E, CHAPA_E,
                     GAB_X0 + CHAPA_E, MOD_Y0, GAB_Z1 - CHAPA_E))
alto_brazo = BRAZO_B / math.cos(math.radians(BRAZO_ANGULO))
piel = piel.cut(caja(CHAPA_E + 2, BRAZO_B + 6, alto_brazo + 8,
                    GAB_X0 - 1, -BRAZO_B / 2 - 3, GAB_ZC - alto_brazo / 2 - 4))
pieza(g, "Carcasa aluminio 2 mm — laterales y techo", piel, "aluminio")

# Fondo inclinado 2° hacia el frente, con dos drenajes reales Ø8.
y0, y1 = MOD_Y0, GAB_Y1 - PUERTA_E
dz = (y1 - y0) * math.tan(math.radians(2))
pts = [V(GAB_X0 + 2, y0, GAB_Z0), V(GAB_X0 + 2, y1, GAB_Z0 + dz),
       V(GAB_X0 + 2, y1, GAB_Z0 + dz + 2), V(GAB_X0 + 2, y0, GAB_Z0 + 2), V(GAB_X0 + 2, y0, GAB_Z0)]
fondo = Part.Face(Part.makePolygon(pts)).extrude(V(GAB_W - 4, 0, 0))
for x in (GAB_X0 + 20, GAB_X0 + GAB_W - 20):
    fondo = fondo.cut(cilindro(8, 20, x, MOD_Y0 + 12, GAB_Z0 - 1))
pieza(g, "Fondo 2° con dos drenajes Ø8", fondo, "aluminio")

# Marco posterior en el plano real de puertas; travesaño central y juntas.
rear_y = GAB_Y1 - 22
rear = hueco(GAB_W - 4, 16, GAB_H - 14, 20, GAB_X0 + 2, rear_y, GAB_Z0 + 12, "y")
rear = rear.fuse(caja(24, 16, GAB_H - 54, GAB_XC - 12, rear_y, GAB_Z0 + 32))
pieza(g, "Marco posterior y batiente central", rear, "aluminio")
PUERTAS = []
for i, xx in enumerate((GAB_X0 + 8, GAB_XC + 3), 1):
    ancho, alto = GAB_W / 2 - 11, GAB_H - 26
    zz = GAB_Z0 + 18
    seal = hueco(ancho, 4, alto, 8, xx, GAB_Y1 - 6, zz, "y")
    pieza(g, f"Junta EPDM puerta #{i}", seal, "EPDM")
    door = caja(ancho, PUERTA_E, alto, xx, GAB_Y1 - PUERTA_E, zz)
    rigid = hueco(ancho - 32, 10, alto - 32, 2, xx + 16, GAB_Y1 - 12, zz + 16, "y")
    door = door.fuse(rigid)
    fan_x, fan_z = xx + ancho / 2, GAB_Z1 - 100
    door = door.cut(cilindro(114, 40, fan_x, GAB_Y1 - 30, fan_z, V(0, 1, 0)))
    door = door.cut(caja(300, 40, 35, fan_x - 150, GAB_Y1 - 30, GAB_Z0 + 50))
    # Bisagra piano esquemática: nudillos alternados, pasador y hojas unidos
    # a cada cuerpo. La selección comercial y los agujeros quedan pendientes.
    hx, hy, hz = GAB_X0 + 5, GAB_Y1 + 2, GAB_Z0 + 50
    fijos, moviles = [], []
    for n in range(12):
        z = hz + n * 50
        nudillo = cilindro(6, 49, hx, hy, z).cut(cilindro(3.2, 51, hx, hy, z - 1))
        hoja = caja(20, 2, 49, hx, GAB_Y1, z) if n % 2 else caja(3, 6, 49, hx - 3, GAB_Y1 - 6, z)
        (moviles if n % 2 else fijos).append(nudillo.fuse(hoja).cut(cilindro(3.2, 51, hx, hy, z - 1)))
    pin = cilindro(3, 600, hx, hy, hz)
    fijo = Part.makeCompound(fijos)
    movil = Part.makeCompound(moviles)
    if i == 2:
        fijo = fijo.mirror(V(GAB_XC, 0, 0), V(1, 0, 0))
        movil = movil.mirror(V(GAB_XC, 0, 0), V(1, 0, 0))
        pin = pin.mirror(V(GAB_XC, 0, 0), V(1, 0, 0))
    door = door.fuse(movil)
    pieza(g, f"Bisagra fija puerta #{i} — geometría de referencia comercial", fijo, "aluminio")
    pieza(g, f"Pasador bisagra puerta #{i}", pin, "acero")
    obj = pieza(g, f"Puerta trasera #{i} con refuerzo y ventilación", door, "aluminio")
    eje_x = GAB_X0 + 5 if i == 1 else GAB_X0 + GAB_W - 5
    PUERTAS.append((obj, eje_x, GAB_Y1 + 2, 1 if i == 1 else -1))
    # Envolvente del ventilador: hueco central preserva el paso de aire.
    fan = caja(120, 25, 120, fan_x - 60, GAB_Y1 - 27, fan_z - 60).cut(
        cilindro(114, 27, fan_x, GAB_Y1 - 28, fan_z, V(0, 1, 0)))
    pieza(g, f"Ventilador 120 mm #{i} — envolvente, seleccionar curva", fan, masa_fija=0.18)
    pieza(g, f"Filtro de entrada #{i} — envolvente porosa",
          caja(300, 10, 35, fan_x - 150, GAB_Y1 - 12, GAB_Z0 + 50), masa_fija=0.10)
    # Capotas externas de descarga/entrada hacia abajo; vuelo máximo 60 mm.
    for nombre, w, h, d, z in (("salida", 128, 128, 60, fan_z - 64),
                              ("entrada", 308, 47, 40, GAB_Z0 + 46)):
        x = fan_x - w / 2
        cap = caja(w, d, 2, x, GAB_Y1, z + h - 2)
        cap = cap.fuse(caja(2, d, h - 2, x, GAB_Y1, z))
        cap = cap.fuse(caja(2, d, h - 2, x + w - 2, GAB_Y1, z))
        cap = cap.fuse(caja(w - 4, 2, h - 2, x + 2, GAB_Y1 + d - 2, z))
        pieza(g, f"Capota {nombre} puerta #{i} — abierta abajo", cap, "aluminio")

doc.recompute()

# Validación anterior excluía choques internos: ahora se comprueba cada pareja.
base = os.path.dirname(os.path.abspath(__file__))
if base not in sys.path:
    sys.path.insert(0, base)
from verificar_modelo import verificar, hash_fuentes

meta.addProperty("App::PropertyString", "FuenteSHA256").FuenteSHA256 = hash_fuentes()
meta.addProperty("App::PropertyInteger", "LadoMastil").LadoMastil = LADO_MASTIL
VALIDACION = verificar(doc, PUERTAS, LADO_MASTIL)
por_grupo = {}
for (grp, mat), kg in masas.items():
    por_grupo[grp] = por_grupo.get(grp, 0) + kg
cartel = por_grupo["Cartel — gabinete LED"]
cab = [(kg, x) for grp, kg, x in centros if grp == "Cartel — gabinete LED"]
xcg = sum(kg * x for kg, x in cab) / cartel
print(f"\n=== {REVISION} ===")
for grp, kg in por_grupo.items():
    print(f"  {grp}: {kg:.2f} kg")
print(f"  Centro de masa del gabinete: {abs(xcg) / 1000:.3f} m del mástil")
print(f"  Reserva adicional de equipamiento: {RESERVA_EQUIPAMIENTO_KG:.1f} kg")
print(f"  Interferencias inesperadas: {len(VALIDACION['interferencias'])}")
print(f"  Errores de validación: {VALIDACION['errores']}")
if VALIDACION["errores"]:
    raise RuntimeError("Modelo no exportado: " + "; ".join(VALIDACION["errores"]))

GENERAR_SALIDA = globals().get("GENERAR_SALIDA", True)
out = os.path.join(base, "build")
if GENERAR_SALIDA:
    import json
    import Import
    os.makedirs(out, exist_ok=True)
    doc.saveAs(os.path.join(out, "monoposte.FCStd"))
    Import.export([o for o in doc.Objects if o.TypeId == "Part::Feature" and not o.Referencia],
                  os.path.join(out, "monoposte.step"))
    with open(os.path.join(out, "verificacion_modelo.json"), "w", encoding="utf-8") as f:
        json.dump(VALIDACION, f, ensure_ascii=False, indent=2)
    print("Archivos en", out)
