"""Taller de redes — Notaría 2 de Cali, 1938-1943.

App pedagógica para Introducción a la Complejidad (Universidad del Valle).
Los estudiantes caracterizan la estructura de la red de transacciones
inmobiliarias y la contrastan con los modelos canónicos (ER, BA, WS,
Configuration).
"""

from pathlib import Path
import pandas as pd
import streamlit as st

from lib.data import load_raw, clean
from lib.network import build_graph, graph_summary, top_actores
from lib.null_models import generar_todos
from lib.metrics import todas_las_metricas, distribucion_grado
from lib.viz import (
    network_html_interactiva,
    degree_dist_hist,
    degree_dist_loglog,
    bar_metricas,
)
from lib.storage import guardar_hipotesis, guardar_reflexion, modo_almacenamiento
import streamlit.components.v1 as components


# ---------- Configuración ----------
st.set_page_config(
    page_title="Taller de redes · Notaría 2 Cali",
    page_icon="🕸️",
    layout="wide",
)

DATA_PATH = Path(__file__).parent / "notaria_2.csv"


@st.cache_data
def cargar_datos():
    return clean(load_raw(DATA_PATH))


@st.cache_data
def grafo_para_rango(año_min: int, año_max: int):
    df = cargar_datos()
    df_f = df[df['año'].between(año_min, año_max)]
    return build_graph(df_f)


@st.cache_data
def grafo_acumulado(año_corte: int):
    df = cargar_datos()
    return build_graph(df[df['año'] <= año_corte])


@st.cache_data
def html_red_rango(año_min: int, año_max: int):
    return network_html_interactiva(grafo_para_rango(año_min, año_max))


@st.cache_data
def html_red_acumulada(año_corte: int):
    return network_html_interactiva(grafo_acumulado(año_corte))


# ---------- Estado de sesión ----------
def init_state():
    defaults = {
        'registrado': False,
        'nombre': '',
        'codigo': '',
        'companeros': '',
        'hipotesis_bloqueada': False,
        'apuesta': {},
        'rango_apostado': None,
        'guardado_destino': None,
        'fila_estudiante': None,
        'reflexion_guardada': False,
        'reflexion': {},
    }
    for k, v in defaults.items():
        st.session_state.setdefault(k, v)


init_state()


# ---------- Pantalla de registro ----------
if not st.session_state.registrado:
    st.title("Taller de redes — Notaría 2 de Cali")
    st.markdown(
        """
Estos son registros reales de compraventas inmobiliarias de la Notaría 2 de
Cali entre 1938 y 1943. Cada actor que compra o vende es un **nodo**; cada
transacción, un **vínculo**. El conjunto forma una **red**.

El taller tiene un objetivo simple: **caracterizar la estructura de esta red**
y **contrastarla con los tres modelos canónicos** de redes complejas
(Erdős–Rényi, Barabási–Albert, Watts–Strogatz). Vas a recorrer 4 actos en
orden. El orden importa porque te vas a comprometer con una hipótesis
antes de ver las métricas.

Antes de empezar, regístrate para que tu profesor pueda revisar tu trabajo.
"""
    )
    with st.form("registro"):
        nombre_in = st.text_input("Nombre completo *", max_chars=120)
        codigo_in = st.text_input("Código Univalle *", max_chars=30)
        companeros_in = st.text_area(
            "Compañeros de grupo (opcional)",
            placeholder="Juan Pérez (2030456), María García (2034567)…",
            help="Si están trabajando en grupo, lista a los demás integrantes.",
            max_chars=400,
        )
        entrar = st.form_submit_button("Entrar", type='primary')
        if entrar:
            if not nombre_in.strip() or not codigo_in.strip():
                st.error("Nombre y código son obligatorios.")
            else:
                st.session_state.nombre = nombre_in.strip()
                st.session_state.codigo = codigo_in.strip()
                st.session_state.companeros = companeros_in.strip()
                st.session_state.registrado = True
                st.rerun()
    st.caption(
        f"Modo de almacenamiento: **{modo_almacenamiento()}**. "
        "En modo `sheets` tu respuesta se guarda en la hoja del curso; "
        "en modo `local` queda solo en este computador (modo desarrollo)."
    )
    st.stop()


