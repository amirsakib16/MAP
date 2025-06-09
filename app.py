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
    c1_time = int(data.get('c1_time'))
    c1_urgency = int(data.get('c1_urgency'))
    c2_time = int(data.get('c2_time'))
    c2_urgency = int(data.get('c2_urgency'))

    G, due_times = create_graph()
    pos = nx.spring_layout(G, seed=42)

    def find_path(end_node):
        heap = [(0, start_node, [start_node])]
        visited = {}
        while heap:
            current_time, node, path = heappop(heap)
            if node == end_node:
                return path, current_time
            if node in visited and visited[node] <= current_time:
                continue
            visited[node] = current_time
            for neighbor in G.neighbors(node):
                if neighbor in path:
                    continue
                weight = G[node][neighbor]['weight']
                arrival_time = current_time + weight
                if arrival_time <= due_times[neighbor]:
                    heappush(heap, (arrival_time, neighbor, path + [neighbor]))
        return [], float('inf')

    # Evaluate both customers
    best = {'customer': None, 'priority': float('inf')}
    customers = [
        {'id': 'Customer 1', 'travel_time': c1_time, 'urgency': c1_urgency, 'node': 6},
        {'id': 'Customer 2', 'travel_time': c2_time, 'urgency': c2_urgency, 'node': 7}
    ]

    for customer in customers:
        path, total_time = find_path(customer['node'])
        cost = int((total_time * 100) / 50)
        priority = customer['travel_time'] + cost - customer['urgency']
        customer.update({'path': path, 'time': total_time, 'cost': cost, 'priority': priority})

        if priority < best['priority']:
            best = {
        'customer': customer['id'],
        'path': path,
        'total_time': total_time,
        'total_cost': cost,
        'node': customer['node'],
        'priority': priority  # ← Add this line to avoid KeyError
    }


    # Draw graph
    edge_colors = []
    for u, v in G.edges():
        if (u in best['path'] and v in best['path'] and abs(best['path'].index(u) - best['path'].index(v)) == 1):
            edge_colors.append('red')
        else:
            edge_colors.append('gray')

    plt.figure(figsize=(8, 6))
    nx.draw(G, pos, with_labels=True,
            node_color=['green' if n in best['path'] else 'lightgray' for n in G.nodes()],
            edge_color=edge_colors, node_size=700)
    nx.draw_networkx_labels(G, pos, labels={n: f"{n}\nDue:{due_times[n]}" for n in G.nodes()}, font_size=8)
    nx.draw_networkx_edge_labels(G, pos, edge_labels=nx.get_edge_attributes(G, 'weight'))
    plt.axis('off')

    if not os.path.exists('static'):
        os.makedirs('static')
    plt.savefig('static/graph.png')
    plt.close()

    return jsonify({
        'selected_customer': best['customer'],
        'path': best['path'],
        'total_time': best['total_time'],
        'total_cost': best['total_cost'],
        'image_url': '/static/graph.png'
    })


if __name__ == '__main__':
    app.run(debug=True)
