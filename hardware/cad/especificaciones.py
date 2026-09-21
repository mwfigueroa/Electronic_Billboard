# -*- coding: utf-8 -*-
"""Genera MD/HTML/PDF R2.1 con mediciones y observaciones trazables.

Ejecutar con bin/python.exe de FreeCAD, DESPUÉS de vistas.py. La generación
de PDF es atómica: un PDF viejo no se acepta como resultado de una ejecución.
"""
import datetime as dt
import hashlib
import html
import json
import math
import os
from pathlib import Path
import re
import subprocess
import sys
import tempfile
import time

import FreeCAD as App

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
base = Path(__file__).resolve().parent
out = base / "build"
ns = {"__file__": str(base / "monoposte.py"), "__name__": "especificaciones", "GENERAR_SALIDA": False}
src = (base / "monoposte.py").read_text(encoding="utf-8")
exec(compile(src, str(base / "monoposte.py"), "exec"), ns)
P, doc = ns, ns["doc"]
validacion = ns["VALIDACION"]
objetos = [o for o in doc.Objects if o.TypeId == "Part::Feature" and not o.Referencia]
# No mezclar imágenes o FCStd antiguos con cálculos nuevos.
manifest = json.loads((out / "vistas_manifest.json").read_text(encoding="utf-8"))
assert manifest["fuente_sha256"] == validacion["fuente_sha256"], "Regenerar vistas.py: geometría desactualizada"
assert manifest["lado_mastil"] == P["LADO_MASTIL"], "Lado de las vistas distinto al modelo"
for archivo, digest in manifest["imagenes"].items():
    assert hashlib.sha256((out / archivo).read_bytes()).hexdigest() == digest, "Imagen modificada: " + archivo
guardado = App.openDocument(str(out / "monoposte.FCStd"))
assert guardado.getObject("Revision").FuenteSHA256 == validacion["fuente_sha256"], "FCStd desactualizado"
assert guardado.getObject("Revision").LadoMastil == P["LADO_MASTIL"]
App.closeDocument(guardado.Name)
comparacion = None
ruta_comparacion = out / "verificacion_cambio_soporte.json"
if ruta_comparacion.is_file():
    candidato = json.loads(ruta_comparacion.read_text(encoding="utf-8"))
    if candidato["geometria_sha256"] == validacion["fuente_sha256"]:
        comparacion = candidato


def bbox(prefijos):
    seleccion = [o for o in objetos if o.Label.startswith(prefijos)]
    b = seleccion[0].Shape.BoundBox
    for o in seleccion[1:]:
        b = b.united(o.Shape.BoundBox)
    return b


def num(v, dec=1):
    return f"{v:,.{dec}f}".replace(",", "@").replace(".", ",").replace("@", ".")


def tabla(encabezados, filas):
    return ["| " + " | ".join(encabezados) + " |", "| " + " | ".join("---" for _ in encabezados) + " |"] + [
        "| " + " | ".join(str(c) for c in fila) + " |" for fila in filas] + [""]


matriz = bbox("Módulo P5")
gabinete = doc.getObjectsByLabel("Cartel — gabinete LED")[0]
envolvente = gabinete.Group[0].Shape.BoundBox
for o in gabinete.Group[1:]:
    envolvente = envolvente.united(o.Shape.BoundBox)
masa_gab = P["por_grupo"][gabinete.Label]
masa_mastil = P["por_grupo"]["Mástil"]
masa_brazo = P["por_grupo"]["Brazo y unión desmontable"]
reserva = P["RESERVA_EQUIPAMIENTO_KG"]
masa_izaje = masa_gab + masa_brazo + reserva

