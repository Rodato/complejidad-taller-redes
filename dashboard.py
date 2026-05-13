"""Dashboard docente — visualización en vivo de las respuestas de los estudiantes.

Lee la misma hoja de Google Sheets que `streamlit_app.py` y muestra las
apuestas, predicciones y reflexiones de la clase de un vistazo, para
exponer resultados durante la sesión.

Lanzar con:
    streamlit run dashboard.py
"""

import pandas as pd
import streamlit as st

from lib.storage import leer_respuestas, modo_almacenamiento


st.set_page_config(
    page_title="Dashboard · Taller Notaría 2",
    page_icon="📊",
    layout="wide",
)

ORDEN_MODELOS = ["Erdős–Rényi", "Barabási–Albert", "Watts–Strogatz", "Configuration"]
ORDEN_ACIERTO = ["Sí", "Parcialmente", "No"]


@st.cache_data(ttl=10)
def cargar(_nonce: int):
    return leer_respuestas()


# ---------- Header ----------
col_t, col_btn = st.columns([4, 1])
with col_t:
    st.title("📊 Resultados de la clase")
    st.caption(f"Origen: **{modo_almacenamiento()}**  ·  cache 10s  ·  pulsa *Recargar* para forzar")
with col_btn:
    if st.button("🔄 Recargar", use_container_width=True):
        st.cache_data.clear()
        st.rerun()

df, origen = cargar(0)

if df.empty:
    st.warning("Aún no hay respuestas registradas.")
    st.stop()

# Normalizar tipos numéricos (vienen como string desde Sheets)
for col in ["rango_min", "rango_max", "n_nodos", "n_aristas",
            "clustering_obs", "asortatividad_obs", "camino_promedio_obs"]:
    if col in df.columns:
        df[col] = pd.to_numeric(df[col], errors="coerce")

n_total = len(df)
n_reflexion = int((df["acerto"].astype(str).str.strip() != "").sum()) if "acerto" in df else 0

# ---------- Selector de estudiante ----------
TODOS = "— Toda la clase —"

def _etiqueta_estudiante(row) -> str:
    nombre = (row.get("nombre", "") or "").strip() or "(sin nombre)"
    codigo = (row.get("codigo", "") or "").strip()
    return f"{nombre} · {codigo}" if codigo else nombre

df = df.reset_index(drop=True)
df["_etiqueta"] = df.apply(_etiqueta_estudiante, axis=1)
# Si hay nombres duplicados, desambiguar con timestamp para no perder filas
if df["_etiqueta"].duplicated().any():
    df["_etiqueta"] = df["_etiqueta"] + "  (" + df["timestamp"].astype(str) + ")"

etiquetas = [TODOS] + df["_etiqueta"].tolist()
seleccion = st.selectbox("👤 Estudiante", etiquetas, index=0)

if seleccion != TODOS:
    fila = df.loc[df["_etiqueta"] == seleccion].iloc[0]
    nombre = (fila.get("nombre", "") or "").strip() or "(sin nombre)"
    codigo = (fila.get("codigo", "") or "").strip()
    companeros = (fila.get("companeros", "") or "").strip()

    st.header(f"🧑‍🎓 {nombre}")
    meta = []
    if codigo:
        meta.append(f"código `{codigo}`")
    if companeros:
        meta.append(f"con: {companeros}")
    if meta:
        st.caption(" · ".join(meta))

    # --- Acto 2: hipótesis ---
    st.subheader("🎲 Acto 2 — Su apuesta")
    a, b, c = st.columns(3)
    a.metric("Modelo apostado", (fila.get("modelo_apostado", "") or "—"))
    b.metric("Distribución predicha", (fila.get("distribucion_predicha", "") or "—"))
    c.metric("Clustering predicho", (fila.get("clustering_predicho", "") or "—"))

    rmin = fila.get("rango_min", "")
    rmax = fila.get("rango_max", "")
    if pd.notna(rmin) or pd.notna(rmax):
        rmin_s = "?" if pd.isna(rmin) else rmin
        rmax_s = "?" if pd.isna(rmax) else rmax
        st.markdown(f"**Rango de exponente predicho:** {rmin_s} – {rmax_s}")

    razon = (fila.get("razonamiento", "") or "").strip()
    if razon:
        st.markdown("**Razonamiento antes de ver las métricas:**")
        st.info(razon)

    # --- Métricas que vio ---
    st.subheader("📐 Métricas observadas que se le mostraron")
    m1, m2, m3 = st.columns(3)
    m1.metric("Nodos", fila.get("n_nodos", "—"))
    m1.metric("Aristas", fila.get("n_aristas", "—"))
    clu = fila.get("clustering_obs", float("nan"))
    aso = fila.get("asortatividad_obs", float("nan"))
    cam = fila.get("camino_promedio_obs", float("nan"))
    m2.metric("Clustering", "—" if pd.isna(clu) else f"{clu:.3f}")
    m2.metric("Asortatividad", "—" if pd.isna(aso) else f"{aso:.3f}")
    m3.metric("Camino promedio", "—" if pd.isna(cam) else f"{cam:.2f}")

    # --- Acto 4: reflexión ---
    acerto = (fila.get("acerto", "") or "").strip()
    mec = (fila.get("mecanismo_historico", "") or "").strip()
    falta = (fila.get("modelo_falta", "") or "").strip()
    if acerto or mec or falta:
        st.subheader("🔁 Acto 4 — Su reflexión final")
        if acerto:
            color = {"Sí": "success", "Parcialmente": "warning", "No": "error"}.get(acerto, "info")
            getattr(st, color)(f"**¿Acertó?** {acerto}")
        if mec:
            st.markdown("**Mecanismo histórico propuesto:**")
            st.markdown(f"> {mec}")
        if falta:
            st.markdown("**¿Qué modelo falta?**")
            st.markdown(f"> {falta}")
    else:
        st.info("Aún no ha completado el Acto 4 (reflexión).")

    st.stop()

