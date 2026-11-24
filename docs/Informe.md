Proyecto 2 Transporte


Fundamentos de Inteligencia Artificial · CINF103 · Universidad Andrés Bello

-Objetivo

El proyecto trata sobre una central de despachos en donde a dos agentes se les presentará la misma información y deberán determinar una acción dependiendo de las condiciones entregadas, como la urgencia y los vehículos disponibles, con el fin de comparar a Prolog, que toma decisiones en base a reglas explícitas, y Laya, que elige mediante una pregunta de elección.


-Modelo del problema

El estado de los pedidos se representan en un formato JSON que incluye su peso, tipo de carga, destino, urgencia y estado de la ruta, al igual que el vehículo asignado y una lista de vehículos alternativos en los cuales cada vehículo tiene su propio tipo, capacidad, disponibilidad, mantención, combustible y disponibilidad del conductor.

Una lista vacía ([]) indica que no hay vehículos alternativos. El valor null indica que se desconoce si hay alternativos y es importante para tomar una decisión.


| Acción       | Criterio general                                                                                                     |
| Despachar    | El asignado es apto, la ruta está libre y conviene salir.                                                            |
| Reasignar    | El asignado no sirve para el pedido y hay un alternativo apto.                                                       |
| Esperar      | El pedido puede quedar pendiente porque la salida está impedida o no conviene todavía.                               |
| Inspeccionar | Falta un dato crítico o hay información contradictoria. También se usa si ninguna regla permite tomar otra decisión. |
| Alertar      | Un pedido de urgencia alta no puede salir por la ruta cortada o por falta de un vehículo apto.                       |


-Funcionamiento de los agentes

Prolog transforma los datos en hechos que luego verifica que los vehículos cumplan, como la capacidad de carga, la compatibilidad con el tipo de carga y las restricciones de acceso. Por ejemplo, un vehículo debe poder soportar el peso del pedido y estar disponible para salir. Para un pedido de urgencia baja se tiene en consideración si la carga ocupa al menos un 80 % de la capacidad.

En Prolog, cuando hay más de una acción válida, tiene un orden de prioridades que sería: inspeccionar, alertar, reasignar, despachar y esperar. Y junto a la respuesta dada entrega los hechos y las reglas que avalan su respuesta.

Por su parte, Laya recibe el mismo estado que después lo convierte en texto en español. Se utilizó Laya 0.5.0 con el modelo multilingüe preentrenado, sin entrenamiento adicional para este proyecto. Aquí las preguntas de decisión entregan las mismas 5 acciones que a Prolog. Se le entregan en cinco distintos órdenes con el fin de encontrar una variación o cambio en su decisión, las cuales se promedia las probabilidades de cada acción y se elige la que tiene el promedio más alto. El sistema también formula preguntas de diagnóstico sobre las urgencias, los datos faltantes, las contradicciones y la aptitud del vehículo que se le asignó, pero estos se procesan por separado.


-Relación con Breakthrough

En el proyecto uno se usaba minimax y poda alfa-beta. Se simulaban jugadas prediciendo acciones del contrincante, descartando las posibles jugadas que no den buenos resultados para priorizar las que sí.

La forma en que se evaluaban las acciones era dando valores a las mismas. Cada jugador contaba con su propio puntaje inicial que se definía en cuántas piezas poseía. Se podían ganar o perder si una pieza era comida y la meta era la que mayor valor tenía, pero el avanzar hacia ella también brindaba puntos, pero en menor medida.

En los dos proyectos se requiere definir un estado y se le aplican criterios en los que basar sus acciones. En el caso del Breakthrough, su estado era el tablero y el agente que evaluaba sus posiciones futuras, tanto suyas como del rival. En este proyecto, el estado se ve representado por el pedido analizado. Prolog le aplica restricciones y prioridades de despacho, mientras que Laya estimaba en base a cálculos matemáticos.


-Metodología

