import networkx as nx
import matplotlib.pyplot as plt
def plot_resource_allocation_graph(system, title="Граф распределения ресурсов"):
    G = nx.DiGraph()
    for p in system.processes:
        G.add_node(p, bipartite=0, type='process')
    for r_idx, r in enumerate(system.resources):
        label = f"{r}\n(свободно: {system.available[r_idx]})"
        G.add_node(label, bipartite=1, type='resource', raw_name=r)
    # Ребра выделения: Ресурс -> Процесс (Allocation)
    for i, p in enumerate(system.processes):
        for j, r in enumerate(system.resources):
            alloc_cnt = system.allocation[i][j]
            if alloc_cnt > 0:
                r_label = [n for n, d in G.nodes(data=True) if d.get('raw_name') == r][0]
                G.add_edge(r_label, p, label=f"выделено: {alloc_cnt}")
    # Ребра запроса: Процесс -> Ресурс (Request)
    for i, p in enumerate(system.processes):
        for j, r in enumerate(system.resources):
            req_cnt = system.request[i][j]
            if req_cnt > 0:
                r_label = [n for n, d in G.nodes(data=True) if d.get('raw_name') == r][0]
                G.add_edge(p, r_label, label=f"ждет: {req_cnt}")
    plt.figure(figsize=(9, 6))
    pos = nx.spring_layout(G, seed=42)
    proc_nodes = [n for n, d in G.nodes(data=True) if d.get('type') == 'process']
    res_nodes = [n for n, d in G.nodes(data=True) if d.get('type') == 'resource']
    nx.draw_networkx_nodes(G, pos, nodelist=proc_nodes, node_color='#7289da', node_shape='o', node_size=1800, label='Процессы')
    nx.draw_networkx_nodes(G, pos, nodelist=res_nodes, node_color='#43b581', node_shape='s', node_size=2200, label='Ресурсы')
    nx.draw_networkx_labels(G, pos, font_size=9, font_family='sans-serif')
    nx.draw_networkx_edges(G, pos, edge_color='#99aab5', arrows=True, arrowsize=18, width=1.5, connectionstyle='arc3, rad = 0.08')
    edge_labels = nx.get_edge_attributes(G, 'label')
    nx.draw_networkx_edge_labels(G, pos, edge_labels=edge_labels, font_size=8)
    plt.title(title, fontsize=12, fontweight='bold')
    plt.legend(scatterpoints=1)
    plt.axis('off')
    plt.tight_layout()
    plt.show()