# ---------- Datos ----------
df = cargar_datos()
años = sorted(df['año'].unique())


# ---------- Sidebar ----------
with st.sidebar:
    st.markdown(f"**{st.session_state.nombre}**")
    st.caption(f"Código: `{st.session_state.codigo}`")
    if st.session_state.companeros:
        with st.expander("Compañeros de grupo"):
            st.markdown(st.session_state.companeros)
    if st.button("Cerrar sesión", help="Vuelve a la pantalla de registro"):
        for k in ['registrado', 'nombre', 'codigo', 'companeros',
                  'hipotesis_bloqueada', 'apuesta', 'rango_apostado',
                  'guardado_destino', 'fila_estudiante',
                  'reflexion_guardada', 'reflexion']:
            st.session_state.pop(k, None)
        st.rerun()
    st.divider()

    st.markdown("### Filtro temporal")
    rango = st.select_slider(
        "Rango de años a analizar",
        options=años,
        value=(años[0], años[-1]),
    )
    st.caption(
        "Afecta toda la app. Cuando bloquees tu hipótesis, "
        "se evaluará sobre este rango."
    )

    st.divider()
    st.markdown("### Sobre este taller")
    st.markdown(
        "Curso **Introducción a la Complejidad** (Univalle, 2026-I). "
        "Datos: compraventas de la Notaría 2 de Cali, 1938-1943."
    )
    if st.button("Reiniciar hipótesis"):
        for k in ['hipotesis_bloqueada', 'apuesta', 'rango_apostado',
                  'guardado_destino', 'fila_estudiante',
                  'reflexion_guardada', 'reflexion']:
            st.session_state.pop(k, None)
        st.rerun()


df_filt = df[df['año'].between(*rango)]
G = grafo_para_rango(int(rango[0]), int(rango[1]))


# ---------- Header ----------
st.title("Taller de redes — Notaría 2 de Cali")
st.markdown(
    "*El mercado inmobiliario caleño, 1938-1943, como red de transacciones*"
)
st.markdown(
    """
Vas a analizar una red real construida a partir de las compraventas
registradas en la Notaría 2 de Cali. Tu tarea: identificar **qué modelo
de red compleja** describe mejor su estructura.

El taller tiene **4 actos**. El orden importa.
"""
)
st.divider()


# ==================== ACTO 0: LOS DATOS ====================
with st.expander("0. Los datos (opcional)", expanded=False):
    st.markdown(
        "Registros de la Notaría 2 después de limpiar nombres y normalizar "
        "valores. La columna `Negocio` describe el tipo de operación "
        "(compraventa, hipoteca, cancelación) y a veces la ubicación de la "
        "propiedad."
    )
    st.dataframe(
        df_filt[['vendedor', 'comprador', 'valor_num', 'Negocio', 'año']],
        width='stretch',
        height=300,
    )
    c1, c2, c3 = st.columns(3)
    c1.metric("Transacciones", len(df_filt))
    c2.metric("Actores únicos", G.number_of_nodes())
    c3.metric("Años cubiertos", f"{rango[0]}-{rango[1]}")


# ==================== ACTO 1: OBSERVAR ====================
st.header("1. Observa la red")
st.markdown(
    "Cada nodo es un actor (persona o entidad); cada arista, una compraventa. "
    "Examina la estructura **antes de calcular cualquier métrica**."
)

tab_est, tab_evol, tab_top = st.tabs([
    "Red agregada",
    "Evolución temporal",
    "Actores más conectados"
])

