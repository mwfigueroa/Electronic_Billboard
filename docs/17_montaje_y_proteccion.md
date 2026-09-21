# 17 — Gabinete LED · revisión constructiva R2

> **Anteproyecto.** R2 sustituye la configuración mecánica anterior de 160 mm de
> fondo para el cartel en voladizo. La fabricación sigue condicionada a muestra,
> detalles de fijación, cálculo de soporte y pruebas. No se declara un grado IP
> ni una temperatura final a partir del modelo CAD.

Soporte: [`18_monoposte.md`](18_monoposte.md). Geometría:
[`hardware/cad/monoposte.py`](../hardware/cad/monoposte.py). La ficha regenerable (`hardware/cad/build/especificaciones_cartel.{md,html,pdf}`,
se genera localmente con `especificaciones.py`; `build/` no está en git) incluye
vistas y observaciones importantes.

## 1. Dimensiones y arquitectura

| Elemento | R2 |
|---|---|
| Matriz | 4 × 4 módulos 320 × 160: 1.280 × 640 mm, 256 × 128 píxeles |
| Cuerpo | 1.340 × 700 × 230 mm |
| Envolvente con capotas | 1.340 × 700 × 290 mm |
| Borde frontal | 30 mm nominales por lado; abertura con 1 mm de holgura |
| Módulo | 20 mm y 1,2 kg supuestos; medir muestra |
| Cara | El propio módulo; sin vidrio y sin solapa sobre píxeles |

Secuencia en profundidad, coordenada Y del modelo:

1. Marco frontal de aluminio de Y=−120 a −117 mm.
2. Módulo de Y=−117 a −97 mm.
3. Riel tubular de Y=−97 a −67 mm.
4. Separadores y bastidor: perímetro desde Y=−65; montante de borde desde Y=−60.
5. Bandeja de fuentes y volumen de servicio.
6. Marco posterior, juntas y puertas; chapa exterior en Y=110 mm.
7. Capotas exteriores hasta Y=170 mm.

El fondo de 160 mm se abandona porque confundía los planos de rieles y tubos,
permitía interferencias y no resolvía el apoyo de las puertas.

## 2. Bastidor y rieles

El gabinete cuelga de un borde; el bastidor es acero, no el marco de aluminio
propuesto inicialmente para una instalación a fachada:

- Montante receptor del brazo: 120 × 100 × 4.
- Cordones superior/inferior y lateral opuesto: 60 × 40 × 3.
- Montante central: 40 × 40 × 2.
- Perfiles modelados a tope, sin atravesarse.
- Cinco rieles de aluminio **tubulares 30 × 20 × 2**, longitud 1.280 mm.
- Masa geométrica de los cinco rieles: **3,18 kg**; el modelo anterior los
  representaba macizos y contaba 10,37 kg.

Los apoyos aislantes están representados, pero **no son fijaciones**. Definir los
tornillos, escuadras y ranuras con el patrón del módulo. No se han inventado
agujeros de montaje sin disponer de la muestra.

Camino de cargas a validar: módulo → fijaciones → rieles → bastidor de acero →
montante de borde → brazo → brida → mástil → base y anclajes → fundación.

## 3. Marco, juntas y envolvente

El marco frontal incorpora un retorno cercano al flanco del módulo. Se reserva
**4,2 mm** para EPDM Ø6 comprimido 30 %, corrigiendo el hueco de 27 mm anterior.
La junta CAD es una envolvente rectangular comprimida, no el perfil comercial
exacto. Confirmar forma de las esquinas, continuidad y compresión con muestra.

La envolvente incluye:

- Laterales y techo de aluminio de 2 mm.
- Fondo de 2 mm inclinado **2° hacia el frente**.
- Dos drenajes **Ø8**, próximos a las esquinas delanteras.
- Marco posterior y batiente central en el plano de cierre real.
- Dos juntas de puerta y hojas de 2 mm con refuerzo posterior.
- Ventana con holgura alrededor del brazo: **definir sellado flexible del encuentro**.

Faltan detalles de costuras, fijaciones carcasa–bastidor, protección de aberturas,
cierres de compresión y ensayo de agua. No se debe interpretar la ausencia de
interferencias como estanqueidad. Los drenajes no se sellan.

## 4. Puertas y mantenimiento

Las bisagras se representan con nudillos alternados, pasador y hojas; son una
geometría de estudio, no una referencia comercial seleccionada. Seleccionar
materiales, capacidad, tornillos, cierres y cables de retención. La reserva de
masa incluye herrajes pendientes.