# Demandas orientativas, no resistencias ni factores de seguridad certificados.
# Hipótesis explícitas: viento uniforme normal a la cara, sin coeficientes de
# exposición, ráfaga, topografía ni combinaciones reglamentarias.
rho, v, cf, cd, E, G = 1.25, 45.0, 1.3, 2.0, 200e9, 77e9
q = rho * v * v / 2
F = q * cf * P["GAB_W"] * P["GAB_H"] / 1e6
zt, z0 = P["POSTE_Z1"] / 1000, P["POSTE_Z0"] / 1000
zc, xc = P["GAB_ZC"] / 1000, abs(P["GAB_XC"]) / 1000
la = math.hypot(P["BORDE_X0"], P["BRAZO_RISE"]) / 1000
Fa = q * cd * P["BRAZO_B"] / 1000 * la
Fp = q * cd * P["POSTE_B"] / 1000 * (zt - z0)
za = (P["BRIDA_Z1"] + P["GAB_ZC"]) / 2000
xa = P["BORDE_X0"] / 2000
Viento = F + Fa + Fp
Mx = F * zc + Fp * (zt + z0) / 2 + Fa * za
T = F * xc + Fa * xa
My = abs(sum(kg * 9.81 * x / 1000 for grp, kg, x in P["centros"] if grp != "Fundación")) + reserva * 9.81 * xc
N = (masa_gab + masa_mastil + masa_brazo + reserva) * 9.81
B, t = P["POSTE_B"] / 1000, P["POSTE_E"] / 1000
A = B**2 - (B - 2 * t)**2
I = (B**4 - (B - 2 * t)**4) / 12
W = I / (B / 2)
Am = (B - t)**2
tau = T / (2 * Am * t)
sigma = (abs(Mx) + abs(My)) / W + N / A
vm = math.sqrt(sigma**2 + 3 * tau**2)
zapata = next(o for o in objetos if o.Label.startswith("Zapata"))
fundacion_peso = sum(o.Masa_kg for o in doc.getObjectsByLabel("Fundación")[0].Group
                    if hasattr(o, "Masa_kg") and not o.Label.startswith("Jabalina")) * 9.81
N_suelo = fundacion_peso + N
a = P["ZAPATA_A"] / 1000
M_suelo = abs(Mx) + Viento * P["ZAPATA_T"] / 1000
indice_nucleo = (M_suelo + abs(My)) / (N_suelo * a)
pmed = N_suelo / a**2
delta_p = 6 * (M_suelo + abs(My)) / a**3
pmin, pmax = pmed - delta_p, pmed + delta_p
if pmin < 0:
    presiones = "La hipótesis de apoyo completo NO es válida: recalcular contacto parcial."
else:
    presiones = f"{num(pmin / 1000)} / {num(pmax / 1000)} kPa; apoyo completo idealizado"

fecha = dt.datetime.now().astimezone().isoformat(timespec="seconds")
sha = hashlib.sha256(src.encode("utf-8")).hexdigest()
L = ["# Cartel LED · revisión R2.1", "",
     "**Mástil con brazo lateral · anteproyecto para revisión técnica**", "",
     "**Cambio R2.1 aprobado: únicamente tubos del soporte. Mástil 120 × 120 × 6,35 mm y brazo 120 × 120 × 4,75 mm. Gabinete R2 conservado.**", "",
     f"Actualizado: {fecha}. Modelo: `monoposte.py` · SHA-256 `{sha[:16]}`.", "",
     "> Estado: geometría comprobada con las exclusiones indicadas. Las bridas, soldaduras, anclajes y fundación requieren dimensionado y validación estructural. No es un plano liberado para fabricar.", "",
     "![Vista general R2.1](vista_iso.png)", "", "## 1. Resumen de la revisión", ""]
L += tabla(["Parámetro", "Revisión R2.1"], [
    ("Tubos del soporte", f"Mástil {num(P['POSTE_B'],0)} × {num(P['POSTE_B'],0)} × {num(P['POSTE_E'],2)} mm; brazo {num(P['BRAZO_B'],0)} × {num(P['BRAZO_B'],0)} × {num(P['BRAZO_E'],2)} mm"),
    ("Display", f"{num(matriz.XLength, 0)} × {num(matriz.ZLength, 0)} mm · 256 × 128 píxeles · paso 5 mm"),
    ("Cuerpo del gabinete", f"{num(P['GAB_W'], 0)} × {num(P['GAB_H'], 0)} × {num(P['GAB_D'], 0)} mm"),
    ("Envolvente con capotas", f"{num(envolvente.XLength, 0)} × {num(envolvente.ZLength, 0)} × {num(envolvente.YLength, 0)} mm"),
    ("Alturas", f"Gabinete {num(P['GAB_Z0']/1000, 2)}–{num(P['GAB_Z1']/1000, 2)} m · mástil hasta {num(zt, 3)} m"),
    ("Vuelo", f"De {num(P['GAB_X0']/1000, 2)} a {num((P['GAB_X0']+P['GAB_W'])/1000, 2)} m del eje"),
    ("Masa de izaje presupuestada", f"{num(masa_izaje)} kg = gabinete + brazo/brida/herrajes modelados + reserva de {num(reserva)} kg"),
    ("Verificación geométrica", f"{validacion['objetos']} objetos · {len(validacion['interferencias'])} interferencias inesperadas · dos puertas hasta 110° en pasos de 5°"),
])
L += ["## 2. Observaciones importantes", "",
      "Estas observaciones forman parte del diseño y deben acompañar el HTML, PDF y modelo al cotizar.", ""]
