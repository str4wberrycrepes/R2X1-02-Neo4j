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


    def extractClassName(uri):
        """Extract just the class name from a URI."""
        if '#' in uri:
            return uri.split('#')[-1]
        else:
            # For URIs without a fragment identifier, use the last path component
            parts = uri.strip('/').split('/')
            return parts[-1]


    def parse_rdf_to_graph(rdf_file, weight_file):
        # Initialize graph
        g = graph()
        
        # Parse RDF file
        tree = ET.parse(rdf_file)
        root = tree.getroot()
        
        # Define namespaces
        namespaces = {
            'rdf': 'http://www.w3.org/1999/02/22-rdf-syntax-ns#',
            'rdfs': 'http://www.w3.org/2000/01/rdf-schema#',
            'owl': 'http://www.w3.org/2002/07/owl#'
        }
        
        # Find all owl:Class elements
        classes = root.findall('./owl:Class', namespaces)
        
        # Dictionary to store classes and their subclasses
        class_hierarchy = defaultdict(list)
        relationship_strengths = {}
        
        # Root nodes
        root_nodes = [
            "Agriculture",
            "Biology",
            "Chemistry",
            "Computer_Science",
            "Engineering",
            "Physics",
            "Technology"
        ]

        node_map = {}

        weightData = pandas.read_excel(excelFilePath)

        
        # Add all classes as nodes first
        for cls in classes:
            class_about = cls.attrib.get('{http://www.w3.org/1999/02/22-rdf-syntax-ns#}about', '')
            if class_about:
                node = {}
                class_id = graph.extractClassName(class_about)
                node["id"] =  class_id

                # Check for name
                label = cls.find('./rdfs:label', namespaces)
                if label is not None:
                    node["name"] = label

                # Check for keywordStatus
                isKeyword = cls.find('./rdfs:comment', namespaces)
                if isKeyword is not None and isKeyword.text == "KEYWORD":
                    node["isKeyword"] = True
                else:
                    node["isKeyword"] = False

                node = node(node["name"], node["id"], node["isKeyword"])
                g.addNode(node)
                node_map[node["name"]] = node
                
                # Check for subClassOf relationship
                subclass_of = cls.find('./rdfs:subClassOf', namespaces)
                if subclass_of is not None:
                    parent_resource = subclass_of.attrib.get('{http://www.w3.org/1999/02/22-rdf-syntax-ns#}resource', '')
                    if parent_resource:
                        parent_name = graph.extractClassName(parent_resource)
                        class_hierarchy[parent_name].append(class_id)
        
        # Add all root nodes
        for node in root_nodes:
            g.addNode(node)
        
        # Add edges between classes and their subclasses with relationship strengths
        for i in range(len(weightData)):
            weight = weightData.loc[i]
            child = node_map[weight.child]
            parent = node_map[weight.parent]
            weightValue = weight.weight

            g.addEdge(parent, child, weightValue) 


