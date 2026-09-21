# 04 — Estructura y montaje en fachada

> **Documento superado.** La configuración adoptada es el gabinete en voladizo
> sobre **mástil con brazo lateral**: gabinete en [`17_montaje_y_proteccion.md`](17_montaje_y_proteccion.md)
> y soporte con fundación en [`18_monoposte.md`](18_monoposte.md). Se conserva como
> registro de la alternativa a fachada; su gabinete de 160 mm, su bastidor de
> aluminio 40×40 y sus anclajes químicos no aplican al diseño vigente. El cálculo
> de viento de abajo sigue siendo referencia de método.

## Gabinete

| Parámetro | Valor |
|---|---|
| Dimensiones exteriores | ~1340 × 700 × 160 mm (módulos + marco, fuentes y ventilación) |
| Material bastidor | Perfil aluminio estructural 40×40 mm |
| Fondo | Chapa de aluminio 2 mm como puerta trasera abisagrada (servicio) |
| Marco frontal | Perfil plegado con junta neopreno/EPDM perimetral |
| Montaje de módulos | Rieles horizontales 20×20, tornillería inox M3/M4 con junta entre módulos |
| Ventilación | Dos ventiladores con rulemán, flujo total ≥200 m³/h, entrada filtrada inferior y salida superior + drenajes |
| Separación de la pared | 80 mm mínimo para ventilación trasera |
| Acceso | Trasero (puerta de servicio) — requiere andamio/escalera |

### Corte de perfiles (referencia, confirmar con módulo real)

- 4× perfil 40×40 L=1340 mm (marco horizontal)
- 4× perfil 40×40 L=660 mm (marco vertical)
- 4× riel 20×20 L=1280 mm (un riel por fila de módulos, a 160 mm entre centros)
- Chapa trasera 1310 × 670 mm con bisagras inox + cierre a presión con junta

### Sellado

- Cordón EPDM perimetral entre módulos y marco frontal (compresión 30 %); no reemplaza una clasificación IP del módulo que el vendedor debe declarar.
- Sellante neutro de poliuretano (tipo Sika) en fijaciones que atraviesan el gabinete
- **Nunca sellante ácido** (ataca estaños y cobre de los módulos)
- Drenajes inferiores en dos esquinas (salida de condensación)

## Montaje en fachada

### Anclaje

- 6× anclaje químico M10 × 110 mm en hormigón o ladrillo macizo (NO ladrillo hueco — si la pared es hueca, atravesar con bulón + placa de repartición interior)
- Subestructura: 2 rieles verticales de aluminio/ acero galvanizado fijados a pared, el gabinete se fija a los rieles con tornillería M8 inox → desmontable para servicio
- Torque de anclajes según ficha del químico (típicamente 20–30 Nm tras curado completo 24–72 h)

### Cálculo de viento

- Área expuesta: A = 1,28 × 0,64 = 0,8192 m²
- Velocidad de diseño: 150 km/h = 41,7 m/s
- Fuerza: F = ½·ρ·v²·A·Cd = 0,5 × 1,25 × 41,7² × 0,8192 × 1,3 ≈ **1.157 N ≈ 118 kgf**
- 6× anclajes M10 químicos: capacidad típica > 200 kgf c/u en hormigón → factor de seguridad estático > 10. La fijación final debe ser validada por un profesional según pared y normativa local.
- Carga sobre tornillería del gabinete M8 (8×): sobrada para 118 kgf repartidos.

## Termal

| Condición | Estrategia |
|---|---|
| Verano / sol directo | Ventilación forzada termostatada. El consumo máximo declarado es 655 W, por lo que la convección natural no es suficiente. |
| Invierno / heladas | Confirmar rango térmico del módulo con el vendedor; la disipación de las fuentes eleva la temperatura interior durante operación. |
| Condensación | Drenajes + posición de fuentes en la mitad superior del gabinete |

Verificación en test: con los filtros limpios, temperatura interior ≤ 15 °C sobre ambiente a blanco completo sostenido 1 h.
