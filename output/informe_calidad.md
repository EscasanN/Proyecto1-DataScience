# Informe de calidad de los datos

Comparación del conjunto de datos
antes y después del proceso de limpieza.

## Métricas

| Métrica | Antes | Después |
|---|---:|---:|
| Registros | 11867 | 11867 |
| Variables | 17 | 18 |
| Valores faltantes | 3,826 (1.90%) | 16,075 (7.53%) |
| Variables con NA | 6 | 7 |
| Duplicados exactos | 0 | 0 |
| Posibles duplicados | 1487 | 1487 |
| Variables con formato inconsistente | 6 | 6 |
| Variables con tipo incorrecto | 0 | 0 |
| Categorías inconsistentes | 2716 | 2176 |

## Registro de transformaciones

| Variable | Problema detectado | Transformación | Registros afectados |
|---|---|---|---:|
| DIRECCION | espacios al inicio/final o multiples espacios internos | normalizar_espacios | 485 |
| DIRECCION | faltantes representados de formas distintas (celda vacia, \xa0, N/A, NULL, ---, etc.) | normalizar_faltantes | 89 |
| DIRECCION | mayusculas inconsistentes | normalizar_mayusculas | 10 |
| DIRECCION | puntuacion sobrante al inicio o final | quitar_puntuacion_borde | 121 |
| DIRECTOR | espacios al inicio/final o multiples espacios internos | normalizar_espacios | 1082 |
| DIRECTOR | faltantes representados de formas distintas (celda vacia, \xa0, N/A, NULL, ---, etc.) | normalizar_faltantes | 2146 |
| DIRECTOR | puntuacion sobrante al inicio o final | quitar_puntuacion_borde | 7 |
| DISTRITO | faltantes representados de formas distintas (celda vacia, \xa0, N/A, NULL, ---, etc.) | normalizar_faltantes | 532 |
| ESTABLECIMIENTO | espacios al inicio/final o multiples espacios internos | normalizar_espacios | 1395 |
| ESTABLECIMIENTO | faltantes representados de formas distintas (celda vacia, \xa0, N/A, NULL, ---, etc.) | normalizar_faltantes | 5 |
| ESTABLECIMIENTO | puntuacion sobrante al inicio o final | quitar_puntuacion_borde | 397 |
| SUPERVISOR | caracteres invisibles (nbsp, tabs, saltos de linea, etc.) | quitar_invisibles | 4 |
| SUPERVISOR | espacios al inicio/final o multiples espacios internos | normalizar_espacios | 133 |
| SUPERVISOR | faltantes representados de formas distintas (celda vacia, \xa0, N/A, NULL, ---, etc.) | normalizar_faltantes | 538 |
| SUPERVISOR | puntuacion sobrante al inicio o final | quitar_puntuacion_borde | 25 |
| TELEFONO | espacios al inicio/final o multiples espacios internos | normalizar_espacios | 8 |
| TELEFONO | faltantes representados de formas distintas (celda vacia, \xa0, N/A, NULL, ---, etc.) | normalizar_faltantes | 946 |
| TELEFONO | telefono con mas de un numero en la celda | separar_telefono_multivalor | 132 |
| TELEFONO | telefono fuera de formato (no son 8 digitos) | normalizar_telefono | 3 |

### Resumen de transformaciones

**Total de registros afectados:** 8058

## Observaciones

- Todas las métricas fueron calculadas utilizando las funciones del proyecto.
- Los duplicados parciales fueron detectados mediante RapidFuzz.
- Ningún registro fue eliminado automáticamente.
- Todas las transformaciones corresponden al pipeline de limpieza ejecutado por `main.py`.
