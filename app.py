from flask import Flask, render_template, request, jsonify
import networkx as nx
import random
import matplotlib.pyplot as plt
import os
from heapq import heappush, heappop


app = Flask(__name__)

# Helper function to create a fully connected graph with due times and edge weights
def create_graph():
    G = nx.complete_graph(8)
    for (u, v) in G.edges():
        G[u][v]['weight'] = random.randint(1, 20)
    due_times = {i: random.randint(15, 60) for i in G.nodes()}
    nx.set_node_attributes(G, due_times, "due_time")
    return G, due_times

# Route for the home page
@app.route('/')
def index():
    return render_template('index.html')

# Route to simulate the delivery traversal
@app.route('/simulate', methods=['POST'])
def simulate():
    data = request.get_json()
    start_node = int(data.get('start_node', 0))
    end_node = int(data.get('end_node', 7))

    G, due_times = create_graph()
    pos = nx.spring_layout(G, seed=42)  # fixed layout for consistency

    # Priority queue: (time_so_far, current_node, path_list)
    heap = []
    heappush(heap, (0, start_node, [start_node]))

    visited = dict()  # node: earliest arrival time

    found_path = None
    total_time = None

    while heap:
        current_time, current_node, path = heappop(heap)

        if current_node == end_node:
            found_path = path
            total_time = current_time
            break

        if current_node in visited and visited[current_node] <= current_time:
            continue
        visited[current_node] = current_time

        for neighbor in G.neighbors(current_node):
            weight = G[current_node][neighbor]['weight']
            arrival_time = current_time + weight
            if arrival_time <= due_times[neighbor] and neighbor not in path:
                heappush(heap, (arrival_time, neighbor, path + [neighbor]))

    if not found_path:
        return jsonify({
            'message': f"No valid delivery path found from {start_node} to {end_node} within due times.",
            'path': [],
            'start_node': start_node,
            'end_node': end_node,
            'total_time': 0,
            'image_url': ''
        })

    # Prepare graph drawing with path highlighted
    edge_colors = []
    for u, v in G.edges():
        if (u in found_path and v in found_path and abs(found_path.index(u) - found_path.index(v)) == 1):
            edge_colors.append('red')
        else:
            edge_colors.append('gray')
    edge_alphas = [1.0 if c == 'red' else 0.2 for c in edge_colors]

    node_colors = ['lightgreen' if n in found_path else 'lightgray' for n in G.nodes()]
    node_alphas = [1.0 if n in found_path else 0.3 for n in G.nodes()]
    labels = {n: f"{n}\n(due:{due_times[n]})" for n in G.nodes()}

    plt.figure(figsize=(8, 6))
    nx.draw_networkx_nodes(G, pos, node_color=node_colors, alpha=node_alphas, node_size=800)
    nx.draw_networkx_edges(G, pos, edge_color=edge_colors, alpha=edge_alphas)
    nx.draw_networkx_labels(G, pos, labels=labels, font_weight='bold', font_size=8)
    edge_labels = nx.get_edge_attributes(G, 'weight')
    nx.draw_networkx_edge_labels(G, pos, edge_labels=edge_labels)

    plt.title("Google Map")
    plt.axis('off')
    plt.tight_layout()

    if not os.path.exists('static'):
        os.makedirs('static')
    plt.savefig('static/graph.png')
    plt.close()

    return jsonify({
        'path': found_path,
        'start_node': start_node,
        'end_node': end_node,
        'total_time': total_time,
        'message': f"Delivery path from node {start_node} to {end_node}: {found_path} with total time {total_time}",
        'image_url': '/static/graph.png'
    })


if __name__ == '__main__':
    app.run(debug=True)
