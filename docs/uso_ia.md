## Uso de IA
Usamos Claude, como asistente, y lo declaramos en docs/uso_ia.md, como pide el enunciado. La base de conocimiento de Prolog es trabajo nuestro: las reglas, las prioridades y el meta-intérprete que arma el árbol ya estaban antes.
La IA nos ayudó con la parte técnica alrededor: el servidor, la página, las pruebas y que el proceso de Prolog recargue las reglas solo. Ninguna IA toma decisiones en la app: las reglas de Prolog las escribimos nosotros.


Bastian
Usé ChatGPT para:
Poder determinar cuáles eran los campos de salida de Prolog y Laya para luego poder realizar la comparación entre ellos.
Subí mi informe y que corrigiera las faltas de ortografía para después pegar el texto corregido.
Probar una descripción distinta para la acción esperar y ver si seguía dependiendo de ella, se probó con 25 casos distintos y su dependencia no bajó en realidad.
Preparar las primeras versiones de `runner.py` y `metricas.py`. Con el primero se guardaban las respuestas de ambos agentes en un JSON y el segundo se encargaba del conteo de los aciertos leyendo el JSON. Después todo eso fue reorganizado y mejorado en `experimento/ejecutar.py`.
Fotos de la 1 a la 4 en docs\Evidencia