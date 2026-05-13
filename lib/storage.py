"""Persistencia de las hipótesis y reflexiones de los estudiantes.

Backend primario: Google Sheets vía service account.
Fallback: CSV local `respuestas_local.csv` cuando no hay credenciales.

Cada estudiante ocupa UNA fila. La hipótesis (Acto 2) crea la fila; la
reflexión (Acto 4) actualiza las últimas 4 columnas de esa misma fila.
"""

import csv
import re
from datetime import datetime
from pathlib import Path
from typing import Optional

import pandas as pd
import streamlit as st


COLUMNAS = [
    "timestamp",
    "nombre",
    "codigo",
    "companeros",
    "rango_min",
    "rango_max",
    "modelo_apostado",
    "distribucion_predicha",
    "clustering_predicho",
    "razonamiento",
    "n_nodos",
    "n_aristas",
    "clustering_obs",
    "asortatividad_obs",
    "camino_promedio_obs",
    # Acto 4 — reflexión
    "acerto",
    "mecanismo_historico",
    "modelo_falta",
    "timestamp_reflexion",
]

# Posición (1-indexed) en la fila donde empieza la reflexión del Acto 4
COL_INICIO_REFLEXION = 16
N_COLS_REFLEXION = 4

ARCHIVO_LOCAL = Path(__file__).parent.parent / "respuestas_local.csv"

SCOPES = ["https://www.googleapis.com/auth/spreadsheets"]


def _tiene_credenciales_google() -> bool:
    """True solo si están ambos bloques: gcp_service_account Y sheets."""
    try:
        return (
            bool(st.secrets.get("gcp_service_account"))
            and bool(st.secrets.get("sheets"))
        )
    except Exception:
        return False


def _column_letter(n: int) -> str:
    """Convierte 1 -> 'A', 27 -> 'AA', etc."""
    s = ""
    while n > 0:
        n, r = divmod(n - 1, 26)
        s = chr(65 + r) + s
    return s


@st.cache_resource
def _abrir_hoja():
    """Conecta con la hoja de Google. Crea/repara el header si hace falta."""
    import gspread
    from google.oauth2.service_account import Credentials

    creds = Credentials.from_service_account_info(
        dict(st.secrets["gcp_service_account"]),
        scopes=SCOPES,
    )
    client = gspread.authorize(creds)

    sheets_cfg = st.secrets["sheets"]
    if "url" in sheets_cfg:
        sh = client.open_by_url(sheets_cfg["url"])
    elif "id" in sheets_cfg:
        sh = client.open_by_key(sheets_cfg["id"])
    else:
        raise RuntimeError("Falta sheets.url o sheets.id en secrets.toml")

    ws_name = sheets_cfg.get("worksheet", "respuestas")
    try:
        ws = sh.worksheet(ws_name)
    except gspread.WorksheetNotFound:
        ws = sh.add_worksheet(title=ws_name, rows=1000, cols=len(COLUMNAS))

    # Self-heal del encabezado: si difiere de COLUMNAS, lo reescribimos.
    encabezado_actual = ws.row_values(1)
    if encabezado_actual != COLUMNAS:
        if ws.col_count < len(COLUMNAS):
            ws.resize(rows=ws.row_count, cols=len(COLUMNAS))
        rango = f"A1:{_column_letter(len(COLUMNAS))}1"
        ws.update(values=[COLUMNAS], range_name=rango, value_input_option="RAW")

    return ws


def _parse_row_index(updated_range: str) -> Optional[int]:
    """De "'respuestas'!A5:S5" o "respuestas!A5:S5" extrae 5."""
    m = re.search(r"!\s*[A-Z]+(\d+)\s*:", updated_range)
    return int(m.group(1)) if m else None


def _guardar_local(fila: list) -> int:
    """Append a CSV local. Devuelve número de fila (1-indexed con header)."""
    nuevo = not ARCHIVO_LOCAL.exists()
    with ARCHIVO_LOCAL.open("a", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        if nuevo:
            w.writerow(COLUMNAS)
        w.writerow(fila)
    # contar filas (incluye header)
    with ARCHIVO_LOCAL.open(encoding="utf-8") as f:
        return sum(1 for _ in f)


def _actualizar_local(row_index: int, valores_reflexion: list):
    """Sobrescribe las columnas de reflexión en la fila row_index (1-indexed)."""
    if not ARCHIVO_LOCAL.exists():
        return
    # dtype=str + na_filter=False evita que pandas infiera float64 en las columnas
    # vacías del Acto 4 — si lo hace, asignar strings ("Parcialmente") falla.
    df = pd.read_csv(ARCHIVO_LOCAL, dtype=str, keep_default_na=False, na_filter=False)
    idx = row_index - 2
    if idx < 0 or idx >= len(df):
        return
    df.loc[idx, COLUMNAS[-N_COLS_REFLEXION:]] = valores_reflexion
    df.to_csv(ARCHIVO_LOCAL, index=False)


def guardar_hipotesis(payload: dict) -> tuple[bool, Optional[str], str, Optional[int]]:
    """Persiste la hipótesis (Acto 2).

    Devuelve (ok, error, destino, row_index).
    destino ∈ {"sheets", "local"}; row_index es la fila para actualizar después.
    """
    fila = [
        datetime.utcnow().isoformat(timespec="seconds"),
        payload.get("nombre", ""),
        payload.get("codigo", ""),
        payload.get("companeros", ""),
        payload.get("rango_min", ""),
        payload.get("rango_max", ""),
        payload.get("modelo", ""),
        payload.get("distribucion", ""),
        payload.get("clustering", ""),
        payload.get("razonamiento", ""),
        payload.get("n_nodos", ""),
        payload.get("n_aristas", ""),
        payload.get("clustering_obs", ""),
        payload.get("asortatividad_obs", ""),
        payload.get("camino_promedio_obs", ""),
        "", "", "", "",  # Acto 4 vacíos por ahora
    ]

    if _tiene_credenciales_google():
        try:
            ws = _abrir_hoja()
            result = ws.append_row(fila, value_input_option="RAW")
            rng = result.get("updates", {}).get("updatedRange", "")
            row = _parse_row_index(rng)
            return True, None, "sheets", row
        except Exception as e:
            row = _guardar_local(fila)
            return False, f"Error escribiendo a Sheets: {e}", "local", row

    row = _guardar_local(fila)
    return True, None, "local", row


def guardar_reflexion(row_index: int, payload: dict) -> tuple[bool, Optional[str], str]:
    """Actualiza las 4 columnas de reflexión (Acto 4) en la fila row_index."""
    valores = [
        payload.get("acerto", ""),
        payload.get("mecanismo", ""),
        payload.get("modelo_falta", ""),
        datetime.utcnow().isoformat(timespec="seconds"),
    ]

    if _tiene_credenciales_google() and row_index:
        try:
            ws = _abrir_hoja()
            col_ini = _column_letter(COL_INICIO_REFLEXION)
            col_fin = _column_letter(COL_INICIO_REFLEXION + N_COLS_REFLEXION - 1)
            rng = f"{col_ini}{row_index}:{col_fin}{row_index}"
            ws.update(values=[valores], range_name=rng, value_input_option="RAW")
            return True, None, "sheets"
        except Exception as e:
            _actualizar_local(row_index, valores)
            return False, f"Error actualizando Sheets: {e}", "local"

    _actualizar_local(row_index, valores)
    return True, None, "local"


def modo_almacenamiento() -> str:
    return "sheets" if _tiene_credenciales_google() else "local"
