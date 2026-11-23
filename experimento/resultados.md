# Resultados del experimento: Prolog vs Laya

Generado por `python -m experimento.ejecutar` el 2026-11-23T18:30:07. SWI-Prolog 10.0.2 · laya 0.5.0 (checkpoint multilingüe, sin entrenar). Las decisiones esperadas se definieron antes de ejecutar (casos/casos.json).

## Métricas

| Métrica | Prolog | Laya |
|---|---|---|
| Aciertos | 20/20 | 3/20 |
| Acuerdo entre agentes | — | 3/20 |
| Confianza media de Laya cuando acierta | — | 0.397 |
| Confianza media de Laya cuando falla | — | 0.421 |
| Casos en que los 5 órdenes eligen lo mismo | — | 6/20 |
| Acciones que eligió Laya | — | esperar 18, inspeccionar 2 |

Referencia: eligiendo al azar entre 5 acciones se esperan 4 aciertos de 20 (20 %).

### Aciertos por categoría

| Categoría | Prolog | Laya |
|---|---|---|
| Información directa | 4/4 | 1/4 |
| Inferencia de un paso | 4/4 | 1/4 |
| Inferencia encadenada | 4/4 | 1/4 |
| Información incompleta | 4/4 | 0/4 |
| Contradicción o ambigüedad | 4/4 | 0/4 |

### Preguntas de diagnóstico de Laya (score y noul) frente a Prolog

| Pregunta | Tipo | Se compara con | Coinciden |
|---|---|---|---|
| ¿Qué urgencia tiene el pedido? | score | `urgencia/2 (hecho del estado)` | 7/19 |
| ¿Falta algún dato necesario para decidir (aparece sin dato)? | noul | `falta_dato_critico/2` | 3/20 |
| ¿Hay datos que se contradicen, como un vehículo disponible y en mantención a la vez o una capacidad imposible para su tipo? | noul | `contradiccion/2` | 3/20 |
| ¿El vehículo asignado puede llevar este pedido (disponible, fuera del taller, con combustible, con conductor, con capacidad suficiente y compatible con la carga y el destino)? | noul | `vehiculo_apto/2 con el vehículo asignado` | 8/20 |

### Matriz de confusión de Laya (filas: esperada · columnas: elegida)

| esperada \ elegida | despachar | reasignar | esperar | inspeccionar | alertar |
|---|---|---|---|---|---|
| despachar | · | · | 2 | 1 | · |
| reasignar | · | · | 3 | 1 | · |
| esperar | · | · | 3 | · | · |
| inspeccionar | · | · | 6 | · | · |
| alertar | · | · | 4 | · | · |

## Los 20 casos

Cada caso registra: identificador y descripción, estado común, decisión esperada y criterio, salida y justificación de Prolog, salida de Laya con probabilidades y confianza, resultado correcto o incorrecto, y observación.

### C01 · Información directa

- **Descripción:** Pedido urgente con una camioneta lista y la ruta libre (el ejemplo del contrato del grupo).
- **Estado común:** 800 kg general → zona_norte, urgencia alta, ruta despejada sí. Asignado: V10 camioneta 1000 kg, disp=sí, taller=no, comb=suficiente, cond=sí. Alternativos: ninguno
- **Esperada:** `despachar`. Criterio: Todo lo necesario está explícito: el vehículo asignado está disponible, fuera del taller, con combustible y conductor; 800 kg caben en 1000 kg; la ruta está despejada y el pedido es urgente.
- **Prolog:** `despachar` ✅ · candidatas: despachar
  ```
  accion_candidata(p01,despachar)   <- regla
      asignado(p01,v10)   <- hecho
      vehiculo_apto(p01,v10)   <- regla
      ruta_despejada(p01,si)   <- hecho
      conviene_salir(p01,v10)   <- regla
  ```
- **Laya:** `esperar` ❌ · confianza 0.4653 · margen 0.2354 · estabilidad 5/5 · despachar 0.15, reasignar 0.04, esperar 0.47, inspeccionar 0.23, alertar 0.12
- **Observación:** Laya eligió esperar (0.47); a la esperada le dio 0.15.

### C02 · Información directa