L += tabla(["Prioridad", "Observación y acción"], [
    ("Compra del soporte", "Solo mástil y brazo se estandarizan. Confirmar stock, corte, fabricante, norma/grado, tolerancia de espesor y radios reales. Los cálculos CAD usan secciones ideales; no equivalen a propiedades certificadas del proveedor."),
    ("Estructural", "Se elimina el registro lateral 100 × 150 del mástil. El tramo conserva la sección tubular cerrada. No volver a abrirlo sin recalcular. El acceso eléctrico se traslada a una caja externa de acometida, pendiente de ubicación."),
    ("Estructural", "Brida doble 280 × 220 × 12, seis M12 8.8 y soldaduras: geometría preliminar; verificar flexión de placas, efecto palanca, precarga, deslizamiento, fatiga y pared local del montante. No hay capacidad admisible certificada."),
    ("Obra civil", "Zapata y anclajes conservan dimensiones de anteproyecto. Verificar suelo, agua, deslizamiento, torsión, hormigón, armaduras, arrancamiento y recubrimientos. Los valores de presión son demandas orientativas, no capacidad del terreno."),
    ("Altura libre", f"Los {num(P['ALTURA_LIBRE']/1000, 2)} m corresponden solo al gabinete. La brida y el inicio del brazo están más bajos; verificar todo el volumen de paso y la ordenanza del lugar."),
    ("Mantenimiento", "La apertura de puertas se comprueba geométricamente. La extracción de módulos traseros, alcance de herramientas, bornes, cierres y flexibilidad de cables siguen pendientes de muestra/prototipo. Si exige desmontar rieles, revisar servicio frontal o soportes desmontables."),
    ("Intemperie", "Las juntas, drenajes y capotas están representados. Faltan ensayo de agua, sellado del paso brazo–carcasa, selección de filtros, protección de aberturas, grado IP y prueba térmica. Los ventiladores se seleccionan por curva caudal–presión, no por caudal nominal solamente."),
    ("Izaje", f"Usar {num(masa_izaje)} kg como presupuesto actual de masa, no como carga de trabajo de un aparejo. Definir y calcular orejas, eslingado y retención secundaria; sus geometrías aún no están cerradas."),
])
L += ["## 3. Cambios aplicados y trazabilidad", ""]
L += ["**Cambio de esta revisión respecto de R2:** solo espesores de los dos tubos del soporte y resultados derivados. Las correcciones del gabinete que se enumeran después son las ya realizadas en R2.", ""]
if comparacion:
    L += [f"Verificación de conservación: **{comparacion['piezas_gabinete_sin_cambio']} piezas del gabinete idénticas** por diferencia booleana bidireccional menor de 0,001 mm³, con material y masa conservados. Informe: `verificacion_cambio_soporte.json`.", ""]
L += tabla(["Hallazgo anterior", "Cambio aplicado / alcance"], [
    ("R2.1 · tubos comerciales", "Mástil: 5 → 6,35 mm. Brazo: 4 → 4,75 mm. Se mantienen las secciones exteriores 120 × 120 y las posiciones de montaje."),
    ("Registro debilitaba el mástil", "Suprimido. Paso de cable por base y brida; tramo vertical sin recorte lateral."),
    ("Tapa sin unión desmontable definida", "Dos placas, seis agujeros Ø14, tornillos, arandelas y tuercas modelados. Capacidad estructural pendiente."),
    ("Tres interferencias internas", "Separación de planos del marco, rieles y bastidor; fuentes reubicadas y bandeja con cuatro apoyos sobre el travesaño inferior."),
    ("Rieles macizos", f"Cinco tubos Al 30 × 20 × 2: {num(5*1280*(30*20-26*16)*2700e-9, 2)} kg, frente a 10,37 kg anteriores."),
    ("Puertas sin plano de apoyo", "Marco posterior, batiente central, juntas, refuerzos y bisagras piano esquemáticas. Cierres/retenciones aún por seleccionar."),
    ("EPDM separado 27 mm del módulo", "Asiento de retorno junto al módulo, con espacio de 4,2 mm; envolvente de junta comprimida, sin pisar LED."),
    ("Sin envolvente ni drenajes", "Laterales y techo de aluminio, fondo inclinado 2°, dos drenajes Ø8, aberturas de ventilación y capotas abiertas abajo."),
    ("Ruta de cables interrumpida", "Reserva Ø50 con curva R100 en zapata; pasos Ø32 en grout, placa, bridas y ambas paredes del montante. Sondas Ø24 verificadas en las interfaces."),
    ("Chequeo omitía choques internos", "Todas las parejas, incluso dentro del gabinete. Solo se permiten embebidos declarados contra hormigón; no se ignoran pernos contra acero."),
    ("Resultados estructurales fijos en la ficha", "Eliminados 80 MPa/13 mm y factores de seguridad fijos. Demandas recalculadas con parámetros y masas actuales; no se publica una aprobación de resistencia."),
])
L += ["## 4. Geometría constructiva y materiales", "",
      "![Vista frontal R2.1](vista_frente.png)", ""]
