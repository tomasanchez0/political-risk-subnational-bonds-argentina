# Volatilidad Electoral y Bonos Soberanos y Provinciales en Argentina

Este repositorio contiene un pipeline reproducible para analizar el comportamiento de la volatilidad de bonos soberanos (GD30) y bonos provinciales argentinos en torno a períodos electorales.

El objetivo es comparar dinámicas de volatilidad entre el benchmark soberano y el promedio de bonos provinciales, así como estimar un modelo panel con efectos fijos.

---

## Estructura del Proyecto

volatilidad-electoral-bonos/
│
├── data/
│   └── raw/                   # Archivos de datos en formato .xlsx
│
├── src/
│   ├── data_processing.py     # Construcción del panel y transformación a USD
│   ├── event_windows.py       # Generación de ventanas electorales
│   ├── modeling.py            # Estimación econométrica (PanelOLS)
│   └── plotting.py            # Módulo de visualización
│
├── main.py                    # Ejecuta el pipeline completo
├── requirements.txt
└── README.md

---

## Metodología

El proceso consiste en:

1. Conversión de precios de bonos a USD.
2. Cálculo de retornos logarítmicos.
3. Estimación de volatilidad rolling anualizada.
4. Construcción de ventanas electorales.
5. Comparación entre:
   - GD30 (bono soberano)
   - Promedio de bonos provinciales
6. Estimación de modelo panel con efectos fijos por entidad.

La volatilidad utilizada en los gráficos se suaviza mediante una media móvil de 30 días.

La anualización se realiza asumiendo 252 días hábiles.

---

## Cómo Ejecutar

Clonar el repositorio:

git clone <https://github.com/tomasanchez0/political-risk-subnational-bonds-argentina>

cd volatilidad-electoral-bonos

Instalar dependencias:

pip install -r requirements.txt

Ejecutar el análisis completo:

python main.py

---

## Resultados Generados

El script produce:

- Gráfico comparativo de volatilidad suavizada (GD30 vs promedio provincial)
- Ratio de volatilidad Provincial / GD30
- Dinámica individual de cada bono
- Resultados del modelo panel impresos en consola

---

## Datos

Los archivos de datos deben ubicarse en:

data/raw/

Los datos utilizados son de carácter público.

---

## Notas Técnicas

- La volatilidad se calcula como desvío estándar rolling de retornos logarítmicos.
- La estimación econométrica se realiza con `PanelOLS`.
- El proyecto está estructurado modularmente para garantizar reproducibilidad.