- **Descripción:** Pedido urgente con el vehículo listo, pero la ruta está cortada.
- **Estado común:** 500 kg general → zona_sur, urgencia alta, ruta despejada no. Asignado: V20 furgon 3500 kg, disp=sí, taller=no, comb=suficiente, cond=sí. Alternativos: ninguno
- **Esperada:** `alertar`. Criterio: La ruta no está despejada, así que no se puede despachar; como el pedido es urgente, no corresponde esperar sin más: el supervisor debe decidir (otra ruta, reprogramar o avisar al cliente).
- **Prolog:** `alertar` ✅ · candidatas: alertar
  ```
  accion_candidata(p02,alertar)   <- regla
      urgente(p02)   <- regla
      ruta_despejada(p02,no)   <- hecho
  ```
- **Laya:** `esperar` ❌ · confianza 0.4525 · margen 0.2436 · estabilidad 4/5 · despachar 0.18, reasignar 0.06, esperar 0.45, inspeccionar 0.21, alertar 0.10
- **Observación:** Laya eligió esperar (0.45); a la esperada le dio 0.10. La respuesta de Laya depende del orden de las alternativas (4 de 5 órdenes eligen lo mismo).

### C03 · Información directa

- **Descripción:** Pedido sin urgencia con la ruta cortada.
- **Estado común:** 400 kg general → zona_oriente, urgencia baja, ruta despejada no. Asignado: V30 camioneta 1500 kg, disp=sí, taller=no, comb=suficiente, cond=sí. Alternativos: ninguno
- **Esperada:** `esperar`. Criterio: La ruta está cortada y el pedido no es urgente: no hace falta molestar al supervisor, basta con esperar a que se despeje.
- **Prolog:** `esperar` ✅ · candidatas: esperar
  ```
  accion_candidata(p03,esperar)   <- regla
      ruta_despejada(p03,no)   <- hecho
      no se puede demostrar urgente(p03)   <- negación por falla (falla: urgencia(p03,alta))
  ```
- **Laya:** `esperar` ✅ · confianza 0.4291 · margen 0.1843 · estabilidad 4/5 · despachar 0.19, reasignar 0.04, esperar 0.43, inspeccionar 0.24, alertar 0.10
- **Observación:** Laya acierta con confianza 0.43. La respuesta de Laya depende del orden de las alternativas (4 de 5 órdenes eligen lo mismo).

### C04 · Información directa

- **Descripción:** El vehículo asignado está en el taller y hay un furgón alternativo listo.
- **Estado común:** 1200 kg general → zona_poniente, urgencia media, ruta despejada sí. Asignado: V40 furgon 3500 kg, disp=no, taller=sí, comb=suficiente, cond=sí. Alternativos: V41 furgon 3500 kg, disp=sí, taller=no, comb=suficiente, cond=sí
- **Esperada:** `reasignar`. Criterio: El estado dice explícitamente que el asignado no está disponible y está en mantención (dato coherente, no contradictorio); el alternativo es del mismo tipo y está listo.
- **Prolog:** `reasignar` ✅ · candidatas: reasignar
  ```
  accion_candidata(p04,reasignar)   <- regla
      asignado(p04,v40)   <- hecho
      no se puede demostrar vehiculo_apto(p04,v40)   <- negación por falla (falla: operativo(v40))
      alternativa_apta(p04,v41)   <- regla
  ```
- **Laya:** `esperar` ❌ · confianza 0.364 · margen 0.1038 · estabilidad 4/5 · despachar 0.15, reasignar 0.16, esperar 0.36, inspeccionar 0.26, alertar 0.06
- **Observación:** Laya eligió esperar (0.36); a la esperada le dio 0.16. La respuesta de Laya depende del orden de las alternativas (4 de 5 órdenes eligen lo mismo).

### C05 · Inferencia de un paso

- **Descripción:** La carga pesa más de lo que soporta la camioneta asignada; hay un furgón libre.
- **Estado común:** 1200 kg general → zona_norte, urgencia media, ruta despejada sí. Asignado: V50 camioneta 1000 kg, disp=sí, taller=no, comb=suficiente, cond=sí. Alternativos: V51 furgon 3500 kg, disp=sí, taller=no, comb=suficiente, cond=sí
- **Esperada:** `reasignar`. Criterio: Una regla: la capacidad (1200 kg > 1000 kg). El asignado está operativo, pero la carga no cabe; el furgón alternativo sí tiene capacidad.
- **Prolog:** `reasignar` ✅ · candidatas: reasignar
  ```
  accion_candidata(p05,reasignar)   <- regla
      asignado(p05,v50)   <- hecho
      no se puede demostrar vehiculo_apto(p05,v50)   <- negación por falla (falla: tiene_capacidad(p05,v50))
      alternativa_apta(p05,v51)   <- regla
  ```
