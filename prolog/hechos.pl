:- encoding(utf8).
/*  hechos.pl  ·  Datos concretos de pedidos de ejemplo (Persona 1)
    ------------------------------------------------------------------
    Escritos a mano para la demo de Prolog y para prolog/consultas.pl.
    Cada campo del estado canónico es un hecho campo(Entidad, Valor);
    un campo vacío sería desconocido(Entidad, campo).

    p01, p02 y p05 son la traducción exacta de los casos C01, C02 y C05
    de casos/casos_directa_paso1.json. p90, p91 y p92 son ejemplos solo
    para la demo: inferencia encadenada con retroceso, pedido sin
    solución y contradicción con varias acciones demostrables.

    Uso:  ?- [prolog/reglas, prolog/hechos].
*/

/* ---- p01 = caso C01 (ejemplo del contrato del grupo) ---------------
   Pedido urgente de 800 kg, camioneta de 1000 kg lista, ruta libre.
   Decisión esperada: despachar.                                       */
pedido(p01).
carga_kg(p01, 800).
tipo_carga(p01, general).
destino(p01, zona_norte).
urgencia(p01, alta).
ruta_despejada(p01, si).
asignado(p01, v10).

vehiculo(v10).
tipo_vehiculo(v10, camioneta).
capacidad_kg(v10, 1000).
disponible(v10, si).
en_mantencion(v10, no).
combustible(v10, suficiente).
conductor_disponible(v10, si).

/* ---- p02 = caso C02 ------------------------------------------------
   Pedido urgente, furgón listo, pero la ruta está cortada.
   Decisión esperada: alertar.                                         */
pedido(p02).
carga_kg(p02, 500).
tipo_carga(p02, general).
destino(p02, zona_sur).
urgencia(p02, alta).
ruta_despejada(p02, no).
asignado(p02, v20).

vehiculo(v20).
tipo_vehiculo(v20, furgon).
capacidad_kg(v20, 3500).
disponible(v20, si).
en_mantencion(v20, no).
combustible(v20, suficiente).
conductor_disponible(v20, si).

/* ---- p05 = caso C05 ------------------------------------------------
   1200 kg asignados a una camioneta de 1000 kg; hay un furgón libre.
   Decisión esperada: reasignar.                                       */
pedido(p05).
carga_kg(p05, 1200).
tipo_carga(p05, general).
destino(p05, zona_norte).
urgencia(p05, media).
ruta_despejada(p05, si).
asignado(p05, v50).
alternativo(p05, v51).

vehiculo(v50).
tipo_vehiculo(v50, camioneta).
capacidad_kg(v50, 1000).
disponible(v50, si).
en_mantencion(v50, no).
combustible(v50, suficiente).
conductor_disponible(v50, si).

vehiculo(v51).
tipo_vehiculo(v51, furgon).
capacidad_kg(v51, 3500).
disponible(v51, si).
en_mantencion(v51, no).
combustible(v51, suficiente).
conductor_disponible(v51, si).

/* ---- p90 · demo de inferencia encadenada y retroceso ---------------
   Carga refrigerada al centro asignada a un camión: no sirve por dos
   motivos (tipo de carga y zona restringida). El primer alternativo
   (v901) tiene poco combustible; el segundo (v902) sirve.
   Decisión esperada: reasignar (a v902).                              */
pedido(p90).
carga_kg(p90, 900).
tipo_carga(p90, refrigerada).
destino(p90, centro).
urgencia(p90, media).
ruta_despejada(p90, si).
asignado(p90, v900).
alternativo(p90, v901).
alternativo(p90, v902).

vehiculo(v900).
tipo_vehiculo(v900, camion).
capacidad_kg(v900, 8000).
disponible(v900, si).
en_mantencion(v900, no).
combustible(v900, suficiente).
conductor_disponible(v900, si).

vehiculo(v901).
tipo_vehiculo(v901, furgon_refrigerado).
capacidad_kg(v901, 3000).
disponible(v901, si).
en_mantencion(v901, no).
combustible(v901, bajo).
conductor_disponible(v901, si).

vehiculo(v902).
tipo_vehiculo(v902, furgon_refrigerado).
capacidad_kg(v902, 3000).
disponible(v902, si).
en_mantencion(v902, no).
combustible(v902, suficiente).
conductor_disponible(v902, si).

/* ---- p91 · demo de pedido sin solución -----------------------------
   El pedido existe, pero no se registró ningún vehículo asignado (y
   tampoco se marcó como desconocido). Ninguna regla de acción se puede
   demostrar, así que decidir/3 cae en inspeccionar por defecto.       */
pedido(p91).
carga_kg(p91, 300).
tipo_carga(p91, general).
destino(p91, zona_oriente).
urgencia(p91, alta).
ruta_despejada(p91, si).

/* ---- p92 · demo de contradicción y varias soluciones ---------------
   El sistema de flota dice que v920 está disponible, pero el taller lo
   tiene en mantención. Hay un alternativo apto, así que también se
   puede demostrar reasignar; la prioridad elige inspeccionar.
   Decisión esperada: inspeccionar.                                    */
pedido(p92).
carga_kg(p92, 600).
tipo_carga(p92, general).
destino(p92, zona_poniente).
urgencia(p92, media).
ruta_despejada(p92, si).
asignado(p92, v920).
alternativo(p92, v921).

vehiculo(v920).
tipo_vehiculo(v920, furgon).
capacidad_kg(v920, 3500).
disponible(v920, si).
en_mantencion(v920, si).
combustible(v920, suficiente).
conductor_disponible(v920, si).

vehiculo(v921).
tipo_vehiculo(v921, camioneta).
capacidad_kg(v921, 1500).
disponible(v921, si).
en_mantencion(v921, no).
combustible(v921, suficiente).
conductor_disponible(v921, si).