L += tabla(["Elemento", "Definición actual"], [
    ("Mástil", f"Acero {num(P['POSTE_B'],0)} × {num(P['POSTE_B'],0)} × {num(P['POSTE_E'],2)} · de {num(P['POSTE_Z0']/1000, 3)} a {num(zt, 3)} m · sin registro lateral"),
    ("Brazo", f"Acero {num(P['BRAZO_B'],0)} × {num(P['BRAZO_B'],0)} × {num(P['BRAZO_E'],2)} · longitud de eje {num(la*1000, 1)} mm · inclinación real {num(P['BRAZO_ANGULO'], 2)}°"),
    ("Brida", "Dos placas 280 × 220 × 12; patrón X = −105, 0, +105; Y = −85, +85 mm; seis Ø14 y paso central Ø32"),
    ("Base", "Placa 350 × 350 × 16, cuatro cartelas 100 × 100 × 10, cuatro M20 en patrón 280 × 280, grout 30 mm"),
    ("Anclajes", "M20 simplificados, 500 mm embebidos; placas de anclaje 80 × 80 × 10 y tuercas de nivelación. Definir unión perno–placa, grado, desarrollo y hormigón."),
    ("Bastidor del gabinete", "Acero: montante 120 × 100 × 4, perímetro 60 × 40 × 3, central 40 × 40 × 2; perfiles a tope"),
    ("Planos de montaje", f"Dorso módulos Y={num(P['MOD_Y1'],0)}; rieles hasta Y={num(P['MOD_Y1']+P['RIEL_B'],0)}; perímetro desde Y={num(P['BAST_Y0'],0)} mm; separadores aislantes"),
    ("Fijaciones de módulos/rieles", "Ubicaciones nominales. Perforaciones, ranuras, tornillos y punto fijo según muestra; aislantes requieren tornillos pasantes, no son fijaciones por sí solos."),
    ("Envolvente", "Aluminio 2 mm; marco frontal con asiento EPDM; fondo 2° hacia el frente con dos drenajes Ø8"),
    ("Puertas", "Dos hojas de 2 mm, refuerzo posterior, juntas comprimidas de 4 mm y bisagras con nudillos alternados; seleccionar cierres y cables de retención"),
    ("Acabados", "Acero galvanizado o sistema anticorrosivo especificado; aluminio anodizado/pintado; aislar pares galvánicos y disponer puentes PE dedicados"),
    ("Jabalina", "Ø16 × 1.500 mm, fuera de la zapata; definir caja de inspección y conexión accesible según instalación eléctrica"),
])
L += ["**Compra de los dos tubos · provincia de Buenos Aires**", ""]
L += tabla(["Pieza", "Pedido para cotización"], [
    ("Mástil", f"1 pieza de tubo {num(P['POSTE_B'],0)} × {num(P['POSTE_B'],0)} × {num(P['POSTE_E'],2)} mm; largo terminado {num(P['POSTE_Z1']-P['POSTE_Z0'],0)} mm; acordar tolerancia de corte"),
    ("Brazo", f"1 tramo bruto de 1.000 mm de tubo {num(P['BRAZO_B'],0)} × {num(P['BRAZO_B'],0)} × {num(P['BRAZO_E'],2)} mm, para realizar los mitrados según plano; 1.000 mm no es su largo terminado"),
    ("Referencias comerciales", "Tubo Center (Los Polvorines, Pilar y Escobar): www.tubocenter.com.ar/cuadrados/ · Metalúrgica Escoda (Villa Ballester): www.mescoda.com.ar/tubos-estructurales/"),
    ("Condiciones a confirmar", "Medidas catalogadas, sin reserva de stock ni precio confirmado. Consultar venta por corte: el 120 × 120 puede ofrecerse en barras de 12 m. Exigir norma/grado y espesor nominal exacto, no redondeado."),
])
L += ["![Interior del gabinete R2 conservado](vista_gabinete_interior.png)", "",
      "![Detalle de la brida R2](vista_detalle_brida.png)", "",
      "## 5. Masas y montaje", ""]