with tab_est:
    resumen = graph_summary(G)
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Actores (nodos)", resumen['n_nodos'])
    c2.metric("Vínculos (aristas)", resumen['n_aristas'])
    c3.metric("Componentes", resumen['componentes'])
    c4.metric("Componente mayor", resumen['tamano_gigante'])
    components.html(html_red_rango(int(rango[0]), int(rango[1])), height=640, scrolling=False)
    st.caption(
        "Arrastra nodos, haz zoom con la rueda o usa los botones de "
        "navegación. Tamaño y color = grado. Solo se muestra el nombre de "
        "actores con grado ≥ 3 para no saturar; pasa el mouse sobre un "
        "nodo para ver el resto."
    )

with tab_evol:
    año_corte = st.slider(
        "Mostrar la red acumulada hasta el año:",
        min_value=int(años[0]),
        max_value=int(años[-1]),
        value=int(años[0]),
        key='slider_evol',
    )
    components.html(html_red_acumulada(año_corte), height=640, scrolling=False)
    st.caption(
        f"Red acumulada hasta {año_corte}. Mueve el slider para ver el "
        "crecimiento año a año. Observa si los nuevos actores se enganchan "
        "a los que ya tienen muchos vínculos o si aparecen al azar."
    )

with tab_top:
    top = top_actores(G, k=15)
    df_top = pd.DataFrame(top, columns=['Actor', 'Grado'])
    st.dataframe(df_top, width='stretch', height=400)
    st.caption(
        "Los actores con más vínculos en el rango seleccionado. Familias "
        "presentes en la base: Borrero, Caicedo, Garcés, Zawadzky, "
        "Sinisterra, Eder. También aparecen bancos y sociedades urbanizadoras."
    )

st.divider()


# ==================== ACTO 2: HIPÓTESIS ====================
st.header("2. Formula una hipótesis")
st.markdown(
    "Antes de calcular las métricas, comprométete con una hipótesis sobre "
    "qué modelo describe esta red. Si solo lees los números, tu lectura va "
    "a quedar sesgada por lo que veas; comprometerte primero te obliga a "
    "tomar postura. Una vez bloqueada no podrás cambiarla en esta sesión "
    "(salvo que reinicies)."
)

if st.session_state.hipotesis_bloqueada:
    destino = st.session_state.guardado_destino or "?"
    nota = "hoja del curso" if destino == "sheets" else "archivo local"
    st.success(
        f"Hipótesis bloqueada para el rango "
        f"**{st.session_state.rango_apostado[0]}-{st.session_state.rango_apostado[1]}**. "
        f"Guardada en {nota}. Continúa al Acto 3."
    )
    with st.expander("Ver mi hipótesis"):
        for k, v in st.session_state.apuesta.items():
            st.markdown(f"- **{k}:** {v}")