Se comprueba cada puerta con su ventilador, filtro y capotas, desde 5° hasta 110°
en pasos de 5°. La ilustración `vista_puertas_abiertas.png` muestra ambas a 100°.
El ensayo automático individual no certifica apertura simultánea, trayectorias
continuas ni encuentros con cables y cierres todavía ausentes.

**La extracción del módulo aún debe probarse.** Los rieles y el montante receptor
del brazo están detrás de los módulos; validar salida de una unidad de esquina
y otra central, acceso de herramienta y conectores con las fuentes instaladas.
Si obliga a desmontar el soporte, revisar servicio frontal o rieles desmontables
antes de fabricar. También validar extracción de la bandeja en presencia del
batiente central.

## 5. Fuentes y bandeja

Cuatro LRS-350-5 están reubicadas dentro del volumen libre, sin intersección con
el montante. Se modela bandeja de aluminio de 2 mm y cuatro apoyos sobre el
travesaño inferior. Los agujeros y fijaciones de las fuentes se definirán según
su plano de fabricante.

Las envolventes son 215 × 30 × 115 mm, masa asignada 0,93 kg por fuente. Verificar
orientación autorizada, ventilación, bornes, aislamiento, separación de CA/CC y
acceso real. El modelo no incluye conectores ni el mazo terminado.

## 6. Ventilación y drenaje

- Entrada filtrada inferior en cada puerta, aberturas 300 × 35 mm.
- Dos envolventes de ventilador 120 × 120 × 25 mm en el dorso superior.
- Capotas superiores con boca hacia abajo, vuelo 60 mm.
- Capotas inferiores de entrada, vuelo 40 mm.
- Alimentación auxiliar 12 V; termostato de referencia alrededor de 35 °C.

Hipótesis térmica inicial: aproximadamente 470 W internos a pico y 180 W en
contenido promedio, según docs/03 y el reparto estimado del calor del módulo.
Objetivo de comparación: ΔT ≤15 K y unos 200 m³/h **entregados**.

Seleccionar ventiladores mediante **curva caudal–presión** con filtro, rejas y
capotas. Una suma de 400 m³/h en aire libre no demuestra 200 m³/h instalados.
Validar pérdida de carga, recirculación, suciedad del filtro y exposición solar.
El CAD representa reservas, no una selección térmica final.

## 7. Materiales, dilatación y PE

- Acero protegido contra corrosión y aluminio anodizado o pintado.
- Aislamiento galvánico acero/aluminio/inox en fijaciones, con materiales adecuados
  al ambiente. Las uniones estructurales se detallan por separado.
- Conductor PE dedicado a bastidor, carcasa, puertas y fuentes; las bisagras y
  separadores no garantizan continuidad eléctrica.
- Holguras y ranuras para diferencias de dilatación. El aluminio de 1.280 mm
  cambia aproximadamente 1,8 mm para ΔT=60 K; el acero y los módulos no acompañan
  exactamente ese movimiento.
- Un punto fijo por módulo y fijaciones restantes con ajuste según su fabricante.
- Coplanaridad objetivo aproximada 0,5 mm entre módulos; verificar con regla y muestra.

## 8. Masas y reservas

Las masas de carcasa, rieles, acero, marco, puertas y herrajes representados se
calculan por volumen. Módulos, fuentes, ventiladores y filtros usan masas
asignadas: confirmar por BOM y pesaje.

La ficha genera la masa actual y añade **5 kg de reserva** para control,
alimentación auxiliar, cables, cierres y soldaduras. No es masa certificada ni
margen estructural. El izaje incluye además brazo y brida superior.

## 9. Datos que faltan para fabricar

- [ ] Muestra P5: agujeros/roscas, dimensiones, espesor, conectores, peso y juntas.
- [ ] Prueba de montaje, coplanaridad y extracción de módulos y bandeja.
- [ ] Fijaciones riel–bastidor, carcasa–bastidor y módulos; ranuras y tolerancias.
- [ ] Cierres, bisagras comerciales, retenes y retención secundaria.
- [ ] Sellado del brazo y costuras, drenajes y prueba de agua; IP documentado.
- [ ] Curvas de ventiladores, filtros, prueba térmica y acceso de limpieza.
- [ ] Cableado real, PE, bornes y pruebas eléctricas.
- [ ] Cálculo de nudos y soporte según docs/18; planos de taller y pesaje.

La antigua lista de corte 40 × 40 de aluminio para fachada queda retirada de
esta configuración. No usarla para el bastidor en voladizo R2.
