import io
import base64
import math
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import networkx as nx

def generate_network_graph(edges, user_names, net_balances=None, is_after=False):
    G = nx.DiGraph()

    for u_id in user_names.keys():
        G.add_node(u_id)

    for e in edges:
        G.add_edge(e['debtor_id'], e['creditor_id'], weight=e['amount'])

    fig, ax = plt.subplots(figsize=(6.5, 5.5))
    fig.patch.set_facecolor('#ffffff')
    ax.set_facecolor('#ffffff')

    nodes = list(G.nodes())
    num_nodes = len(nodes)
    pos = {}

    for i, node in enumerate(nodes):
        angle = 2 * math.pi * i / max(num_nodes, 1)
        # Scaled radius slightly inward to avoid edge clipping
        pos[node] = (0.75 * math.cos(angle), 0.75 * math.sin(angle))

    labels = {}
    for node in nodes:
        name = user_names.get(node, f"User {node}")
        if is_after and net_balances and node in net_balances:
            bal = net_balances[node]
            sign = "+" if bal > 0 else ""
            labels[node] = f"{name}\n({sign}${bal:.2f})"
        else:
            labels[node] = name

    node_color = '#e0f2fe' if not is_after else '#dcfce7'
    edge_color = '#64748b' if not is_after else '#16a34a'

    nx.draw_networkx_nodes(G, pos, ax=ax, node_size=2600, node_color=node_color, edgecolors='#334155', linewidths=1.5)
    nx.draw_networkx_labels(G, pos, labels=labels, ax=ax, font_size=8, font_weight='bold')

    if len(edges) > 0:
        nx.draw_networkx_edges(
            G, pos, ax=ax,
            edge_color=edge_color,
            width=2,
            arrowstyle='-|>',
            arrowsize=18,
            node_size=2600,
            connectionstyle='arc3,rad=0.12'
        )

        edge_labels = {(u, v): f"${d['weight']:.2f}" for u, v, d in G.edges(data=True)}
        nx.draw_networkx_edge_labels(
            G, pos, edge_labels=edge_labels, ax=ax,
            font_size=8, font_weight='bold',
            bbox=dict(boxstyle='round,pad=0.2', facecolor='#ffffff', edgecolor='#cbd5e1')
        )

    # Added generous padding to prevent circle boundaries from getting cut off
    ax.margins(0.30)
    ax.axis('off')
    plt.tight_layout()

    buf = io.BytesIO()
    plt.savefig(buf, format='png', dpi=120, bbox_inches='tight')
    plt.close(fig)
    buf.seek(0)
    
    encoded = base64.b64encode(buf.read()).decode('utf-8')
    return f"data:image/png;base64,{encoded}"