- **Laya:** `esperar` ❌ · confianza 0.3168 · margen 0.0304 · estabilidad 3/5 · despachar 0.17, reasignar 0.18, esperar 0.32, inspeccionar 0.29, alertar 0.05
- **Observación:** Laya eligió esperar (0.32); a la esperada le dio 0.18. La respuesta de Laya depende del orden de las alternativas (3 de 5 órdenes eligen lo mismo).

### C06 · Inferencia de un paso

- **Descripción:** Carga refrigerada urgente asignada a un furgón común, sin vehículos alternativos.
- **Estado común:** 300 kg refrigerada → zona_sur, urgencia alta, ruta despejada sí. Asignado: V60 furgon 3500 kg, disp=sí, taller=no, comb=suficiente, cond=sí. Alternativos: ninguno
- **Esperada:** `alertar`. Criterio: Una regla: la carga refrigerada solo puede ir en furgón refrigerado. El furgón asignado no sirve y no hay alternativos; como el pedido es urgente, debe intervenir el supervisor.
- **Prolog:** `alertar` ✅ · candidatas: alertar
  ```
  accion_candidata(p06,alertar)   <- regla
      urgente(p06)   <- regla
      sin_vehiculo_apto(p06)   <- regla
  ```
- **Laya:** `esperar` ❌ · confianza 0.4237 · margen 0.209 · estabilidad 4/5 · despachar 0.21, reasignar 0.05, esperar 0.42, inspeccionar 0.21, alertar 0.10
- **Observación:** Laya eligió esperar (0.42); a la esperada le dio 0.10. La respuesta de Laya depende del orden de las alternativas (4 de 5 órdenes eligen lo mismo).

### C07 · Inferencia de un paso

- **Descripción:** Pedido sin urgencia que llena casi toda la camioneta.
- **Estado común:** 1350 kg general → zona_oriente, urgencia baja, ruta despejada sí. Asignado: V70 camioneta 1500 kg, disp=sí, taller=no, comb=suficiente, cond=sí. Alternativos: ninguno
- **Esperada:** `despachar`. Criterio: Una regla: aprovechamiento. Aunque no hay urgencia, 1350 de 1500 kg es 90 % (sobre el umbral de 80 %): el viaje ya se aprovecha y no tiene sentido esperar para juntar más carga.
- **Prolog:** `despachar` ✅ · candidatas: despachar
  ```
  accion_candidata(p07,despachar)   <- regla
      asignado(p07,v70)   <- hecho
      vehiculo_apto(p07,v70)   <- regla
      ruta_despejada(p07,si)   <- hecho
      conviene_salir(p07,v70)   <- regla
  ```
- **Laya:** `esperar` ❌ · confianza 0.4257 · margen 0.1848 · estabilidad 4/5 · despachar 0.19, reasignar 0.04, esperar 0.43, inspeccionar 0.24, alertar 0.10
- **Observación:** Laya eligió esperar (0.43); a la esperada le dio 0.19. La respuesta de Laya depende del orden de las alternativas (4 de 5 órdenes eligen lo mismo).

### C08 · Inferencia de un paso

- **Descripción:** Pedido sin urgencia que ocupa muy poco del furgón.
- **Estado común:** 200 kg general → zona_poniente, urgencia baja, ruta despejada sí. Asignado: V80 furgon 1500 kg, disp=sí, taller=no, comb=suficiente, cond=sí. Alternativos: ninguno
- **Esperada:** `esperar`. Criterio: Una regla: aprovechamiento. Sin urgencia y con 200 de 1500 kg (13 %, bajo el 80 %), conviene esperar para consolidar con otros pedidos aunque el vehículo esté listo.
- **Prolog:** `esperar` ✅ · candidatas: esperar
  ```
  accion_candidata(p08,esperar)   <- regla
      asignado(p08,v80)   <- hecho
      vehiculo_apto(p08,v80)   <- regla
      ruta_despejada(p08,si)   <- hecho
      no se puede demostrar conviene_salir(p08,v80)   <- negación por falla (falla: urgencia(p08,alta) / urgencia(p08,media) / aprovechamiento_alto(p08,v80))
  ```
