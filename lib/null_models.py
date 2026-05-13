"""Modelos nulos comparables: Erdős–Rényi, Barabási–Albert, Watts–Strogatz, Configuration."""

import networkx as nx


def er_match(n, m, seed=42):
    """Erdős–Rényi G(n, m) con exactamente n nodos y m aristas (azar puro)."""
    return nx.gnm_random_graph(n, m, seed=seed)


def ba_match(n, m_total, seed=42):
    """Barabási–Albert que aproxima m_total aristas (vinculación preferencial).

    BA con parámetro m produce m*(n-m) ≈ m*n aristas, así que despejamos m.
    """
    m = max(1, round(m_total / n))
    m = min(m, n - 1) if n > 1 else 1
    return nx.barabasi_albert_graph(n, m, seed=seed)


def ws_match(n, m_total, p=0.1, seed=42):
    """Watts–Strogatz aproximando m_total (mundo pequeño).

    El número de aristas en WS es n*k/2, así que despejamos k.
    k debe ser par y < n.
    """
    k = max(2, round(2 * m_total / n))
    if k % 2:
        k += 1
    if k >= n:
        k = n - 2 if n > 2 else 2
    return nx.watts_strogatz_graph(n, k, p, seed=seed)


def config_match(G_observed, seed=42):
    """Configuration model: preserva exactamente la distribución de grado."""
    deg_seq = [d for _, d in G_observed.degree()]
    G = nx.configuration_model(deg_seq, seed=seed)
    G = nx.Graph(G)  # colapsa multi-aristas
    G.remove_edges_from(nx.selfloop_edges(G))
    return G


def generar_todos(G_observed, seed=42):
    """Devuelve un dict {nombre: grafo_nulo} con los 4 modelos."""
    n = G_observed.number_of_nodes()
    m = G_observed.number_of_edges()
    return {
        'Erdős–Rényi': er_match(n, m, seed=seed),
        'Barabási–Albert': ba_match(n, m, seed=seed),
        'Watts–Strogatz': ws_match(n, m, p=0.1, seed=seed),
        'Configuration': config_match(G_observed, seed=seed),
    }
