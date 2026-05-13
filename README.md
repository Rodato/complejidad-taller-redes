# Taller de redes — Notaría 2 de Cali

App pedagógica diseñada y desarrollada por **Daniel Otero** para el curso **Introducción a la Complejidad** (Universidad del Valle, 2026-I).

## ¿Qué hace?

El estudiante asume el rol de un detective histórico y caracteriza la red de compraventas inmobiliarias registradas en la **Notaría 2 de Cali entre 1938 y 1943** (≈260 transacciones). En cuatro actos:

1. **Conocer el expediente** — explorar los datos crudos.
2. **Apostar** — antes de ver las métricas, el estudiante elige qué modelo de red describe mejor las transacciones: **Erdős–Rényi**, **Barabási–Albert**, **Watts–Strogatz** o **Configuration**, y registra su razonamiento.
3. **Comparar contra el dato real** — la app calcula la red observada y la contrasta con los cuatro modelos nulos.
4. **Reflexionar** — el estudiante revisa si acertó y propone qué mecanismo histórico y qué modelo faltaría.

Las respuestas se guardan en una hoja de Google Sheets compartida con el docente.

## Dos apps desde el mismo repo

| Entry point | Para quién | Qué muestra |
|---|---|---|
| `streamlit_app.py` | Estudiantes | Los 4 actos del taller, una instancia por estudiante. |
| `dashboard.py` | Docente | Vista agregada de la clase (apuestas, aciertos, predicciones) y ficha individual por estudiante para que sustente al frente. |

Ambos despliegues leen la misma Sheet.

## Datos

`notaria_2.csv` — registros de la Notaría 2 con `vendedor`, `comprador`, `Valor`, `Negocio`, `fecha`. Los datos vienen con la rugosidad típica de archivos históricos (mayúsculas inconsistentes, valores mixtos, falta el año 1942). La red resultante es muy fragmentada — eso es **parte del aprendizaje**, no un defecto: lleva al estudiante a preguntarse qué le falta a la fuente.

Aparecen familias y actores centrales para la historia económica caleña: Caicedo, Garcés Borrero, Zawadzky, Sinisterra, Eder, Banco Central Hipotecario, Sociedad Urbanizadora Colombiana.

## Estructura del código

```
streamlit_app.py        ← app de estudiantes (entry point 1)
dashboard.py            ← dashboard docente   (entry point 2)
notaria_2.csv           ← datos
lib/
  data.py               ← carga y limpieza
  network.py            ← construcción del grafo
  null_models.py        ← ER, BA, WS, Configuration
  metrics.py            ← clustering, asortatividad, camino promedio, distribución de grado
  viz.py                ← red interactiva (pyvis) y distribuciones
  storage.py            ← persistencia en Google Sheets + fallback local
```

## Cómo correrlo localmente

Requiere Python 3.11+.

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt

# Configura credenciales (ver .streamlit/secrets.toml.example)
cp .streamlit/secrets.toml.example .streamlit/secrets.toml
# Edita el archivo con tu service account y la URL de tu Sheet

# App de estudiantes
streamlit run streamlit_app.py

# Dashboard docente (en otro puerto)
streamlit run dashboard.py --server.port=8502
```

Sin credenciales de Google, la app guarda en `respuestas_local.csv` y sigue funcionando para pruebas.

## Contexto del curso

Forma parte del **Grupo B (red inmobiliaria)** del curso. Dos grupos paralelos trabajan con perspectivas distintas sobre la misma pregunta —cómo emerge Cali como espacio urbano entre 1900 y 1980—: Grupo A (red social/élites) y Grupo C (red urbana/espacial).

## Créditos

- **Autor, diseño pedagógico y desarrollo:** Daniel Otero
- **Programación en pareja:** Claude (Anthropic)
- **Chispa inicial:** Boris Salazar — propuso modelar la red con Barabási–Albert; sobre esa semilla Daniel construyó el taller completo de cuatro actos, los cuatro modelos nulos comparados y las dos apps.
- **Curso:** Introducción a la Complejidad, Departamento de Economía, Universidad del Valle, 2026-I
