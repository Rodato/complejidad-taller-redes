"""Construcción del grafo de transacciones a partir del DataFrame limpio."""

import networkx as nx
import pandas as pd


def build_graph(df, weight_col='valor_num'):
    """Construye una red no dirigida.

    Cada nodo es un actor (vendedor o comprador). Cada arista es una relación
    de compraventa. Si dos actores transan más de una vez, se agregan los pesos
    y se cuenta el número de transacciones en el atributo 'n_transacciones'.
    """
    G = nx.Graph()
    for _, row in df.iterrows():
        v, c = row['vendedor'], row['comprador']
        w = row.get(weight_col)
        w = float(w) if pd.notna(w) else 0.0
        if G.has_edge(v, c):
            G[v][c]['weight'] += w
            G[v][c]['n_transacciones'] += 1
        else:
            G.add_edge(v, c, weight=w, n_transacciones=1)
    return G


def build_graph_acumulado(df, año_max):
    """Red acumulada con todas las transacciones hasta `año_max` inclusive."""
    return build_graph(df[df['año'] <= año_max])


def graph_summary(G):
    n = G.number_of_nodes()
    m = G.number_of_edges()
    return {
        'n_nodos': n,
        'n_aristas': m,
        'densidad': nx.density(G) if n > 1 else 0,
        'componentes': nx.number_connected_components(G),
        'tamano_gigante': len(max(nx.connected_components(G), key=len)) if n else 0,
    }


def top_actores(G, k=10):
    """Devuelve los k actores con mayor grado."""
    return sorted(G.degree(), key=lambda x: x[1], reverse=True)[:k]