Se evaluaron 20 casos con 5 categorías con 4 casos cada una. El grupo definió la decisión esperada y su motivo de antemano para que los agentes pudieran comparar sus resultados. Cada agente solo recibió los estados de cada pedido y posteriormente fue comparado con el caso esperado.

El acierto mide si la decisión de un agente coincide con la esperada. El acuerdo mide si ambos agentes eligen la misma acción, incluso si esas acciones están erróneas. La confianza de Laya corresponde a la probabilidad promediada de la acción que eligió.

El último arranque usó SWI-Prolog 10.0.2 y Laya 0.5.0. El comando `python -m experimento.ejecutar` se procesaron los veinte casos y los resultados se guardaron en `experimento/resultados.json`, `experimento/resultados.csv` y `experimento/resultados.md`.


-Resultados

| Categoría                  | Prolog | Laya |
| Información directa        | 4/4    | 1/4  |
| Inferencia de un paso      | 4/4    | 1/4  |
| Inferencia encadenada      | 4/4    | 1/4  |
| Información incompleta     | 4/4    | 0/4  |
| Contradicción o ambigüedad | 4/4    | 0/4  |
| Total                      | 20/20  | 3/20 |

Prolog consiguió un 100 % de acierto, mientras que Laya un 15 %. Solo coincidieron en tres casos y estuvieron en desacuerdo los otros diecisiete casos.

Laya eligió esperar en 18 casos e inspeccionar en dos. Sus aciertos fueron C03, C08 y C11, los tres casos en que correspondía esperar. Una regla que eligiera siempre esperar habría obtenido el mismo número de aciertos en este conjunto. La confianza media de Laya fue de 0,397 en los aciertos y de 0,421 en los errores.


-Análisis de casos

| Caso                                                            | Decisión esperada y de Prolog | Decisión de Laya |
| C03.- Pedido no urgente con ruta cortada                        | Esperar                       | Esperar          |
| C09.- Carga refrigerada con un alternativo apto                 | Reasignar                     | Inspeccionar     |
| C15.- Alternativos desconocidos, asignado apto y pedido urgente | Despachar                     | Inspeccionar     |
| C17.- Pedido urgente con ruta cortada y un alternativo apto     | Alertar                       | Esperar          |
| C19.- Vehículo informado como disponible y en mantención        | Inspeccionar                  | Esperar          |

C09: Prolog comprobó que el vehículo asignado era incompatible con la carga refrigerada. Luego verificó que el alternativo estaba operativo, soportaba los 900 kg, podía transportar carga refrigerada y podía ingresar al centro. Esas condiciones justificaron la reasignación.

C15: faltaba saber si había vehículos alternativos, pero ese dato no impedía decidir. El asignado era apto y el pedido era urgente. Laya eligió inspeccionar con una confianza de 0,560, aunque la decisión esperada era despachar.

C17: Prolog encontró dos acciones posibles: reasignar y alertar. La ruta cortada impedía resolver el problema con un cambio de vehículo, así que la alerta tuvo prioridad. En C19 también se podía demostrar una reasignación. La contradicción en los datos del asignado hizo que inspeccionar tuviera prioridad.

-Conclusiones y mejoras

Prolog aplicó la política de despacho del grupo en los veinte casos y mostró cómo llegó a cada decisión. Por su parte, Laya entregó una acción junto con las probabilidades de las alternativas, pero la gran mayoría de sus respuestas fueron esperar y, en menor medida, inspeccionar. La confianza fue mayor en los errores que en los aciertos, por lo que no fue suficiente para determinar una decisión correcta.

Los casos son simulados y para determinar sus resultados esperados usamos las políticas de Prolog, eso explicando el que consiguiera 20 de 20 aciertos. Por su parte, Laya mostró que prefirió esperar con mucha frecuencia, pero no nos permite determinar por qué ocurrió esa tendencia.

Cómo mejorar. El modelo de Laya se podría mejorar brindándole descripciones más claras para las cinco acciones, ir cambiando un elemento a la vez para ver la variación de los resultados durante el desarrollo.