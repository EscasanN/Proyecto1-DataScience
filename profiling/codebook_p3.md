# Code book — estrategia de limpieza

Reglas probadas sobre: datos crudos completos (2,000 filas). Tratamiento
propuesto por variable. NINGUNA de estas reglas esta aplicada de forma
definitiva sobre `raw_files/datos_crudos_completos.csv`: son el plan de
limpieza (actividad 4), medidas sobre una muestra para saber cuanto
tocaria cada una antes de decidir aplicarla sobre el dataset completo.

| variable | problema | transformación propuesta | riesgo |
|---|---|---|---|
| AREA | faltantes representados de formas distintas (celda vacia, \xa0, N/A, NULL, ---, etc.) | normalizar_faltantes | un centinela puede ser ambiguo: '0' esta en la lista de centinelas (detectores.CENTINELAS) pero podria ser un valor real en una variable numerica que no sea TELEFONO/CODIGO; revisar antes de aplicar fuera de esas dos |
| AREA | espacios al inicio/final o multiples espacios internos | normalizar_espacios | minimo; un espacio interno multiple casi nunca es intencional en este dataset |
| AREA | caracteres invisibles (nbsp, tabs, saltos de linea, etc.) | quitar_invisibles | bajo: se reemplazan por un espacio normal, nunca se borran, asi que no pegan palabras que estaban separadas |
| AREA | puntuacion sobrante al inicio o final | quitar_puntuacion_borde | bajo, pero depende de que los delimitadores desbalanceados ya se hayan revisado; si no, se puede dejar un parentesis o comilla sin su cierre |
| AREA | mayusculas inconsistentes | normalizar_mayusculas | bajo: son categoricas de dominio cerrado, casi todo el dataset ya viene en mayusculas |
| CODIGO | caracteres invisibles (nbsp, tabs, saltos de linea, etc.) | quitar_invisibles | bajo: se reemplazan por un espacio normal, nunca se borran, asi que no pegan palabras que estaban separadas |
| CODIGO | codigo fuera del patron dd-dd-dddd-dd | normalizar_codigo | CODIGO es la llave del establecimiento: forzar un formato sin verificar el valor real podria mezclar dos establecimientos o dejar uno sin identificador valido; los que no calcen quedan para revision manual, no se tocan |
| CODIGO | espacios al inicio/final o multiples espacios internos | normalizar_espacios | minimo; un espacio interno multiple casi nunca es intencional en este dataset |
| CODIGO | faltantes representados de formas distintas (celda vacia, \xa0, N/A, NULL, ---, etc.) | normalizar_faltantes | un centinela puede ser ambiguo: '0' esta en la lista de centinelas (detectores.CENTINELAS) pero podria ser un valor real en una variable numerica que no sea TELEFONO/CODIGO; revisar antes de aplicar fuera de esas dos |
| DEPARTAMENTAL | espacios al inicio/final o multiples espacios internos | normalizar_espacios | minimo; un espacio interno multiple casi nunca es intencional en este dataset |
| DEPARTAMENTAL | puntuacion sobrante al inicio o final | quitar_puntuacion_borde | bajo, pero depende de que los delimitadores desbalanceados ya se hayan revisado; si no, se puede dejar un parentesis o comilla sin su cierre |
| DEPARTAMENTAL | faltantes representados de formas distintas (celda vacia, \xa0, N/A, NULL, ---, etc.) | normalizar_faltantes | un centinela puede ser ambiguo: '0' esta en la lista de centinelas (detectores.CENTINELAS) pero podria ser un valor real en una variable numerica que no sea TELEFONO/CODIGO; revisar antes de aplicar fuera de esas dos |
| DEPARTAMENTAL | mayusculas inconsistentes | normalizar_mayusculas | bajo: son categoricas de dominio cerrado, casi todo el dataset ya viene en mayusculas |
| DEPARTAMENTAL | caracteres invisibles (nbsp, tabs, saltos de linea, etc.) | quitar_invisibles | bajo: se reemplazan por un espacio normal, nunca se borran, asi que no pegan palabras que estaban separadas |
| DEPARTAMENTO | mayusculas inconsistentes | normalizar_mayusculas | bajo: son categoricas de dominio cerrado, casi todo el dataset ya viene en mayusculas |
| DEPARTAMENTO | caracteres invisibles (nbsp, tabs, saltos de linea, etc.) | quitar_invisibles | bajo: se reemplazan por un espacio normal, nunca se borran, asi que no pegan palabras que estaban separadas |
| DEPARTAMENTO | faltantes representados de formas distintas (celda vacia, \xa0, N/A, NULL, ---, etc.) | normalizar_faltantes | un centinela puede ser ambiguo: '0' esta en la lista de centinelas (detectores.CENTINELAS) pero podria ser un valor real en una variable numerica que no sea TELEFONO/CODIGO; revisar antes de aplicar fuera de esas dos |
| DEPARTAMENTO | espacios al inicio/final o multiples espacios internos | normalizar_espacios | minimo; un espacio interno multiple casi nunca es intencional en este dataset |
| DEPARTAMENTO | valor fuera del catalogo oficial (ver profiler.detectar_fuera_de_catalogo) | ninguna: marcar para revision manual | autocorregir a ciegas por similitud de texto podria asignar un establecimiento al departamento equivocado; se revisa a mano contra profiling/valores_problematicos.csv |
| DEPARTAMENTO | puntuacion sobrante al inicio o final | quitar_puntuacion_borde | bajo, pero depende de que los delimitadores desbalanceados ya se hayan revisado; si no, se puede dejar un parentesis o comilla sin su cierre |
| DIRECCION | caracteres invisibles (nbsp, tabs, saltos de linea, etc.) | quitar_invisibles | bajo: se reemplazan por un espacio normal, nunca se borran, asi que no pegan palabras que estaban separadas |
| DIRECCION | espacios al inicio/final o multiples espacios internos | normalizar_espacios | minimo; un espacio interno multiple casi nunca es intencional en este dataset |
| DIRECCION | mayusculas inconsistentes | normalizar_mayusculas | mas alto que en las categoricas: son nombres propios (ej. ESTABLECIMIENTO), y el enunciado pide conservar la ortografia; mayusculizar no cambia letras pero SI pierde cualquier estilizacion de mayusculas que fuera intencional (poco probable, pero no se puede verificar solo con la columna) |
| DIRECCION | faltantes representados de formas distintas (celda vacia, \xa0, N/A, NULL, ---, etc.) | normalizar_faltantes | un centinela puede ser ambiguo: '0' esta en la lista de centinelas (detectores.CENTINELAS) pero podria ser un valor real en una variable numerica que no sea TELEFONO/CODIGO; revisar antes de aplicar fuera de esas dos |
| DIRECCION | puntuacion sobrante al inicio o final | quitar_puntuacion_borde | bajo, pero depende de que los delimitadores desbalanceados ya se hayan revisado; si no, se puede dejar un parentesis o comilla sin su cierre |
| DIRECTOR | puntuacion sobrante al inicio o final | quitar_puntuacion_borde | bajo, pero depende de que los delimitadores desbalanceados ya se hayan revisado; si no, se puede dejar un parentesis o comilla sin su cierre |
| DIRECTOR | mayusculas inconsistentes | normalizar_mayusculas | mas alto que en las categoricas: son nombres propios (ej. ESTABLECIMIENTO), y el enunciado pide conservar la ortografia; mayusculizar no cambia letras pero SI pierde cualquier estilizacion de mayusculas que fuera intencional (poco probable, pero no se puede verificar solo con la columna) |
| DIRECTOR | espacios al inicio/final o multiples espacios internos | normalizar_espacios | minimo; un espacio interno multiple casi nunca es intencional en este dataset |
| DIRECTOR | caracteres invisibles (nbsp, tabs, saltos de linea, etc.) | quitar_invisibles | bajo: se reemplazan por un espacio normal, nunca se borran, asi que no pegan palabras que estaban separadas |
| DIRECTOR | faltantes representados de formas distintas (celda vacia, \xa0, N/A, NULL, ---, etc.) | normalizar_faltantes | un centinela puede ser ambiguo: '0' esta en la lista de centinelas (detectores.CENTINELAS) pero podria ser un valor real en una variable numerica que no sea TELEFONO/CODIGO; revisar antes de aplicar fuera de esas dos |
| DISTRITO | espacios al inicio/final o multiples espacios internos | normalizar_espacios | minimo; un espacio interno multiple casi nunca es intencional en este dataset |
| DISTRITO | caracteres invisibles (nbsp, tabs, saltos de linea, etc.) | quitar_invisibles | bajo: se reemplazan por un espacio normal, nunca se borran, asi que no pegan palabras que estaban separadas |
| DISTRITO | faltantes representados de formas distintas (celda vacia, \xa0, N/A, NULL, ---, etc.) | normalizar_faltantes | un centinela puede ser ambiguo: '0' esta en la lista de centinelas (detectores.CENTINELAS) pero podria ser un valor real en una variable numerica que no sea TELEFONO/CODIGO; revisar antes de aplicar fuera de esas dos |
| ESTABLECIMIENTO | puntuacion sobrante al inicio o final | quitar_puntuacion_borde | bajo, pero depende de que los delimitadores desbalanceados ya se hayan revisado; si no, se puede dejar un parentesis o comilla sin su cierre |
| ESTABLECIMIENTO | mayusculas inconsistentes | normalizar_mayusculas | mas alto que en las categoricas: son nombres propios (ej. ESTABLECIMIENTO), y el enunciado pide conservar la ortografia; mayusculizar no cambia letras pero SI pierde cualquier estilizacion de mayusculas que fuera intencional (poco probable, pero no se puede verificar solo con la columna) |
| ESTABLECIMIENTO | espacios al inicio/final o multiples espacios internos | normalizar_espacios | minimo; un espacio interno multiple casi nunca es intencional en este dataset |
| ESTABLECIMIENTO | caracteres invisibles (nbsp, tabs, saltos de linea, etc.) | quitar_invisibles | bajo: se reemplazan por un espacio normal, nunca se borran, asi que no pegan palabras que estaban separadas |
| ESTABLECIMIENTO | posibles typos entre nombres de establecimiento (ver profiler.detectar_typos_establecimiento) | ninguna: marcar para revision manual | dos establecimientos legitimos y distintos pueden tener nombres parecidos (ej. dos sedes de un mismo colegio); fusionarlos sin revisar perderia un registro real |
| ESTABLECIMIENTO | faltantes representados de formas distintas (celda vacia, \xa0, N/A, NULL, ---, etc.) | normalizar_faltantes | un centinela puede ser ambiguo: '0' esta en la lista de centinelas (detectores.CENTINELAS) pero podria ser un valor real en una variable numerica que no sea TELEFONO/CODIGO; revisar antes de aplicar fuera de esas dos |
| JORNADA | mayusculas inconsistentes | normalizar_mayusculas | bajo: son categoricas de dominio cerrado, casi todo el dataset ya viene en mayusculas |
| JORNADA | faltantes representados de formas distintas (celda vacia, \xa0, N/A, NULL, ---, etc.) | normalizar_faltantes | un centinela puede ser ambiguo: '0' esta en la lista de centinelas (detectores.CENTINELAS) pero podria ser un valor real en una variable numerica que no sea TELEFONO/CODIGO; revisar antes de aplicar fuera de esas dos |
| JORNADA | puntuacion sobrante al inicio o final | quitar_puntuacion_borde | bajo, pero depende de que los delimitadores desbalanceados ya se hayan revisado; si no, se puede dejar un parentesis o comilla sin su cierre |
| JORNADA | caracteres invisibles (nbsp, tabs, saltos de linea, etc.) | quitar_invisibles | bajo: se reemplazan por un espacio normal, nunca se borran, asi que no pegan palabras que estaban separadas |
| JORNADA | espacios al inicio/final o multiples espacios internos | normalizar_espacios | minimo; un espacio interno multiple casi nunca es intencional en este dataset |
| MODALIDAD | espacios al inicio/final o multiples espacios internos | normalizar_espacios | minimo; un espacio interno multiple casi nunca es intencional en este dataset |
| MODALIDAD | caracteres invisibles (nbsp, tabs, saltos de linea, etc.) | quitar_invisibles | bajo: se reemplazan por un espacio normal, nunca se borran, asi que no pegan palabras que estaban separadas |
| MODALIDAD | faltantes representados de formas distintas (celda vacia, \xa0, N/A, NULL, ---, etc.) | normalizar_faltantes | un centinela puede ser ambiguo: '0' esta en la lista de centinelas (detectores.CENTINELAS) pero podria ser un valor real en una variable numerica que no sea TELEFONO/CODIGO; revisar antes de aplicar fuera de esas dos |
| MODALIDAD | mayusculas inconsistentes | normalizar_mayusculas | bajo: son categoricas de dominio cerrado, casi todo el dataset ya viene en mayusculas |
| MODALIDAD | puntuacion sobrante al inicio o final | quitar_puntuacion_borde | bajo, pero depende de que los delimitadores desbalanceados ya se hayan revisado; si no, se puede dejar un parentesis o comilla sin su cierre |
| MUNICIPIO | valor fuera del catalogo de su departamento (hay nombres homonimos en mas de un departamento) | ninguna: marcar para revision manual | un mapeo automatico por similitud de texto podria reasignar un municipio homonimo al departamento equivocado |
| MUNICIPIO | puntuacion sobrante al inicio o final | quitar_puntuacion_borde | bajo, pero depende de que los delimitadores desbalanceados ya se hayan revisado; si no, se puede dejar un parentesis o comilla sin su cierre |
| MUNICIPIO | mayusculas inconsistentes | normalizar_mayusculas | bajo: son categoricas de dominio cerrado, casi todo el dataset ya viene en mayusculas |
| MUNICIPIO | caracteres invisibles (nbsp, tabs, saltos de linea, etc.) | quitar_invisibles | bajo: se reemplazan por un espacio normal, nunca se borran, asi que no pegan palabras que estaban separadas |
| MUNICIPIO | espacios al inicio/final o multiples espacios internos | normalizar_espacios | minimo; un espacio interno multiple casi nunca es intencional en este dataset |
| MUNICIPIO | faltantes representados de formas distintas (celda vacia, \xa0, N/A, NULL, ---, etc.) | normalizar_faltantes | un centinela puede ser ambiguo: '0' esta en la lista de centinelas (detectores.CENTINELAS) pero podria ser un valor real en una variable numerica que no sea TELEFONO/CODIGO; revisar antes de aplicar fuera de esas dos |
| NIVEL | mayusculas inconsistentes | normalizar_mayusculas | bajo: son categoricas de dominio cerrado, casi todo el dataset ya viene en mayusculas |
| NIVEL | caracteres invisibles (nbsp, tabs, saltos de linea, etc.) | quitar_invisibles | bajo: se reemplazan por un espacio normal, nunca se borran, asi que no pegan palabras que estaban separadas |
| NIVEL | puntuacion sobrante al inicio o final | quitar_puntuacion_borde | bajo, pero depende de que los delimitadores desbalanceados ya se hayan revisado; si no, se puede dejar un parentesis o comilla sin su cierre |
| NIVEL | faltantes representados de formas distintas (celda vacia, \xa0, N/A, NULL, ---, etc.) | normalizar_faltantes | un centinela puede ser ambiguo: '0' esta en la lista de centinelas (detectores.CENTINELAS) pero podria ser un valor real en una variable numerica que no sea TELEFONO/CODIGO; revisar antes de aplicar fuera de esas dos |
| NIVEL | espacios al inicio/final o multiples espacios internos | normalizar_espacios | minimo; un espacio interno multiple casi nunca es intencional en este dataset |
| PLAN | faltantes representados de formas distintas (celda vacia, \xa0, N/A, NULL, ---, etc.) | normalizar_faltantes | un centinela puede ser ambiguo: '0' esta en la lista de centinelas (detectores.CENTINELAS) pero podria ser un valor real en una variable numerica que no sea TELEFONO/CODIGO; revisar antes de aplicar fuera de esas dos |
| PLAN | puntuacion sobrante al inicio o final | quitar_puntuacion_borde | bajo, pero depende de que los delimitadores desbalanceados ya se hayan revisado; si no, se puede dejar un parentesis o comilla sin su cierre |
| PLAN | caracteres invisibles (nbsp, tabs, saltos de linea, etc.) | quitar_invisibles | bajo: se reemplazan por un espacio normal, nunca se borran, asi que no pegan palabras que estaban separadas |
| PLAN | espacios al inicio/final o multiples espacios internos | normalizar_espacios | minimo; un espacio interno multiple casi nunca es intencional en este dataset |
| PLAN | mayusculas inconsistentes | normalizar_mayusculas | bajo: son categoricas de dominio cerrado, casi todo el dataset ya viene en mayusculas |
| SECTOR | puntuacion sobrante al inicio o final | quitar_puntuacion_borde | bajo, pero depende de que los delimitadores desbalanceados ya se hayan revisado; si no, se puede dejar un parentesis o comilla sin su cierre |
| SECTOR | mayusculas inconsistentes | normalizar_mayusculas | bajo: son categoricas de dominio cerrado, casi todo el dataset ya viene en mayusculas |
| SECTOR | caracteres invisibles (nbsp, tabs, saltos de linea, etc.) | quitar_invisibles | bajo: se reemplazan por un espacio normal, nunca se borran, asi que no pegan palabras que estaban separadas |
| SECTOR | espacios al inicio/final o multiples espacios internos | normalizar_espacios | minimo; un espacio interno multiple casi nunca es intencional en este dataset |
| SECTOR | faltantes representados de formas distintas (celda vacia, \xa0, N/A, NULL, ---, etc.) | normalizar_faltantes | un centinela puede ser ambiguo: '0' esta en la lista de centinelas (detectores.CENTINELAS) pero podria ser un valor real en una variable numerica que no sea TELEFONO/CODIGO; revisar antes de aplicar fuera de esas dos |
| STATUS | mayusculas inconsistentes | normalizar_mayusculas | bajo: son categoricas de dominio cerrado, casi todo el dataset ya viene en mayusculas |
| STATUS | puntuacion sobrante al inicio o final | quitar_puntuacion_borde | bajo, pero depende de que los delimitadores desbalanceados ya se hayan revisado; si no, se puede dejar un parentesis o comilla sin su cierre |
| STATUS | espacios al inicio/final o multiples espacios internos | normalizar_espacios | minimo; un espacio interno multiple casi nunca es intencional en este dataset |
| STATUS | caracteres invisibles (nbsp, tabs, saltos de linea, etc.) | quitar_invisibles | bajo: se reemplazan por un espacio normal, nunca se borran, asi que no pegan palabras que estaban separadas |
| STATUS | faltantes representados de formas distintas (celda vacia, \xa0, N/A, NULL, ---, etc.) | normalizar_faltantes | un centinela puede ser ambiguo: '0' esta en la lista de centinelas (detectores.CENTINELAS) pero podria ser un valor real en una variable numerica que no sea TELEFONO/CODIGO; revisar antes de aplicar fuera de esas dos |
| SUPERVISOR | mayusculas inconsistentes | normalizar_mayusculas | mas alto que en las categoricas: son nombres propios (ej. ESTABLECIMIENTO), y el enunciado pide conservar la ortografia; mayusculizar no cambia letras pero SI pierde cualquier estilizacion de mayusculas que fuera intencional (poco probable, pero no se puede verificar solo con la columna) |
| SUPERVISOR | caracteres invisibles (nbsp, tabs, saltos de linea, etc.) | quitar_invisibles | bajo: se reemplazan por un espacio normal, nunca se borran, asi que no pegan palabras que estaban separadas |
| SUPERVISOR | espacios al inicio/final o multiples espacios internos | normalizar_espacios | minimo; un espacio interno multiple casi nunca es intencional en este dataset |
| SUPERVISOR | faltantes representados de formas distintas (celda vacia, \xa0, N/A, NULL, ---, etc.) | normalizar_faltantes | un centinela puede ser ambiguo: '0' esta en la lista de centinelas (detectores.CENTINELAS) pero podria ser un valor real en una variable numerica que no sea TELEFONO/CODIGO; revisar antes de aplicar fuera de esas dos |
| SUPERVISOR | puntuacion sobrante al inicio o final | quitar_puntuacion_borde | bajo, pero depende de que los delimitadores desbalanceados ya se hayan revisado; si no, se puede dejar un parentesis o comilla sin su cierre |
| TELEFONO | caracteres invisibles (nbsp, tabs, saltos de linea, etc.) | quitar_invisibles | bajo: se reemplazan por un espacio normal, nunca se borran, asi que no pegan palabras que estaban separadas |
| TELEFONO | faltantes representados de formas distintas (celda vacia, \xa0, N/A, NULL, ---, etc.) | normalizar_faltantes | un centinela puede ser ambiguo: '0' esta en la lista de centinelas (detectores.CENTINELAS) pero podria ser un valor real en una variable numerica que no sea TELEFONO/CODIGO; revisar antes de aplicar fuera de esas dos |
| TELEFONO | telefono con mas de un numero en la celda | separar_telefono_multivalor | el 'primer numero' es una convencion arbitraria y podria no ser el principal; el numero descartado tiene que guardarse aparte para no perder informacion, no solo botarse |
| TELEFONO | telefono fuera de formato (no son 8 digitos) | normalizar_telefono | un telefono con una letra de mas ('12345678A') podria quedar en 8 digitos 'validos' por coincidencia sin que el numero real sea correcto; una regla de formato no puede detectar eso |
| TELEFONO | espacios al inicio/final o multiples espacios internos | normalizar_espacios | minimo; un espacio interno multiple casi nunca es intencional en este dataset |

## Como leer `casos_afectados_en_muestra`

Es el número de celdas que la regla tocaría en la muestra probada,
NO en el dataset completo. Antes de aplicar una regla sobre
`raw_files/datos_crudos_completos.csv` hay que volver a correr
`estrategia.py` sobre los datos reales (quitando `N_MUESTRA` o
subiéndolo al total de filas) para tener el número real de registros
afectados.

Detalle de antes/después en `evidencia_muestra.csv`.