L += tabla(["Conjunto", "Masa"], [
    ("Gabinete modelado", f"{num(masa_gab,2)} kg"),
    ("Mástil, base, cartelas y brida inferior", f"{num(masa_mastil,2)} kg"),
    ("Brazo, brida superior y fijaciones", f"{num(masa_brazo,2)} kg"),
    ("Reserva de equipamiento no representado", f"{num(reserva,1)} kg: cableado, control, auxiliar, cierres y soldaduras; sustituir por BOM/pesaje"),
    ("Conjunto que se iza al mástil", f"{num(masa_izaje,2)} kg, incluyendo reserva"),
    ("Centro de masa del gabinete modelado", f"{num(abs(P['xcg'])/1000,3)} m del eje del mástil"),
    ("Zapata neta, descontando reserva de conducto", f"{num(zapata.Shape.Volume/1e9,3)} m³ · {num(zapata.Masa_kg,0)} kg"),
])
L += ["- Armar y verificar el conjunto en taller; definir puntos de izaje antes de montar.",
      "- Instalar mástil con medios de elevación, nivelar y ejecutar grout según procedimiento de obra.",
      "- Izar gabinete y brazo como conjunto; presentar brida, comprobar nivel y ejecutar apriete especificado por el cálculo.",
      "- Conectar PE, alimentación y controles; verificar drenajes, cierres, ventilación y aislamiento.",
      "- Acceso de mantenimiento: plataforma adecuada a puertas centradas a 2,85 m; validar extracción de un módulo de esquina y uno central.", ""]
L += ["## 6. Demandas mecánicas orientativas, recalculadas", "",
      "> Hipótesis de comparación: aire 1,25 kg/m³, viento uniforme 45 m/s, Cf=1,3 en gabinete y Cd=2 en tubos. No incluye el procedimiento completo CIRSOC, viento oblicuo, dinámica/fatiga, combinaciones reglamentarias ni verificaciones locales. La presión del suelo supone apoyo completo sin levantamiento y ausencia de flotación.", ""]
L += tabla(["Magnitud", "Resultado"], [
    ("Presión dinámica", f"{num(q,0)} Pa"),
    ("Empuje sobre gabinete", f"{num(F,0)} N a {num(zc,2)} m"),
    ("Empuje sobre mástil / brazo", f"{num(Fp,0)} / {num(Fa,0)} N"),
    ("Cortante horizontal total", f"{num(Viento/1000,2)} kN"),
    ("Momento por viento respecto al suelo", f"{num(Mx/1000,2)} kN·m"),
    ("Torsión por gabinete + viento en brazo", f"{num(T/1000,2)} kN·m"),
    ("Momento gravitatorio lateral, con reserva", f"{num(My/1000,2)} kN·m"),
    ("Sección nominal del mástil", f"A={num(A*1e6,0)} mm² · W={num(W*1e6,1)} cm³; esquinas ideales"),
    ("Tensión equivalente nominal orientativa", f"{num(vm/1e6,1)} MPa; sección íntegra idealizada, sin uniones ni factores de utilización"),
    ("Momento de viento al plano inferior de zapata", f"{num(M_suelo/1000,2)} kN·m; incluye traslado de cortante por {num(P['ZAPATA_T']/1000,2)} m"),
    ("Índice de núcleo biaxial", f"{num(indice_nucleo,3)}; límite geométrico 1/6≈0,167 para apoyo completo idealizado"),
    ("Presión mínima / máxima sobre suelo", presiones),
    ("Capacidades y desplazamientos", "PENDIENTES: bridas, soldaduras, pared local, anclajes, placa base, suelo, flecha total y fatiga"),
])
L += ["Fórmulas: q=ρv²/2; F=q·Cf·A; M=ΣF·z; T=ΣF·x; Mg=Σm·g·x; σnom=(|Mx|+|My|)/W+N/A; τ=T/(2·Am·t); σVM=√(σnom²+3τ²). En el suelo: p=N/a² ± 6(|Mx|+|My|)/a³.", "",
      "**No se asigna un factor de seguridad ni una capacidad admisible al conjunto a partir de estos resultados.**", ""]
