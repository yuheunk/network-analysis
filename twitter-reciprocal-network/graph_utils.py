#!/usr/bin/env python
# coding: utf-8

import networkx as nx
import matplotlib.pyplot as plt

def graph_info(graph):
    # Get graph information:
    # Number of nodes, Number of edges, Diameter, and average distance
    num_nodes = graph.number_of_nodes()
    num_edges = graph.number_of_edges()
    diameter = nx.diameter(graph)
    average_distance = nx.average_shortest_path_length(graph)
    print("---Network Information---")
    # print the number of nodes and edges
    print("Number of nodes:", num_nodes)
    print("Number of edges:", num_edges)

    # print the diameter and average distance
    print("Diameter:", diameter)
    print("Average Distance:", average_distance)
    return num_nodes, num_edges, diameter, average_distance

def save_graph_info(graph, filename):
    # Import graph information from graph_info() function
    num_nodes, num_edges, diameter, average_distance = graph_info(graph)
    # Open file to save
    with open(filename, "w") as f:
        f.write(f'---Network Information---\n')
        f.write(f'Number of nodes: {num_nodes}\n')
        f.write(f'Number of edges: {num_edges}\n')
        f.write(f'Diameter: {diameter}\n')
        f.write(f'Average Distance: {average_distance}\n')

def save_graph_vis(graph, filename):
    """
    Save two versions of graph visualization
    1. Simple graph visualization
    2. Community clustered graph visualization
    """
    ## 1. Simple visualization
    plt.figure(figsize=(10,8))  # Set visualization size
    nx.draw(graph)  # Draw a simple graph
    plt.savefig(filename+"-simple.png")  # Save image
    plt.show()

    ## 2. Community clustered visualization
    # Import necessary modules
    from networkx.algorithms.community import greedy_modularity_communities
    
    # Get the degree of each node
    degree = dict(graph.degree)
    # Find communities using the Louvain method
    communities = list(greedy_modularity_communities(graph))
    # Assign a color to each community
    colors = {node: i for i, comm in enumerate(communities) for node in comm}
    # Set node colors based on community
    node_colors = [colors[node] for node in graph.nodes]
    # Set node sizes based on degree
    node_sizes = [degree[node]*10 for node in graph.nodes]

    # Draw the network
    fig, ax = plt.subplots(figsize=(10, 8))  # Set visualization size
    pos = nx.spring_layout(graph)  # Compute node positions for a network graph visualization
    nx.draw_networkx_nodes(graph, pos, node_color=node_colors, node_size=node_sizes)
    nx.draw_networkx_edges(graph, pos)

    plt.axis('off')
    plt.savefig(filename+"-community.png")  # Save image
    plt.show()
    return