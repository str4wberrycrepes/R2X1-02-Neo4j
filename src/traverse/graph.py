# ephemera
# oh, mine beloved.

import xml.etree.ElementTree as ET
from collections import defaultdict
import pandas

class node:
    def __init__(self, name, id, isKeyword=False):
        self.name = name
        self.id = id
        self.isKeyword = isKeyword
    
    def __str__(self):
        return f"{self.name} (ID: {self.id}, Keyword: {self.isKeyword})"
    
    def __repr__(self):
        return self.__str__()
class graph:  # undirected, weighted graph
    def __init__(self):
        self.graph = {}

    def addNode(self, node):
        if node not in self.graph:
            self.graph[node] = {}

    def addEdge(self, node1, node2, weight=1):
        self.addNode(node1)
        self.addNode(node2)

        self.graph[node1][node2] = weight
        self.graph[node2][node1] = weight

    def removeEdge(self, node1, node2):
        if node1 in self.graph and node2 in self.graph[node1]:
            del self.graph[node1][node2]
            del self.graph[node2][node1]

    def removeNode(self, node):
        if node in self.graph:
            for adjacent_node in list(self.graph[node].keys()):
                del self.graph[adjacent_node][node]

            del self.graph[node]

    def getNodes(self):
        return list(self.graph.keys())

    def getEdges(self):
        edges = []
        visited = set()
        
        for node in self.graph:
            for neighbor, weight in self.graph[node].items():
                edge_id = tuple(sorted([id(node), id(neighbor)])) + (weight,)
                if edge_id not in visited:
                    edges.append((node, neighbor, weight))
                    visited.add(edge_id)
        
        return edges

    def getNeighbors(self, node):
        return self.graph.get(node, {})

    def checkForEdge(self, node1, node2):
        return (node1 in self.graph and 
                node2 in self.graph[node1])

    def __str__(self):
        graph_str = "Erm, what the sigma:\n"
        for node, neighbors in sorted(self.graph.items(), key=lambda x: x[0].name if hasattr(x[0], 'name') else str(x[0])):
            graph_str += f"{node}: {neighbors}\n"
        return graph_str