L += ["## 7. Verificación del modelo y alcance", "",
      "![Dorso R2.1](vista_dorso.png)", "",
      "![Puertas abiertas 100 grados — ilustración de mantenimiento](vista_puertas_abiertas.png)", ""]
L += tabla(["Comprobación", "Resultado / limitación"], [
    ("Sólidos", f"{validacion['objetos']} objetos físicos; validez topológica comprobada"),
    ("Interferencias", f"{len(validacion['interferencias'])} inesperadas; umbral volumétrico 1 mm³"),
    ("Hormigón", f"{len(validacion['embebidos_hormigon'])} encuentros declarados de piezas embebidas; se listan individualmente en verificacion_modelo.json"),
    ("Puertas", "Hoja + bisagra móvil + ventilador + filtro + capotas; 5° a 110° cada 5°. Ensayo discreto, no demostración de todo el barrido continuo."),
    ("Simultaneidad de puertas", "Cada hoja se prueba contra la otra cerrada; apertura simultánea y encuentro con cierres/cables no certificados."),
    ("Paso de cables", "Sondas Ø24 en pasos Ø32: base/grout, brida y montante; faltan accesorios, pasamuros, radios reales y guiado final."),
    ("Mantenimiento", "Extracción de módulos y bandeja pendiente de prototipo; el modelo no sustituye esa prueba."),
    ("Control de exportación", "Si la geometría es inválida, hay choques o un paso está bloqueado, se aborta la exportación."),
])
L += ["## 8. Display, alimentación y ventilación", ""]
L += tabla(["Sistema", "Especificación / fuente"], [
    ("Panel", "16 módulos P5 de 320 × 160 mm, 4 × 4, 256 × 128 px. Espesor supuesto 20 mm, masa supuesta 1,2 kg: confirmar muestra (docs/01, 08, 17)."),
    ("Óptica", ">4.500 nits declarados; verificar a pleno sol, IP y temperatura del fabricante."),
    ("Fuentes", "4 × Mean Well LRS-350-5, 5 V/60 A, una por fila; positivas independientes. Bornes y ventilación según montaje autorizado por fabricante (docs/03)."),
    ("Consumo estimado del display", "246 W promedio / 655 W pico a 5 V; el consumo de red suma pérdidas y auxiliares."),
    ("Distribución", "Dos ramas 12 AWG por fila con fusibles 20 A según docs/03; verificar caída ≤0,2 V, terminales y corriente real."),
    ("Protecciones", "PE dedicado a acero, aluminio, puertas y fuentes; diferencial 30 mA, protección contra sobrecorriente y SPD según proyecto eléctrico local."),
    ("Control", "Producción: Huidu HD-WF4. Alternativa de desarrollo: Colorlight 5A-75B; configuración y driver según docs/11 y docs/14."),
    ("Ventilación", "Dos envolventes 120 × 120 × 25 mm a 12 V y fuente auxiliar separada; filtros inferiores y capotas superiores con boca hacia abajo."),
    ("Objetivo térmico", "≈470 W internos estimados a pico, ΔT objetivo ≤15 K; caudal objetivo 200 m³/h entregados. Seleccionar curva con pérdidas de filtro y capotas y comprobar bajo sol."),
])
L += ["## 9. Pendientes para liberar fabricación", "",
      "- Ubicación, lado del mástil, ordenanza, gálibo completo y viento reglamentario.",
      "- Suelo y cálculo estructural: bridas, nudos soldados, pared local, sección con perforaciones, anclajes, armadura, estabilidad y deformaciones.",
      "- Planos de taller: tolerancias, agujeros, ranuras, símbolos de soldadura, recubrimientos, secuencia de armado y pares de apriete.",
      "- Muestra del módulo: patrón, espesor, peso, conectores, juntas y prueba real de extracción.",
      "- Selección de bisagras y cierres, cables de retención, orejas de izaje y fijaciones carcasa–bastidor/rieles.",
      "- Especificación de caja externa de acometida y caja de inspección de jabalina; pasamuros y sellado de la brida y del brazo.",
      "- Ensayos de agua/drenaje, ventilación con filtro, temperatura y continuidad de PE; pesaje del conjunto terminado.", "",
      "## 10. Vistas y archivos", "", "![Perfil R2.1](vista_perfil.png)", "",
      "Modelo editable: `monoposte.FCStd` · intercambio: `monoposte.step` · auditoría: `verificacion_modelo.json` · mediciones: `medir.py`.", "",
      "Fuentes del proyecto: `docs/01_especificaciones.md`, `docs/03_electrico.md`, `docs/17_montaje_y_proteccion.md`, `docs/18_monoposte.md`. R2.1 actualiza únicamente los tubos del soporte de R2; el gabinete mantiene su definición R2.", ""]

