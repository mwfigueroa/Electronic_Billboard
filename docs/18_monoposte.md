# 18 — Mástil con brazo lateral · revisión R2.1

**R2.1: estandarización aprobada exclusivamente para los dos tubos del soporte.**
Mástil 120 × 120 × **6,35 mm** y brazo 120 × 120 × **4,75 mm**. El gabinete
mantiene su definición R2; se conservan secciones exteriores, largos y posiciones
del soporte. Se recalculan masas y demandas derivadas.

> **Anteproyecto revisado, no plano liberado para fabricar.** R2 corrige la
> geometría y hace explícitas las verificaciones pendientes. Las capacidades de
> las uniones y de la fundación requieren cálculo con viento, suelo y materiales
> del emplazamiento. Se retiran las anteriores afirmaciones de utilización del
> 50 %, flecha de 13 mm y factores de seguridad fijos.

Fuente de geometría: [`hardware/cad/monoposte.py`](../hardware/cad/monoposte.py).
Ficha regenerable con mediciones, vistas, masas y demandas orientativas, en
`hardware/cad/build/` (no está en git: se genera con `vistas.py` + `especificaciones.py`,
ver README): `especificaciones_cartel.{pdf,html,md}` y `verificacion_modelo.json`.

## 1. Configuración

Se conserva el concepto del croquis `foto/estructura_basica.jpeg`: mástil
vertical y brazo aproximadamente a 45°, con el gabinete volado hacia un lado.
El cartel es el gabinete de 16 módulos P5, sin cara adicional de 2,4 × 1,2 m.

| Elemento | R2.1 |
|---|---|
| Display | 1.280 × 640 mm, 4 × 4 módulos, 256 × 128 píxeles |
| Cuerpo del gabinete | 1.340 × 700 × **230 mm** |
| Envolvente con capotas | 1.340 × 700 × **290 mm** |
| Cotas del gabinete | Z = 2,50–3,20 m; X = 0,50–1,84 m respecto al eje del mástil |
| Mástil | 120 × 120 × 6,35; desde Z=46 hasta Z=2.326 mm; **sin registro lateral** |
| Brazo | 120 × 120 × 4,75; eje desde (0, 0, 2.350) a (502, 0, 2.850) mm |
| Inclinación real | 44,89°; los 2 mm adicionales corresponden al espesor de carcasa |
| Brida desmontable | Dos placas 280 × 220 × 12; seis M12 8.8; paso central Ø32 |
| Base | Placa 350 × 350 × 16; cuatro cartelas 100 × 100 × 10 |
| Anclajes | Cuatro M20, patrón 280 × 280, 500 mm embebidos; placas 80 × 80 × 10 provisionales |
| Fundación | Zapata 1,60 × 1,60 × 0,60 m, por verificar según suelo y cargas |

**Gálibo:** los 2,50 m describen el borde inferior del gabinete, no toda la
estructura. La brida, tornillos y comienzo del brazo están por debajo. Verificar
el volumen completo de paso, proyección sobre vereda y ordenanza local; no se
presume un valor municipal universal.

### Compra del soporte en provincia de Buenos Aires

- **Mástil:** una pieza 120 × 120 × 6,35 mm, largo terminado 2.280 mm.
- **Brazo:** un tramo bruto 120 × 120 × 4,75 mm de 1.000 mm; realizar después
  los mitrados según plano. El metro es material bruto, no la longitud terminada.