- **Laya:** `esperar` ✅ · confianza 0.4536 · margen 0.249 · estabilidad 5/5 · despachar 0.20, reasignar 0.05, esperar 0.45, inspeccionar 0.19, alertar 0.10
- **Observación:** Laya acierta con confianza 0.45.

### C09 · Inferencia encadenada

- **Descripción:** Carga refrigerada con destino al centro asignada a un camión; el alternativo es un furgón refrigerado listo.
- **Estado común:** 900 kg refrigerada → centro, urgencia media, ruta despejada sí. Asignado: V90 camion 8000 kg, disp=sí, taller=no, comb=suficiente, cond=sí. Alternativos: V91 furgon_refrigerado 3000 kg, disp=sí, taller=no, comb=suficiente, cond=sí
- **Esperada:** `reasignar`. Criterio: Varias relaciones: el camión no sirve porque la carga refrigerada exige furgón refrigerado (y además los camiones no entran al centro); el alternativo es refrigerado, está operativo, tiene capacidad y puede entrar al centro.
- **Prolog:** `reasignar` ✅ · candidatas: reasignar
  ```
  accion_candidata(p09,reasignar)   <- regla
      asignado(p09,v90)   <- hecho
      no se puede demostrar vehiculo_apto(p09,v90)   <- negación por falla (falla: tipo_compatible(p09,v90))
      alternativa_apta(p09,v91)   <- regla
  ```
- **Laya:** `inspeccionar` ❌ · confianza 0.3297 · margen 0.0362 · estabilidad 3/5 · despachar 0.14, reasignar 0.18, esperar 0.29, inspeccionar 0.33, alertar 0.06
- **Observación:** Laya eligió inspeccionar (0.33); a la esperada le dio 0.18. La respuesta de Laya depende del orden de las alternativas (3 de 5 órdenes eligen lo mismo).

### C10 · Inferencia encadenada

- **Descripción:** Pedido urgente: la camioneta asignada no tiene conductor y el único alternativo tiene poco combustible.
- **Estado común:** 700 kg general → zona_sur, urgencia alta, ruta despejada sí. Asignado: V100 camioneta 1500 kg, disp=sí, taller=no, comb=suficiente, cond=no. Alternativos: V101 furgon 3500 kg, disp=sí, taller=no, comb=bajo, cond=sí
- **Esperada:** `alertar`. Criterio: Cadena: sin conductor el asignado no está operativo; con poco combustible el alternativo tampoco; por lo tanto no hay vehículo apto, y como el pedido es urgente debe intervenir el supervisor.
- **Prolog:** `alertar` ✅ · candidatas: alertar
  ```
  accion_candidata(p10,alertar)   <- regla
      urgente(p10)   <- regla
      sin_vehiculo_apto(p10)   <- regla
  ```
- **Laya:** `esperar` ❌ · confianza 0.369 · margen 0.1073 · estabilidad 3/5 · despachar 0.17, reasignar 0.13, esperar 0.37, inspeccionar 0.26, alertar 0.07
- **Observación:** Laya eligió esperar (0.37); a la esperada le dio 0.07. La respuesta de Laya depende del orden de las alternativas (3 de 5 órdenes eligen lo mismo).

### C11 · Inferencia encadenada

- **Descripción:** Pedido no urgente: la carga no cabe en el vehículo asignado y el alternativo no tiene conductor.
- **Estado común:** 1800 kg general → zona_oriente, urgencia baja, ruta despejada sí. Asignado: V110 camioneta 1500 kg, disp=sí, taller=no, comb=suficiente, cond=sí. Alternativos: V111 furgon 3500 kg, disp=sí, taller=no, comb=suficiente, cond=no
- **Esperada:** `esperar`. Criterio: Cadena: 1800 kg no caben en 1500 kg; el furgón tendría capacidad pero no tiene conductor; no hay vehículo apto y, como no es urgente, se espera a que haya uno libre.
- **Prolog:** `esperar` ✅ · candidatas: esperar
  ```
  accion_candidata(p11,esperar)   <- regla
      sin_vehiculo_apto(p11)   <- regla
      no se puede demostrar urgente(p11)   <- negación por falla (falla: urgencia(p11,alta))
  ```