out.mkdir(exist_ok=True)
(out / "especificaciones_cartel.md").write_text("\n".join(L), encoding="utf-8")


def inline(text):
    text = html.escape(text, quote=False)
    text = re.sub(r"\*\*(.+?)\*\*", r"<strong>\1</strong>", text)
    return re.sub(r"`(.+?)`", r"<code>\1</code>", text)


def a_html(lineas):
    result, rows, lista = [], [], False

    def cerrar_tabla():
        if rows:
            result.append("<table><thead><tr>" + "".join("<th>" + inline(c) + "</th>" for c in rows[0]) + "</tr></thead><tbody>")
            result.extend("<tr>" + "".join("<td>" + inline(c) + "</td>" for c in r) + "</tr>" for r in rows[1:])
            result.append("</tbody></table>")
            rows.clear()

    for ln in lineas:
        if ln.startswith("|"):
            cols = [c.strip() for c in ln.strip("|").split("|")]
            if not all(set(c) <= set("-:") for c in cols):
                rows.append(cols)
            continue
        cerrar_tabla()
        if ln.startswith("- "):
            if not lista:
                result.append("<ul>")
                lista = True
            result.append("<li>" + inline(ln[2:]) + "</li>")
            continue
        if lista:
            result.append("</ul>")
            lista = False
        image = re.fullmatch(r"!\[(.*?)\]\((.*?)\)", ln)
        if image:
            if not (out / image[2]).is_file():
                raise FileNotFoundError("Regenerar vistas antes del documento: " + image[2])
            result.append(f'<figure><img src="{html.escape(image[2])}" alt="{html.escape(image[1])}"><figcaption>{inline(image[1])}</figcaption></figure>')
        elif ln.startswith("# "):
            result.append("<h1>" + inline(ln[2:]) + "</h1>")
        elif ln.startswith("## "):
            result.append("<h2>" + inline(ln[3:]) + "</h2>")
        elif ln.startswith("> "):
            result.append("<blockquote>" + inline(ln[2:]) + "</blockquote>")
        elif ln:
            result.append("<p>" + inline(ln) + "</p>")
    cerrar_tabla()
    if lista:
        result.append("</ul>")
    return "\n".join(result)


