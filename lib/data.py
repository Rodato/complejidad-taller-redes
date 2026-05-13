"""Carga y limpieza de la base de la Notaría 2 de Cali (1938-1943)."""

from pathlib import Path
import re
import pandas as pd


def load_raw(path):
    return pd.read_csv(path)


def parse_valor(v):
    """Convierte strings tipo '700,00', '1.500,00', '3050$' a float.
    Devuelve None si no se puede parsear o si es N/A."""
    if pd.isna(v):
        return None
    s = str(v).strip().replace('$', '').replace(' ', '')
    if s.lower() in ('n/a', 'na', ''):
        return None
    if ',' in s:
        s = s.replace('.', '').replace(',', '.')
    try:
        return float(s)
    except ValueError:
        return None


def normalize_name(name):
    """Normaliza nombres: lower, strip, espacios colapsados, N/A -> None."""
    if pd.isna(name):
        return None
    s = re.sub(r'\s+', ' ', str(name).strip().lower())
    if s in ('n/a', 'na', ''):
        return None
    return s


def clean(df):
    df = df.copy()
    df['vendedor'] = df['vendedor'].apply(normalize_name)
    df['comprador'] = df['comprador'].apply(normalize_name)
    df['valor_num'] = df['Valor'].apply(parse_valor)
    df['año'] = df['fecha'].astype(int)
    df = df.dropna(subset=['vendedor', 'comprador'])
    df = df[df['vendedor'] != df['comprador']]
    return df.reset_index(drop=True)