- **Laya:** `esperar` ✅ · confianza 0.3077 · margen 0.0554 · estabilidad 2/5 · despachar 0.14, reasignar 0.23, esperar 0.31, inspeccionar 0.25, alertar 0.08
- **Observación:** Laya acierta con confianza 0.31. La respuesta de Laya depende del orden de las alternativas (2 de 5 órdenes eligen lo mismo).

### C12 · Inferencia encadenada

- **Descripción:** Camión asignado a un pedido con destino al centro; hay una camioneta alternativa lista.
- **Estado común:** 1100 kg general → centro, urgencia media, ruta despejada sí. Asignado: V120 camion 10000 kg, disp=sí, taller=no, comb=suficiente, cond=sí. Alternativos: V121 camioneta 1500 kg, disp=sí, taller=no, comb=suficiente, cond=sí
- **Esperada:** `reasignar`. Criterio: Cadena: destino centro + tipo camión => zona restringida => el camión no puede entrar aunque esté operativo y tenga capacidad; la camioneta alternativa sí puede y le caben los 1100 kg.
- **Prolog:** `reasignar` ✅ · candidatas: reasignar
  ```
  accion_candidata(p12,reasignar)   <- regla
      asignado(p12,v120)   <- hecho
      no se puede demostrar vehiculo_apto(p12,v120)   <- negación por falla (falla: puede_ingresar(p12,v120))
      alternativa_apta(p12,v121)   <- regla
  ```
- **Laya:** `esperar` ❌ · confianza 0.3855 · margen 0.1479 · estabilidad 3/5 · despachar 0.13, reasignar 0.18, esperar 0.39, inspeccionar 0.24, alertar 0.07
- **Observación:** Laya eligió esperar (0.39); a la esperada le dio 0.18. La respuesta de Laya depende del orden de las alternativas (3 de 5 órdenes eligen lo mismo).

### C13 · Información incompleta

- **Descripción:** No se registró la urgencia del pedido; todo lo demás está listo.
- **Estado común:** 600 kg general → zona_norte, urgencia sin dato, ruta despejada sí. Asignado: V130 furgon 3500 kg, disp=sí, taller=no, comb=suficiente, cond=sí. Alternativos: ninguno
- **Esperada:** `inspeccionar`. Criterio: Sin urgencia no se sabe si conviene salir ya o esperar a consolidar carga (el furgón iría al 17 %). Elegir despachar o esperar sería inventar el dato.
- **Prolog:** `inspeccionar` ✅ · candidatas: inspeccionar, esperar
  ```
  accion_candidata(p13,inspeccionar)   <- regla
      falta_dato_critico(p13,dato(p13,urgencia))   <- regla
  ```
- **Laya:** `esperar` ❌ · confianza 0.4843 · margen 0.2558 · estabilidad 5/5 · despachar 0.23, reasignar 0.06, esperar 0.48, inspeccionar 0.12, alertar 0.10
- **Observación:** Falta dato crítico: dato(p13,urgencia). Varias acciones demostrables (inspeccionar, esperar); Prolog elige por prioridad. Laya eligió esperar (0.48); a la esperada le dio 0.12.

### C14 · Información incompleta

- **Descripción:** Falta la capacidad del vehículo asignado.
- **Estado común:** 1200 kg general → zona_poniente, urgencia alta, ruta despejada sí. Asignado: V140 camioneta None kg, disp=sí, taller=no, comb=suficiente, cond=sí. Alternativos: ninguno
- **Esperada:** `inspeccionar`. Criterio: No se puede saber si 1200 kg caben en la camioneta. Aunque el pedido es urgente, alertar o despachar supondría un dato que no existe.
- **Prolog:** `inspeccionar` ✅ · candidatas: inspeccionar, alertar
  ```
  accion_candidata(p14,inspeccionar)   <- regla
      falta_dato_critico(p14,dato(v140,capacidad_kg))   <- regla
  ```
- **Laya:** `esperar` ❌ · confianza 0.5136 · margen 0.3139 · estabilidad 5/5 · despachar 0.20, reasignar 0.03, esperar 0.51, inspeccionar 0.13, alertar 0.13
- **Observación:** Falta dato crítico: dato(v140,capacidad_kg). Varias acciones demostrables (inspeccionar, alertar); Prolog elige por prioridad. Laya eligió esperar (0.51); a la esperada le dio 0.13.