css = """
@page { size: A4; margin: 14mm 14mm 16mm;
  @bottom-left { content: 'BILLBOARD · R2.1 · Anteproyecto'; font-size: 8pt; color: #627682; }
  @bottom-right { content: counter(page) ' / ' counter(pages); font-size: 8pt; color: #627682; }
}
body { font: 10pt/1.38 'Segoe UI', Arial, sans-serif; color: #24303a; max-width: 185mm; margin: auto; }
h1 { font-size: 24pt; line-height: 1.12; color: #143647; margin: 0 0 8pt; }
h2 { font-size: 14pt; color: #143647; margin: 17pt 0 7pt; border-bottom: 2px solid #388899; padding-bottom: 4pt; break-after: avoid; }
p { margin: 5pt 0; overflow-wrap: anywhere; }
blockquote { margin: 9pt 0; padding: 8pt 10pt; background: #fff7e8; border-left: 4px solid #c58a28; break-inside: avoid; }
table { border-collapse: collapse; width: 100%; margin: 6pt 0 10pt; font-size: 9pt; table-layout: fixed; }
thead { display: table-header-group; }
th { color: white; background: #244f61; text-align: left; padding: 6pt; }
th:first-child,td:first-child { width: 27%; }
td { padding: 5pt 6pt; vertical-align: top; border-bottom: 1px solid #d9e2e6; overflow-wrap: anywhere; }
tr { break-inside: avoid; }
tbody tr:nth-child(even) { background: #f2f6f8; }
figure { margin: 8pt 0; text-align: center; break-inside: avoid; }
figure img { width: 100%; height: 66mm; object-fit: contain; }
figcaption { font-size: 8pt; color: #627682; }
code { font: 8.5pt Consolas, monospace; overflow-wrap: anywhere; }
li { margin: 4pt 0; }
@media screen { body { padding: 24px; background: white; } html { background: #e8eef1; } }
"""
documento = '<!doctype html><html lang="es"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">'
documento += '<title>Cartel LED — revisión R2.1</title><style>' + css + '</style></head><body>' + a_html(L) + '</body></html>'
html_path = out / "especificaciones_cartel.html"
html_path.write_text(documento, encoding="utf-8")
revision = {
    "revision": P["REVISION"], "fecha": fecha, "fuente_sha256": sha,
    "geometria_sha256": validacion["fuente_sha256"],
    "html_sha256": hashlib.sha256(html_path.read_bytes()).hexdigest(),
    "masa_gabinete_kg": masa_gab, "masa_izaje_con_reserva_kg": masa_izaje,
    "tubo_mastil_mm": [P["POSTE_B"], P["POSTE_B"], P["POSTE_E"]],
    "tubo_brazo_mm": [P["BRAZO_B"], P["BRAZO_B"], P["BRAZO_E"]],
    "conservacion_gabinete_verificada": comparacion is not None,
    "momento_viento_suelo_kNm": Mx / 1000, "torsion_kNm": T / 1000,
    "momento_gravedad_kNm": My / 1000, "tension_nominal_MPa": vm / 1e6,
    "presion_min_kPa": pmin / 1000, "presion_max_kPa": pmax / 1000,
    "pdf_estado": "pendiente de regeneración",
}
revision_path = out / "revision_documental.json"
revision_path.write_text(json.dumps(revision, ensure_ascii=False, indent=2), encoding="utf-8")
if "--sin-pdf" in sys.argv:
    print("MD/HTML actualizados. Generar el PDF con render_pdf.py (WeasyPrint).")
    raise SystemExit(0)

# Chrome/Edge genera un archivo NUEVO en un perfil local y se publica al terminar.
navegadores = [Path(r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe"),
               Path(r"C:\Program Files\Microsoft\Edge\Application\msedge.exe"),
               Path(r"C:\Program Files\Google\Chrome\Application\chrome.exe")]
pdf_path = out / "especificaciones_cartel.pdf"
for navegador in navegadores:
    if not navegador.is_file():
        continue
    with tempfile.TemporaryDirectory(prefix="billboard_r2_") as temporal:
        tmp = Path(temporal)
        nuevo = tmp / "especificaciones_cartel.pdf"
        cmd = [str(navegador), "--headless=new", "--disable-gpu", "--no-first-run", "--disable-extensions",
               "--no-pdf-header-footer", "--allow-file-access-from-files", f"--user-data-dir={tmp / 'perfil'}",
               f"--print-to-pdf={nuevo}", html_path.as_uri()]
        try:
            resultado = subprocess.run(cmd, timeout=100, capture_output=True, text=True, errors="replace")
            for _ in range(40):
                if nuevo.is_file() and nuevo.stat().st_size > 1000:
                    break
                time.sleep(0.5)
            if not nuevo.is_file() or not nuevo.read_bytes().startswith(b"%PDF-"):
                raise RuntimeError("El navegador no produjo un PDF nuevo: " + resultado.stderr[-500:])
            staging = out / "especificaciones_cartel.nuevo.pdf"
            staging.write_bytes(nuevo.read_bytes())
            os.replace(staging, pdf_path)
        except (OSError, subprocess.TimeoutExpired, RuntimeError) as exc:
            print("Fallo PDF:", exc)
            continue
    break
else:
    raise RuntimeError("HTML/MD actualizados, pero no se generó PDF nuevo")

revision.update(pdf_estado="actualizado", pdf_bytes=pdf_path.stat().st_size,
                pdf_sha256=hashlib.sha256(pdf_path.read_bytes()).hexdigest(), pdf_motor="navegador")
revision_path.write_text(json.dumps(revision, ensure_ascii=False, indent=2), encoding="utf-8")
print("Documentos actualizados:", html_path, pdf_path)
