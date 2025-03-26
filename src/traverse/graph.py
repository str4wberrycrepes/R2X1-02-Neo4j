# I don't understand how the code I wrote works so neither will you

class graph: # undirected, weighted graph
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
                if (neighbor, node, weight) not in visited:
                    edges.append((node, neighbor, weight))
                    visited.add((node, neighbor, weight))
        
        return edges

    def getNeighbors(self, node):
        return self.graph.get(node, {})

    def checkForEdge(self, node1, node2):
        return (node1 in self.graph and 
                node2 in self.graph[node1])

    def __str__(self):
        graph_str = "Undirected Weighted Graph:\n"
        for node, neighbors in self.graph.items():
            graph_str += f"{node}: {neighbors}\n"
        return graph_str