### C15 · Información incompleta

- **Descripción:** No se sabe si hay vehículos alternativos, pero el asignado está listo y el pedido es urgente.
- **Estado común:** 800 kg general → zona_sur, urgencia alta, ruta despejada sí. Asignado: V150 camioneta 1500 kg, disp=sí, taller=no, comb=suficiente, cond=sí. Alternativos: sin dato
- **Esperada:** `despachar`. Criterio: Falta un dato, pero no importa: los alternativos solo se necesitan si el asignado no sirve, y el asignado sirve. Inspeccionar aquí sería demorar un pedido urgente sin motivo.
- **Prolog:** `despachar` ✅ · candidatas: despachar
  ```
  accion_candidata(p15,despachar)   <- regla
      asignado(p15,v150)   <- hecho
      vehiculo_apto(p15,v150)   <- regla
      ruta_despejada(p15,si)   <- hecho
      conviene_salir(p15,v150)   <- regla
  ```
- **Laya:** `inspeccionar` ❌ · confianza 0.56 · margen 0.367 · estabilidad 5/5 · despachar 0.11, reasignar 0.05, esperar 0.19, inspeccionar 0.56, alertar 0.09
- **Observación:** Laya eligió inspeccionar (0.56); a la esperada le dio 0.11.

### C16 · Información incompleta

- **Descripción:** El vehículo asignado está en el taller y del alternativo no se sabe el combustible.
- **Estado común:** 500 kg general → zona_oriente, urgencia media, ruta despejada sí. Asignado: V160 furgon 3500 kg, disp=no, taller=sí, comb=suficiente, cond=sí. Alternativos: V161 camioneta 1500 kg, disp=sí, taller=no, comb=sin dato, cond=sí
- **Esperada:** `inspeccionar`. Criterio: El asignado no sirve, así que el alternativo pasa a ser necesario, pero falta su combustible: no se puede saber si reasignar es posible.
- **Prolog:** `inspeccionar` ✅ · candidatas: inspeccionar, esperar
  ```
  accion_candidata(p16,inspeccionar)   <- regla
      falta_dato_critico(p16,dato(v161,combustible))   <- regla
  ```
- **Laya:** `esperar` ❌ · confianza 0.3501 · margen 0.0444 · estabilidad 3/5 · despachar 0.14, reasignar 0.13, esperar 0.35, inspeccionar 0.31, alertar 0.08
- **Observación:** Falta dato crítico: dato(v161,combustible). Varias acciones demostrables (inspeccionar, esperar); Prolog elige por prioridad. Laya eligió esperar (0.35); a la esperada le dio 0.31. La respuesta de Laya depende del orden de las alternativas (3 de 5 órdenes eligen lo mismo).

### C17 · Contradicción o ambigüedad

- **Descripción:** Ambigüedad: pedido urgente con la ruta cortada; el asignado está en el taller y hay un alternativo listo.
- **Estado común:** 500 kg general → zona_sur, urgencia alta, ruta despejada no. Asignado: V170 furgon 3500 kg, disp=no, taller=sí, comb=suficiente, cond=sí. Alternativos: V171 camioneta 1500 kg, disp=sí, taller=no, comb=suficiente, cond=sí
- **Esperada:** `alertar`. Criterio: Dos acciones se pueden justificar a la vez: reasignar (el alternativo sirve) y alertar (urgente con la ruta cortada). Reasignar no resuelve el problema, porque ningún vehículo puede pasar por la ruta cortada; con un pedido urgente decide el supervisor. La política de prioridad del grupo pone alertar antes que reasignar.
- **Prolog:** `alertar` ✅ · candidatas: alertar, reasignar
  ```
  accion_candidata(p17,alertar)   <- regla
      urgente(p17)   <- regla
      ruta_despejada(p17,no)   <- hecho
  ```
- **Laya:** `esperar` ❌ · confianza 0.4154 · margen 0.1612 · estabilidad 3/5 · despachar 0.14, reasignar 0.13, esperar 0.42, inspeccionar 0.25, alertar 0.06
- **Observación:** Varias acciones demostrables (alertar, reasignar); Prolog elige por prioridad. Laya eligió esperar (0.42); a la esperada le dio 0.06. La respuesta de Laya depende del orden de las alternativas (3 de 5 órdenes eligen lo mismo).