- Referencias de catálogo: [Tubo Center](https://www.tubocenter.com.ar/cuadrados/)
  (Los Polvorines, Pilar y Escobar) y
  [Metalúrgica Escoda](https://www.mescoda.com.ar/tubos-estructurales/)
  (Villa Ballester). Stock y precio no reservados; confirmar con cotización.
- Consultar venta por corte, pues el 120 × 120 puede suministrarse en barras
  de 12 m. Pedir fabricante, norma/grado, tolerancia de espesor y radios de esquina.
- No redondear 6,35 o 4,75 a otra medida. Las masas y propiedades del CAD son
  idealizadas y se contrastan con la ficha del material efectivamente suministrado.

## 2. Correcciones estructurales y constructivas

### Mástil íntegro

El registro anterior de 100 × 150 mm eliminaba casi toda una pared del tubo.
En la sección del recorte el módulo resistente frontal bajaba de unos 84,7 a
39,0 cm³, y dejaba de ser aplicable localmente la torsión de sección cerrada.

**R2 elimina el recorte.** El acceso de mantenimiento eléctrico pasa a una caja
externa de acometida, que debe ubicarse en el proyecto eléctrico. No perforar de
nuevo lateralmente el mástil sin revisar sección neta, concentración de tensiones,
torsión y fatiga. Las perforaciones de las placas y del montante de borde también
deben entrar en el cálculo local.

### Brida desmontable

Se modelan ambas placas, los seis agujeros Ø14, vástagos M12, cabezas, arandelas
y tuercas. Coordenadas de taladros respecto al eje: X=−105, 0, +105 mm;
Y=−85, +85 mm. Esto deja acceso geométrico lateral para las fijaciones.

**El patrón es una propuesta constructiva, no un dimensionado aprobado.** Verificar:

- Flexión de placas y efecto palanca sobre los tornillos.
- Grupo de tornillos bajo tracción, cortante y torsión; precarga y deslizamiento.
- Soldaduras mástil–placa, brazo–placa y brazo–montante.
- Comportamiento local de las paredes tubulares, necesidad de rigidizadores y fatiga.
- Acceso de herramienta, protección anticorrosiva y sellado del paso central.

No sustituir la brida por una soldadura improvisada en obra. La secuencia final y
el apriete se fijan una vez calculada la unión.

### Anclaje y fundación

El modelo incorpora placas de anclaje, tuercas de nivelación y arandelas. Las
roscas están simplificadas. Queda pendiente definir la unión perno–placa de
anclaje y comprobar acero, arrancamiento, cono de hormigón, distancias,
recubrimientos, armadura, placa base y grout.

La doble malla Ø8 c/15 de la propuesta anterior **no se considera una armadura
verificada**; no hay despiece de armadura liberado en R2. Tampoco se certifica
H-21 como suficiente para el emplazamiento sin cálculo.

La jabalina se ubica fuera de la zapata. Debe disponer de conexión y caja de
inspección accesibles; su resistencia se mide en obra.

## 3. Gabinete

El desarrollo está en [`17_montaje_y_proteccion.md`](17_montaje_y_proteccion.md).
El fondo crece de 160 a 230 mm para separar planos y permitir un marco posterior
real. Las capotas añaden hasta 60 mm al dorso.

Se corrigen los cruces marco–bastidor, rieles–bastidor y fuente–montante. Los
rieles son tubos 30 × 20 × 2, no barras macizas. Hay bandeja de fuentes con cuatro
apoyos, carcasa, fondo inclinado, juntas, dos puertas reforzadas y bisagras
esquemáticas. Quedan por seleccionar cierres, retenciones y fijaciones definitivas.

## 4. Recorrido eléctrico

- Reserva Ø50 en la zapata, con curva de eje R100 y salida lateral a Z=−450 mm.
  Es una reserva constructiva; adaptar la acometida enterrada y profundidad a la
  instalación real, sin confundirla con un tendido ya especificado.
- Pasos Ø32 en grout, placa base y brida doble.
- Interior libre del mástil y del brazo; pasos Ø32 en las dos paredes del montante.
- Pasamuros, camisa real, radios de cable, guía de tendido y sellado por definir.
- PE dedicado a todas las masas; la brida, bisagra o unión mecánica no sustituye
  un conductor de protección. Las protecciones CA se coordinan con docs/03.

El verificador comprueba sondas Ø24 en las interfaces modeladas. Eso no verifica
que un mazo con conectores pueda introducirse o doblarse durante el montaje.

## 5. Masas e izaje

Las masas se calculan sobre el volumen CAD; módulos y fuentes tienen masas
asignadas. La ficha HTML/PDF es la referencia numérica regenerable.

Se añade una reserva explícita de **5 kg** para equipamiento no representado
completamente: cableado, control, auxiliar, cierres y soldaduras. No es un margen
de resistencia ni reemplaza el pesaje. La carga presupuestada de izaje incluye
gabinete, brazo, brida superior, herrajes modelados y esa reserva.

Montaje previsto:

1. Confirmar suelo, emplazamiento, viento y cálculo; ejecutar fundación y curado
   con procedimiento de obra, no con una autorización genérica de “7 días”.
2. Elevar el mástil con medios de elevación, nivelar y ejecutar grout.
3. Armar y probar gabinete y brazo en taller, con cableado y módulos.
4. Definir y calcular puntos de izaje, eslingado y retención secundaria.
5. Elevar el conjunto, presentar la brida y aplicar la secuencia de apriete calculada.
6. Conectar PE y alimentación; efectuar pruebas eléctricas, térmicas y de agua.

Acceso de servicio mediante plataforma adecuada: el centro de las puertas está
a 2,85 m. La apertura CAD no garantiza que un módulo pueda extraerse.

## 6. Cálculos de comparación, no aprobación

`especificaciones.py` recalcula, a partir de dimensiones y masas actuales:

- Viento uniforme de comparación: 45 m/s, aire 1,25 kg/m³, Cf=1,3 y Cd=2.
- Fuerzas sobre gabinete, mástil y brazo.
- Flexión y torsión, incluyendo el viento sobre el brazo.
- Momento permanente incluyendo la reserva de equipamiento.
- Tensión nominal combinada de una sección tubular ideal íntegra.
- Traslado del cortante al fondo de la zapata e índice de núcleo biaxial.
- Presiones mínima/máxima idealizadas bajo apoyo completo.

Se eliminan resultados estructurales escritos a mano como constantes. **No se
publican factores de seguridad, flecha total ni capacidad admisible aprobada.**
Faltan el procedimiento CIRSOC aplicable, combinaciones, viento en otras
direcciones, respuesta dinámica, fatiga, nudos locales y terreno real. Si la
presión mínima resulta negativa, el generador marca inválida la hipótesis de
apoyo completo en lugar de interpretar una tracción del suelo como válida.

## 7. Verificaciones automáticas

`verificar_modelo.py` se ejecuta antes de exportar:

- Validez topológica de todas las piezas.
- Interferencias entre **todas** las parejas, incluyendo las del mismo grupo.
- Excepción explícita únicamente para piezas declaradas embebidas contra hormigón.
- Apertura individual de cada puerta con sus accesorios, de 5° a 110° cada 5°.
- Sondas en pasos de cables. Umbral volumétrico: 1 mm³.

El ensayo de apertura es **discreto e individual**, contra la otra hoja cerrada;
no demuestra todo el movimiento continuo ni la apertura simultánea. No incluye
cables flexibles, cierres o accesorios aún no seleccionados. Una interferencia o
forma inválida aborta la exportación.

## 8. Pendientes de liberación

- [ ] Suelo, viento, emplazamiento, gálibo y lado del mástil.
- [ ] Cálculo de secciones, uniones, soldaduras, placa base, pernos y fundación.
- [ ] Armadura y planos de taller con tolerancias, acabados y secuencia.
- [ ] Muestra del módulo y prueba de extracción con rieles y fuentes instalados.
- [ ] Cierres, bisagras comerciales, fijaciones, puntos de izaje y retenciones.
- [ ] Caja de acometida, inspección de tierra, pasamuros y sellado del brazo.
- [ ] Curvas de ventilación, prueba térmica, agua/drenaje, PE y pesaje final.

Acortar el brazo podría reducir torsión, pero no se cambia su avance nominal de
500 mm sin confirmar ubicación y apariencia. Una segunda faz requiere revisar
viento, peso, centro de masa y ventilación; no se presume capacidad disponible.
