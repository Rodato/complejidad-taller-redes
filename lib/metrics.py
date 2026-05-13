"""Métricas estructurales para comparar la red observada con modelos nulos."""

import networkx as nx


def distribucion_grado(G):
    return [d for _, d in G.degree()]


def clustering_promedio(G):
    return nx.average_clustering(G) if G.number_of_nodes() > 0 else 0.0


def longitud_camino_promedio(G):
    """Promedio sobre el componente más grande (la red suele estar fragmentada)."""
    if G.number_of_nodes() < 2:
        return None
    comps = list(nx.connected_components(G))
    if not comps:
        return None
    gigante = G.subgraph(max(comps, key=len))
    if gigante.number_of_nodes() < 2:
        return None
    return nx.average_shortest_path_length(gigante)


def asortatividad(G):
    """Coeficiente de asortatividad por grado.
    Positivo: nodos de alto grado se conectan entre sí.
    Negativo: nodos de alto grado se conectan con los de bajo grado (estrellas)."""
    if G.number_of_edges() < 2:
        return None
    try:
        return nx.degree_assortativity_coefficient(G)
    except Exception:
        return None


def todas_las_metricas(G):
    return {
        'n_nodos': G.number_of_nodes(),
        'n_aristas': G.number_of_edges(),
        'clustering': clustering_promedio(G),
        'camino_promedio': longitud_camino_promedio(G),
        'asortatividad': asortatividad(G),
        'grado_maximo': max((d for _, d in G.degree()), default=0),
        'grado_promedio': (
            sum(d for _, d in G.degree()) / G.number_of_nodes()
            if G.number_of_nodes() > 0 else 0
        ),
    }