### C18 · Contradicción o ambigüedad

- **Descripción:** Contradicción: el sistema de flota dice que el vehículo está disponible y el taller dice que está en mantención.
- **Estado común:** 1500 kg general → zona_norte, urgencia media, ruta despejada sí. Asignado: V18 camioneta 1500 kg, disp=sí, taller=sí, comb=suficiente, cond=sí. Alternativos: ninguno
- **Esperada:** `inspeccionar`. Criterio: Los dos datos no pueden ser verdad al mismo tiempo. Despachar con un vehículo que podría estar en el taller es un riesgo; hay que revisar los datos antes de actuar.
- **Prolog:** `inspeccionar` ✅ · candidatas: inspeccionar, esperar
  ```
  accion_candidata(p18,inspeccionar)   <- regla
      contradiccion(p18,disponible_y_en_mantencion(v18))   <- regla
  ```
- **Laya:** `esperar` ❌ · confianza 0.4575 · margen 0.2563 · estabilidad 5/5 · despachar 0.18, reasignar 0.06, esperar 0.46, inspeccionar 0.20, alertar 0.10
- **Observación:** Contradicción: disponible_y_en_mantencion(v18). Varias acciones demostrables (inspeccionar, esperar); Prolog elige por prioridad. Laya eligió esperar (0.46); a la esperada le dio 0.20.

### C19 · Contradicción o ambigüedad

- **Descripción:** Contradicción con varias acciones posibles: el asignado figura disponible y en mantención, y hay un alternativo listo.
- **Estado común:** 600 kg general → zona_poniente, urgencia media, ruta despejada sí. Asignado: V190 furgon 3500 kg, disp=sí, taller=sí, comb=suficiente, cond=sí. Alternativos: V191 camioneta 1500 kg, disp=sí, taller=no, comb=suficiente, cond=sí
- **Esperada:** `inspeccionar`. Criterio: Se podría reasignar al alternativo, pero el registro del asignado es contradictorio y la central no sabe cuál de los dos sistemas se equivoca. Primero se revisan los datos (política: la calidad de los datos va antes que la operación).
- **Prolog:** `inspeccionar` ✅ · candidatas: inspeccionar, reasignar
  ```
  accion_candidata(p19,inspeccionar)   <- regla
      contradiccion(p19,disponible_y_en_mantencion(v190))   <- regla
  ```
- **Laya:** `esperar` ❌ · confianza 0.3942 · margen 0.1296 · estabilidad 3/5 · despachar 0.15, reasignar 0.13, esperar 0.39, inspeccionar 0.26, alertar 0.06
- **Observación:** Contradicción: disponible_y_en_mantencion(v190). Varias acciones demostrables (inspeccionar, reasignar); Prolog elige por prioridad. Laya eligió esperar (0.39); a la esperada le dio 0.26. La respuesta de Laya depende del orden de las alternativas (3 de 5 órdenes eligen lo mismo).

### C20 · Contradicción o ambigüedad

- **Descripción:** Contradicción: la capacidad declarada (9000 kg) es imposible para una camioneta.
- **Estado común:** 200 kg general → zona_poniente, urgencia alta, ruta despejada sí. Asignado: V20 camioneta 9000 kg, disp=sí, taller=no, comb=suficiente, cond=sí. Alternativos: ninguno
- **Esperada:** `inspeccionar`. Criterio: Una camioneta carga como máximo 1500 kg (supuesto S7 del grupo). Si el registro dice 9000 kg, hay un error en los datos y no se puede confiar en que la carga quepa.
- **Prolog:** `inspeccionar` ✅ · candidatas: inspeccionar, despachar
  ```
  accion_candidata(p20,inspeccionar)   <- regla
      contradiccion(p20,capacidad_imposible(v20))   <- regla
  ```
- **Laya:** `esperar` ❌ · confianza 0.4417 · margen 0.2071 · estabilidad 4/5 · despachar 0.18, reasignar 0.05, esperar 0.44, inspeccionar 0.23, alertar 0.09
- **Observación:** Contradicción: capacidad_imposible(v20). Varias acciones demostrables (inspeccionar, despachar); Prolog elige por prioridad. Laya eligió esperar (0.44); a la esperada le dio 0.23. La respuesta de Laya depende del orden de las alternativas (4 de 5 órdenes eligen lo mismo).
