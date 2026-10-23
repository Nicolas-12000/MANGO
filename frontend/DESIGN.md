---
version: alpha
name: Mango
description: Identidad visual de Mango — pulpa, cáscara y hoja para leer segmentos de clientes.
colors:
  primary: "#2C1210"
  on-primary: "#FFF6EE"
  secondary: "#5C3A2E"
  tertiary: "#C2410C"
  on-tertiary: "#FFFFFF"
  tertiary-container: "#9A3412"
  neutral: "#FFF4EA"
  surface: "#FFFBF7"
  outline: "#F0D9C8"
  mark: "#E09F3E"
  positive: "#3F6B2A"
  mora: "#9B2335"
  error: "#9F1239"
  high-value: "#C2410C"
  potential: "#9A3412"
  average: "#C4841D"
  low-value: "#6B2D3C"
  budget: "#D4673A"
typography:
  display:
    fontFamily: Fraunces
    fontSize: 2.25rem
    fontWeight: 600
    lineHeight: 1.05
    letterSpacing: -0.02em
  title:
    fontFamily: Fraunces
    fontSize: 1.5rem
    fontWeight: 600
    lineHeight: 1.15
    letterSpacing: -0.01em
  heading:
    fontFamily: IBM Plex Sans
    fontSize: 1rem
    fontWeight: 600
    lineHeight: 1.4
  body-md:
    fontFamily: IBM Plex Sans
    fontSize: 1rem
    fontWeight: 400
    lineHeight: 1.6
  body-sm:
    fontFamily: IBM Plex Sans
    fontSize: 0.875rem
    fontWeight: 400
    lineHeight: 1.5
  label-caps:
    fontFamily: IBM Plex Mono
    fontSize: 0.6875rem
    fontWeight: 500
    lineHeight: 1.2
    letterSpacing: 0.08em
  num-xl:
    fontFamily: IBM Plex Mono
    fontSize: 2.5rem
    fontWeight: 500
    lineHeight: 1
    letterSpacing: -0.02em
    fontFeature: '"tnum"'
  num-md:
    fontFamily: IBM Plex Mono
    fontSize: 1rem
    fontWeight: 400
    lineHeight: 1.4
    fontFeature: '"tnum"'
rounded:
  sm: 4px
  md: 8px
  lg: 14px
  full: 9999px
spacing:
  xs: 4px
  sm: 8px
  md: 16px
  lg: 24px
  xl: 40px
components:
  page:
    backgroundColor: "{colors.neutral}"
    textColor: "{colors.primary}"
    typography: "{typography.body-md}"
  card:
    backgroundColor: "{colors.surface}"
    textColor: "{colors.primary}"
    rounded: "{rounded.lg}"
    padding: 20px
  button-primary:
    backgroundColor: "{colors.tertiary}"
    textColor: "{colors.on-tertiary}"
    typography: "{typography.heading}"
    rounded: "{rounded.md}"
    padding: 12px
    height: 48px
  button-primary-hover:
    backgroundColor: "{colors.tertiary-container}"
    textColor: "{colors.on-tertiary}"
  input:
    backgroundColor: "{colors.surface}"
    textColor: "{colors.primary}"
    typography: "{typography.num-md}"
    rounded: "{rounded.md}"
    padding: 12px
    height: 48px
---

## Overview

**Un mango partido, no un tablero genérico.** La interfaz enseña los cinco segmentos
del centro comercial: pulpa para lo que se mira, cáscara para lo que se hace, hoja
para lo que está sano. Números en mono, títulos en serif, fondo de papel cálido.

Mobile first, desde 320 px. La profundidad se marca con borde y superficie, no con sombras.

## Colors

**Cáscara, pulpa y hoja.** Rojos y naranjas sobre papel. El verde aparece solo como
hoja: silueta alta y estado en línea.

- **Primary (#2C1210):** tinta. Títulos y texto.
- **Secondary (#5C3A2E):** metadatos. Pasa AA sobre neutral y surface.
- **Tertiary (#C2410C):** la única acción. Hover en **#9A3412**.
- **Neutral (#FFF4EA):** fondo.
- **Surface (#FFFBF7):** tarjetas y campos.
- **Outline (#F0D9C8):** bordes. Nunca texto.
- **Mark (#E09F3E):** pulpa. Fondo o trazo, nunca texto sobre claro.
- **Positive (#3F6B2A):** hoja. Estado en línea.
- **Mora (#9B2335) y low-value (#6B2D3C):** el segmento de bajo valor.
- **Error (#9F1239):** validación, siempre con mensaje.

Los cinco segmentos usan `high-value`, `potential`, `average`, `low-value` y `budget`.
Son relleno de puntos, no texto pequeño sobre el papel.

## Typography

- **Fraunces** para el nombre y los títulos.
- **IBM Plex Sans** para lectura.
- **IBM Plex Mono** para todo número, con cifras tabulares.

Los campos numéricos quedan en 16 px para que iOS no haga zoom al enfocar.

## Layout

Base de 4 px. Una columna en el teléfono, márgenes de 16 px. Desde `lg` el gráfico de
segmentos y el formulario van lado a lado. El contenedor se queda en 1152 px.

## Do's and Don'ts

- **Do** mostrar K y la silueta junto al gráfico.
- **Do** escribir la interfaz en español y los identificadores del modelo en inglés.
- **Do** avisar si el cliente nuevo sale del rango de entrenamiento.
- **Don't** usar la pulpa como color de botón. El botón es la cáscara.
- **Don't** separar tarjetas con sombras.
