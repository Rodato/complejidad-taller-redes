"""Visualizaciones de la red y de las distribuciones de grado.

- Red interactiva: pyvis (vis.js) — soporta arrastrar nodos, zoom, pan.
- Distribuciones: Plotly.
"""

from collections import Counter
import math
import networkx as nx
import plotly.graph_objects as go
from pyvis.network import Network


def network_html_interactiva(G, height=620, mostrar_labels_desde_grado=3):
    """Devuelve HTML de una red interactiva (pyvis/vis.js).

    Soporta:
    - arrastrar nodos
    - zoom (rueda del mouse) y pan (arrastre del fondo)
    - tooltip con nombre + grado al pasar el mouse
    - física de Barnes-Hut que separa componentes desconectados

    Solo se muestran labels de actores con grado >= mostrar_labels_desde_grado
    para evitar saturación visual.
    """
    net = Network(
        height=f"{height}px",
        width="100%",
        bgcolor="#ffffff",
        font_color="#222",
        notebook=False,
        directed=False,
        cdn_resources='remote',
    )

    # Calcular colores en escala viridis-like por grado
    grados = dict(G.degree())
    g_max = max(grados.values()) if grados else 1

    def color_por_grado(d):
        # rampa azul oscuro -> amarillo claro
        t = d / g_max if g_max else 0
        r = int(68 + (253 - 68) * t)
        g = int(1 + (231 - 1) * t)
        b = int(84 + (37 - 84) * t)
        return f"rgb({r},{g},{b})"

    for nodo in G.nodes():
        d = grados[nodo]
        label = nodo if d >= mostrar_labels_desde_grado else " "
        net.add_node(
            nodo,
            label=label,
            title=f"<b>{nodo}</b><br>grado: {d}",
            size=8 + 2 * d,
            color=color_por_grado(d),
            borderWidth=1,
            font={"size": 12, "face": "Inter, Arial"},
        )

    for u, v, data in G.edges(data=True):
        w = data.get('weight', 0) or 0
        n_tx = data.get('n_transacciones', 1)
        ancho = min(6, 0.5 + (n_tx ** 0.5))
        net.add_edge(
            u, v,
            title=f"valor total: {w:,.0f}<br>transacciones: {n_tx}",
            width=ancho,
            color={"color": "#bbb", "opacity": 0.6},
        )

    # Física: Barnes-Hut con repulsión moderada y estabilización corta
    net.set_options("""
    {
      "physics": {
        "solver": "barnesHut",
        "barnesHut": {
          "gravitationalConstant": -3500,
          "centralGravity": 0.25,
          "springLength": 120,
          "springConstant": 0.04,
          "damping": 0.4,
          "avoidOverlap": 0.6
        },
        "stabilization": {
          "enabled": true,
          "iterations": 250,
          "updateInterval": 25
        },
        "minVelocity": 0.5,
        "timestep": 0.4
      },
      "interaction": {
        "hover": true,
        "tooltipDelay": 100,
        "zoomView": true,
        "dragNodes": true,
        "dragView": true,
        "navigationButtons": true,
        "keyboard": false
      },
      "nodes": {
        "shape": "dot",
        "scaling": {"min": 6, "max": 40}
      },
      "edges": {
        "smooth": {"enabled": true, "type": "continuous"}
      }
    }
    """)

    return net.generate_html(notebook=False)


def network_plot(G, titulo=None):
    """Dibuja la red usando spring_layout (Fruchterman–Reingold). Versión estática Plotly."""
    n = G.number_of_nodes()
    if n == 0:
        return go.Figure().update_layout(title="(red vacía)")

    k = 1 / math.sqrt(n) if n > 0 else None
    pos = nx.spring_layout(G, seed=42, k=k, iterations=50)

    edge_x, edge_y = [], []
    for u, v in G.edges():
        x0, y0 = pos[u]
        x1, y1 = pos[v]
        edge_x.extend([x0, x1, None])
        edge_y.extend([y0, y1, None])

    edge_trace = go.Scatter(
        x=edge_x, y=edge_y,
        mode='lines',
        line=dict(width=0.5, color='#888'),
        hoverinfo='none',
    )

    node_x, node_y, hover, sizes, colors = [], [], [], [], []
    for nodo in G.nodes():
        x, y = pos[nodo]
        deg = G.degree(nodo)
        node_x.append(x)
        node_y.append(y)
        hover.append(f"<b>{nodo}</b><br>grado: {deg}")
        sizes.append(6 + 1.5 * deg)
        colors.append(deg)

    node_trace = go.Scatter(
        x=node_x, y=node_y,
        mode='markers',
        marker=dict(
            size=sizes,
            color=colors,
            colorscale='Viridis',
            showscale=True,
            colorbar=dict(title='Grado'),
            line=dict(width=0.5, color='#333'),
        ),
        hovertext=hover,
        hoverinfo='text',
    )

    fig = go.Figure(
        data=[edge_trace, node_trace],
        layout=go.Layout(
            title=titulo,
            showlegend=False,
            hovermode='closest',
            margin=dict(b=10, l=10, r=10, t=40),
            xaxis=dict(showgrid=False, zeroline=False, showticklabels=False),
            yaxis=dict(showgrid=False, zeroline=False, showticklabels=False),
            plot_bgcolor='white',
        )
    )
    return fig


def degree_dist_hist(degs_dict, normalizar=False):
    """Histogramas superpuestos de distribución de grado para varias redes."""
    fig = go.Figure()
    for label, degs in degs_dict.items():
        fig.add_trace(go.Histogram(
            x=degs,
            name=label,
            opacity=0.55,
            histnorm='probability' if normalizar else None,
            nbinsx=25,
        ))
    fig.update_layout(
        barmode='overlay',
        xaxis_title='Grado',
        yaxis_title='Proporción' if normalizar else 'Frecuencia',
        legend=dict(orientation='h', y=-0.2),
        margin=dict(b=10, l=10, r=10, t=40),
    )
    return fig


def degree_dist_loglog(degs_dict):
    """Distribución de grado en escala log-log. Una ley de potencia se ve recta."""
    fig = go.Figure()
    for label, degs in degs_dict.items():
        counts = Counter(degs)
        xs = sorted(k for k in counts.keys() if k > 0)
        ys = [counts[k] for k in xs]
        fig.add_trace(go.Scatter(
            x=xs, y=ys,
            mode='markers+lines',
            name=label,
            marker=dict(size=8),
        ))
    fig.update_xaxes(type='log', title='Grado (log)')
    fig.update_yaxes(type='log', title='Nodos con ese grado (log)')
    fig.update_layout(
        legend=dict(orientation='h', y=-0.2),
        margin=dict(b=10, l=10, r=10, t=40),
    )
    return fig


def bar_metricas(rows, metrica):
    """Barra horizontal comparando una métrica entre redes."""
    labels = [r['red'] for r in rows]
    vals = [r.get(metrica) or 0 for r in rows]
    colors = ['#1f77b4' if l == 'Observada' else '#bbbbbb' for l in labels]
    fig = go.Figure(go.Bar(x=vals, y=labels, orientation='h', marker_color=colors))
    fig.update_layout(
        title=metrica,
        margin=dict(b=10, l=10, r=10, t=40),
        height=250,
    )
    return fig