else:
    with st.form("hipotesis"):
        st.markdown("##### 1. ¿Qué modelo te parece más adecuado?")
        modelo = st.radio(
            "modelo",
            options=[
                "Erdős–Rényi (azar puro: cualquier par de actores tiene la misma probabilidad de transar)",
                "Barabási–Albert (vinculación preferencial: los actores con muchos vínculos atraen más)",
                "Watts–Strogatz (mundo pequeño: clusters muy densos conectados por atajos)",
                "Ninguno: estos datos no caben en los modelos canónicos",
            ],
            index=None,
            label_visibility='collapsed',
        )

        st.markdown("##### 2. ¿Cómo predices que se ve la distribución de grado?")
        grado = st.radio(
            "grado",
            options=[
                "Campana (la mayoría con grado parecido al promedio)",
                "Cola larga (poquísimos muy conectados, muchísimos con 1-2 vínculos)",
                "Uniforme (todos con grado similar)",
            ],
            index=None,
            label_visibility='collapsed',
        )

        st.markdown("##### 3. ¿El coeficiente de clustering será…?")
        clust = st.radio(
            "clust",
            options=[
                "Alto (>0.3) — muchos triángulos: los vecinos de un actor suelen conectarse entre sí",
                "Medio (0.1–0.3)",
                "Bajo (<0.1) — pocos triángulos: la red es más arbórea",
            ],
            index=None,
            label_visibility='collapsed',
        )

        st.markdown("##### 4. Tu razonamiento (1-3 frases)")
        razon = st.text_area(
            "razon",
            placeholder=(
                "Pienso que esto se parece a [modelo] porque la Cali de los 40 "
                "era una sociedad donde…"
            ),
            label_visibility='collapsed',
        )

        submit = st.form_submit_button("Bloquear hipótesis", type='primary')
        if submit:
            if not (modelo and grado and clust):
                st.error("Responde las 3 preguntas de opción múltiple antes de bloquear.")
            else:
                st.session_state.apuesta = {
                    'Modelo elegido': modelo,
                    'Distribución de grado predicha': grado,
                    'Clustering predicho': clust,
                    'Razonamiento': razon or "(sin razonamiento)",
                }
                st.session_state.hipotesis_bloqueada = True
                st.session_state.rango_apostado = tuple(rango)

                metricas_obs = todas_las_metricas(G)
                payload = {
                    'nombre': st.session_state.nombre,
                    'codigo': st.session_state.codigo,
                    'companeros': st.session_state.companeros,
                    'rango_min': int(rango[0]),
                    'rango_max': int(rango[1]),
                    'modelo': modelo,
                    'distribucion': grado,
                    'clustering': clust,
                    'razonamiento': razon or '',
                    'n_nodos': metricas_obs['n_nodos'],
                    'n_aristas': metricas_obs['n_aristas'],
                    'clustering_obs': metricas_obs['clustering'],
                    'asortatividad_obs': metricas_obs['asortatividad'],
                    'camino_promedio_obs': metricas_obs['camino_promedio'],
                }
                ok, err, destino, row = guardar_hipotesis(payload)
                st.session_state.guardado_destino = destino
                st.session_state.fila_estudiante = row
                if not ok:
                    st.warning(
                        f"No se pudo escribir en la hoja del curso "
                        f"({err}). Quedó guardada localmente. Avísale a tu profe."
                    )
                st.rerun()

st.divider()


# ==================== ACTO 3: COMPARACIÓN CON MODELOS NULOS ====================
st.header("3. Métricas y comparación con modelos nulos")

if not st.session_state.hipotesis_bloqueada:
    st.warning("Bloquea tu hipótesis (Acto 2) para desbloquear este acto.")