# ---------- Vista de toda la clase ----------
c1, c2, c3 = st.columns(3)
c1.metric("Respuestas (Acto 2)", n_total)
c2.metric("Reflexiones (Acto 4)", n_reflexion)
c3.metric("Pendientes de cerrar", n_total - n_reflexion)

st.divider()

# ---------- Apuestas por modelo ----------
st.subheader("🎲 ¿Qué modelo apostó la clase?")
serie_modelo = (
    df["modelo_apostado"].fillna("").replace("", "(sin responder)").value_counts()
)
# Reordenar dejando los modelos canónicos primero
orden = [m for m in ORDEN_MODELOS if m in serie_modelo.index] + \
        [m for m in serie_modelo.index if m not in ORDEN_MODELOS]
st.bar_chart(serie_modelo.reindex(orden), horizontal=True)

# ---------- Acertaron? ----------
if n_reflexion:
    st.subheader("🎯 ¿Acertaron?")
    serie_acierto = df["acerto"].replace("", pd.NA).dropna().value_counts()
    orden_a = [a for a in ORDEN_ACIERTO if a in serie_acierto.index] + \
              [a for a in serie_acierto.index if a not in ORDEN_ACIERTO]
    st.bar_chart(serie_acierto.reindex(orden_a))

st.divider()

# ---------- Predicciones cualitativas ----------
st.subheader("🔮 Predicciones cualitativas")
cdist, cclu = st.columns(2)
with cdist:
    st.markdown("**Distribución de grado**")
    s = df["distribucion_predicha"].fillna("").replace("", "(sin responder)").value_counts()
    st.bar_chart(s)
with cclu:
    st.markdown("**Clustering esperado**")
    s = df["clustering_predicho"].fillna("").replace("", "(sin responder)").value_counts()
    st.bar_chart(s)

st.divider()

# ---------- Razonamientos (Acto 2) ----------
st.subheader("📝 Razonamientos antes de ver las métricas")
with st.expander(f"Ver {n_total} razonamientos", expanded=False):
    for _, r in df.iterrows():
        nombre = r.get("nombre", "") or "(anónimo)"
        modelo = r.get("modelo_apostado", "") or "—"
        razon = (r.get("razonamiento", "") or "").strip()
        if razon:
            st.markdown(f"**{nombre}** — apostó *{modelo}*")
            st.markdown(f"> {razon}")
            st.markdown("")

# ---------- Reflexiones (Acto 4) ----------
if n_reflexion:
    st.subheader("🔁 Reflexión final")
    cmec, cfalta = st.columns(2)
    with cmec:
        st.markdown("**Mecanismo histórico propuesto**")
        for _, r in df.iterrows():
            txt = (r.get("mecanismo_historico", "") or "").strip()
            if txt:
                nombre = r.get("nombre", "") or "(anónimo)"
                st.markdown(f"- **{nombre}:** {txt}")
    with cfalta:
        st.markdown("**¿Qué modelo falta?**")
        for _, r in df.iterrows():
            txt = (r.get("modelo_falta", "") or "").strip()
            if txt:
                nombre = r.get("nombre", "") or "(anónimo)"
                st.markdown(f"- **{nombre}:** {txt}")

st.divider()

# ---------- Tabla completa ----------
with st.expander("📋 Tabla completa de respuestas", expanded=False):
    st.dataframe(df, use_container_width=True, hide_index=True)
