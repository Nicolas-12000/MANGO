# Limpieza de datos

Se etiquetan colas estadísticas y solo se eliminan valores imposibles.

- Filas de entrada: 200
- Filas listas: 200
- Filas eliminadas: 0
- Duplicados exactos: 0
- `customer_id` duplicados: 0
- Nulos: `{'customer_id': 0, 'gender': 0, 'age': 0, 'annual_income_k': 0, 'spending_score': 0}`
- Errores de captura: `{'gender': 0, 'age': 0, 'annual_income_k': 0, 'spending_score': 0}`

## Valla de Tukey (1.5 IQR)

| Variable | Límite inferior | Límite superior | Conteo | customer_id |
|---|---:|---:|---:|---|
| `age` | -1.62 | 79.38 | 0 | [] |
| `annual_income_k` | -13.25 | 132.75 | 2 | [199, 200] |
| `spending_score` | -22.62 | 130.38 | 0 | [] |

## Z modificada de Iglewicz y Hoaglin

Umbral 3.5. Un valor por encima es una cola robusta, no un borrado automático.

## Distancia de Mahalanobis

Alfa 0.975, umbral chi-cuadrado 9.348, filas marcadas: 3.

La nube tiene varios grupos. Una sola elipse gaussiana marca las esquinas de segmentos reales, así que esa marca no saca filas.

## Sensibilidad

Se reentrena sin las colas IQR de las variables del modelo (2 filas). Silueta completa: 0.5547. Sin esas colas: 0.5599. Desplazamiento máximo de centroide, en unidades originales: 1.9126.

Esas colas siguen en el modelo publicado. En ingreso, son clientes reales de la cola alta, no un error de captura.