else:
    st.markdown(
        """
##### ¿Qué estás viendo?

Voy a mostrarte **tu red** junto a cuatro **redes nulas** generadas con el
mismo número de nodos y aproximadamente el mismo número de aristas. Cada
una representa una hipótesis distinta sobre el mecanismo que generó la
estructura:

- **Erdős–Rényi (ER)** — cada par de actores tiene la misma probabilidad de
  estar conectado. Si tu red se parece a esta, **no hay estructura más allá
  del azar**.
- **Barabási–Albert (BA)** — los actores con muchos vínculos atraen
  proporcionalmente más vínculos nuevos. Es la red de **acumulación de
  poder** o "los ricos se hacen más ricos en conexiones".
- **Watts–Strogatz (WS)** — clusters densos donde casi todos se conocen
  entre sí, conectados por algunos atajos. Es la red de **mundo pequeño**.
- **Configuration model** — preserva exactamente la **distribución de
  grado** de tu red pero recablea al azar. Sirve para preguntar: ¿qué de
  mi estructura se explica solo por la distribución de grado, y qué
  requiere algo más?

Compara cada métrica de la red **Observada** contra los cuatro modelos.
Donde se parezca a uno de ellos, esa es una pista sobre el mecanismo
generador. Donde no se parezca a ninguno, hay algo histórico que los
modelos no capturan.
"""
    )

    with st.spinner("Generando modelos nulos comparables…"):
        nulos = generar_todos(G)

    redes_a_comparar = {'Observada': G, **nulos}
    rows = []
    for nombre, g in redes_a_comparar.items():
        m = todas_las_metricas(g)
        m['red'] = nombre
        rows.append(m)
    df_metricas = pd.DataFrame(rows)
    cols = ['red', 'n_nodos', 'n_aristas', 'grado_promedio', 'grado_maximo',
            'clustering', 'camino_promedio', 'asortatividad']
    df_metricas = df_metricas[cols]

    st.subheader("Tabla comparativa")
    st.dataframe(
        df_metricas.style.format({
            'grado_promedio': '{:.2f}',
            'clustering': '{:.3f}',
            'camino_promedio': '{:.2f}',
            'asortatividad': '{:.3f}',
        }),
        width='stretch',
    )

    with st.expander("Cómo leer cada métrica", expanded=True):
        st.markdown(
            """
- **Grado promedio** — número promedio de vínculos por actor. Es igual entre
  ER y la red observada por construcción del modelo.
- **Grado máximo** — el actor más conectado. Si es muy alto comparado con el
  promedio (por ejemplo, 10× o más), es señal de la presencia de **hubs** y
  apunta a BA.
- **Clustering** — probabilidad de que dos vecinos de un mismo nodo estén
  conectados entre sí. **Alto** ≈ red de "amigos de amigos" (élites,
  WS). **Bajo** ≈ red arbórea o aleatoria. En esta base es muy bajo porque
  cada transacción suele ser una arista aislada.
- **Camino promedio** — número promedio de saltos entre dos actores
  cualesquiera del **componente gigante**. **Corto** ≈ mundo pequeño;
  **largo** ≈ red fragmentada o lineal.
- **Asortatividad por grado** — ¿con quién se conectan los hubs?
  - **> 0**: hubs con hubs ("los ricos se conectan con los ricos") — élite
    cerrada y endogámica.
  - **< 0**: hubs con periferia (forma de estrella) — patrón típico de BA y
    de intermediarios financieros.
  - **≈ 0**: indiferente al grado.
"""
        )

    st.subheader("Distribución de grado")
    use_loglog = st.toggle(
        "Escala log-log (para detectar leyes de potencia)",
        value=False,
    )
    degs_dict = {nombre: distribucion_grado(g) for nombre, g in redes_a_comparar.items()}
    if use_loglog:
        st.plotly_chart(degree_dist_loglog(degs_dict), width='stretch')
    else:
        st.plotly_chart(degree_dist_hist(degs_dict, normalizar=True),
                        width='stretch')

    with st.expander("Cómo leer las distribuciones", expanded=True):
        st.markdown(
            """
El histograma muestra **cuántos actores tienen cada cantidad de vínculos**.

- **ER** produce una **distribución Poisson**: campana estrecha centrada en
  el grado promedio. Casi nadie está muy por encima o por debajo.
- **BA** produce una **ley de potencia**: cola larga — pocos hubs muy
  conectados y una mayoría con grado 1-2. En **escala log-log** una ley de
  potencia aparece como una **línea recta**.
- **WS** produce una distribución concentrada alrededor de *k* (el número
  inicial de vecinos del modelo).
- **Configuration model** reproduce exactamente la distribución observada,
  porque la fija como input.

**Cómo decidir:** activa el toggle log-log. Si los puntos de tu red caen
sobre una recta, hay vinculación preferencial. Si forman una campana, es
más cercano al azar.
"""
        )

    st.subheader("Comparaciones individuales")
    c1, c2 = st.columns(2)
    with c1:
        st.plotly_chart(bar_metricas(rows, 'clustering'), width='stretch')
    with c2:
        st.plotly_chart(bar_metricas(rows, 'asortatividad'), width='stretch')

    st.markdown("---")
    st.markdown("##### Tu hipótesis del Acto 2 (para que la tengas a la vista)")
    for k, v in st.session_state.apuesta.items():
        st.markdown(f"- **{k}:** {v}")

st.divider()


# ==================== ACTO 4: INTERPRETACIÓN ====================
st.header("4. Interpretación")

if not st.session_state.hipotesis_bloqueada:
    st.warning("Disponible después de bloquear tu hipótesis (Acto 2).")
elif st.session_state.reflexion_guardada:
    destino = st.session_state.guardado_destino or "?"
    nota = "hoja del curso" if destino == "sheets" else "archivo local"
    st.success(f"Reflexión guardada en {nota}.")
    with st.expander("Ver mi reflexión", expanded=True):
        for k, v in st.session_state.reflexion.items():
            st.markdown(f"**{k}**")
            st.markdown(f"> {v}")
else:
    st.markdown(
        "Revisa la tabla y los gráficos del Acto 3. Responde abajo. Tus "
        "respuestas se guardan junto a tu hipótesis."
    )

    st.markdown("**Pistas conceptuales** — útiles para conectar lo que ves con el contexto histórico:")
    st.markdown(
        """
- **Padgett & McLean 2006**, *Organizational Invention and Elite
  Transformation*. Los Medici de Florencia ocupaban una posición de
  **broker** entre clusters desconectados.
- **Londoño 2019**, *Optimismo, tesón y labor. Jorge Garcés Borrero
  1899–1944*. Garcés Borrero como nodo articulador del Valle azucarero y
  financiero.
- **Collins 2019** — la burguesía azucarera vallecaucana se consolida en
  los 30-40 mediante matrimonios y sociedades.
- **Sáenz 2022**, *Élite, orden y conflicto. Cali 1910-1953*. La élite
  caleña como red densa pero excluyente.
- **Arroyo 2014** — prácticas empresariales en el Valle 1900-1940.
"""
    )

    with st.form("form_reflexion"):
        st.markdown("##### 1. ¿Tu hipótesis del Acto 2 acertó?")
        acerto = st.radio(
            "acerto",
            options=[
                "Sí, completamente",
                "Parcialmente",
                "No",
            ],
            index=None,
            label_visibility='collapsed',
        )

        st.markdown(
            "##### 2. Mecanismo histórico"
        )
        st.caption(
            "¿Qué historia explica el patrón que observas? Si la red se "
            "parece a BA, ¿por qué unos pocos actores acumulan tantos "
            "vínculos (clase, capital, familia, posición política)? Si se "
            "parece a WS, ¿qué clusters identificas? Si no se parece a "
            "ninguno, ¿qué describe mejor lo que ves?"
        )
        mecanismo = st.text_area(
            "mecanismo",
            placeholder="La red se parece a… porque en la Cali de esos años…",
            label_visibility='collapsed',
            height=160,
        )

        st.markdown("##### 3. ¿Qué le falta a los modelos canónicos?")
        st.caption(
            "Pista: piensa en lo que estos modelos NO modelan. ¿Tiempo? "
            "¿Heterogeneidad de actores (bancos vs. personas naturales)? "
            "¿Tipos de transacción (compraventa, hipoteca, cancelación)? "
            "¿El hecho de que esto es solo UNA notaría?"
        )
        modelo_falta = st.text_area(
            "modelo_falta",
            placeholder="Un modelo adecuado para Cali 1938-1943 debería incluir…",
            label_visibility='collapsed',
            height=160,
        )

        submit_ref = st.form_submit_button("Guardar reflexión", type='primary')
        if submit_ref:
            if not (acerto and mecanismo.strip() and modelo_falta.strip()):
                st.error("Responde las 3 preguntas antes de guardar.")
            else:
                st.session_state.reflexion = {
                    '¿Acertaste?': acerto,
                    'Mecanismo histórico': mecanismo.strip(),
                    'Qué le falta a los modelos': modelo_falta.strip(),
                }
                ok, err, destino = guardar_reflexion(
                    st.session_state.fila_estudiante,
                    {
                        'acerto': acerto,
                        'mecanismo': mecanismo.strip(),
                        'modelo_falta': modelo_falta.strip(),
                    }
                )
                st.session_state.reflexion_guardada = True
                if not ok:
                    st.warning(
                        f"No se pudo actualizar la hoja del curso ({err}). "
                        "Quedó en local. Avísale a tu profe."
                    )
                st.rerun()
