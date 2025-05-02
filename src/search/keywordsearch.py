# ephemera
# import
from ..traverse.graph import graph, node # undirected weighted graph
import xml.etree.ElementTree as ET
from collections import defaultdict
import pandas

import sys  # sys

from neo4j import GraphDatabase # Neo4j
import json # Config

def ontsearch(edgesum, n, x, startNode, traversed):
    # Since I like to tweak, get the actual node if what I input is a string.
    if isinstance(startNode, str):
        startNode = next((n for n in graph_.getNodes() if n.name == startNode or n.id == startNode), None)
        if not startNode:
            return traversed
    
    # Check if we've already visited this node
    if any(n.name == startNode.name for n in traversed):
        return traversed
    
    traversed.append(startNode)
    
    # Get neighbors that haven't been traversed
    neighbors = graph_.getNeighbors(startNode)
    untraversed_neighbors = [
        n for n in neighbors 
        if not any(t.name == n.name for t in traversed)
    ]
    
    # Calculate current semantic value
    sv = edgesum / (n * x) if (n * x) != 0 else 0
    
    # Base case - stop if no neighbors or sv too low
    if not untraversed_neighbors or sv < 0:  # More lenient threshold
        return traversed
    
    # Recursive case
    for neighbor in untraversed_neighbors:
        edge_weight = neighbors[neighbor]
        new_edgesum = edgesum + edge_weight
        new_n = n + 1
        
        # Continue traversal
        ontsearch(new_edgesum, new_n, x, neighbor, traversed)
    
    return traversed

def extractClassName(uri):
    if '#' in uri:
        return uri.split('#')[-1]
    else:
        # For URIs without a fragment identifier, use the last path component
        parts = uri.strip('/').split('/')
        return parts[-1]


def parse_rdf_to_graph(rdf_file):
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

    # Add all classes as nodes first
    for cls in classes:
        class_about = cls.attrib.get('{http://www.w3.org/1999/02/22-rdf-syntax-ns#}about', '')
        if class_about:
            node_ = {}
            class_id = extractClassName(class_about)
            node_["id"] = class_id

            # Check for name
            label = cls.find('./rdfs:label', namespaces)
            if label is None:
                continue
            else:
                label = label.text
                node_["name"] = label

            # Check for keywordStatus
            isKeyword = cls.find('./rdfs:comment', namespaces)
            if isKeyword is not None and isKeyword.text == "KEYWORD":
                node_["isKeyword"] = True
            else:
                node_["isKeyword"] = False

            node_obj = node(node_["name"], node_["id"], node_["isKeyword"])
            g.addNode(node_obj)
            node_map[node_["name"]] = node_obj
            
            # Check for subClassOf relationship
            subclasses = cls.findall('./rdfs:subClassOf', namespaces)
            for subclass_of in subclasses:
                parent_resource = subclass_of.attrib.get('{http://www.w3.org/1999/02/22-rdf-syntax-ns#}resource', '')
                if parent_resource:
                    parent_name = extractClassName(parent_resource)
                    class_hierarchy[parent_name].append(class_id)
    
    # Add all root nodes
    for root_name in root_nodes:
        root_node = node(root_name, root_name, False)
        g.addNode(root_node)
        node_map[root_name] = root_node

    # Add edges between parent and child classes with weight 1
    for parent_name, children in class_hierarchy.items():
        # Find parent node in node_map (either by name or ID)
        parent_node = None
        for node_obj in node_map.values():
            if node_obj.name == parent_name or node_obj.id == parent_name:
                parent_node = node_obj
                break
        
        if parent_node is not None:
            for child_name in children:
                # Find child node in node_map
                child_node = None
                for node_obj in node_map.values():
                    if node_obj.name == child_name or node_obj.id == child_name:
                        child_node = node_obj
                        break
                
                if child_node is not None:
                    g.addEdge(parent_node, child_node, 1)  # Add edge with weight 1

    print(g)
    return g
    
    # # Add edges between classes and their subclasses with relationship strengths
    # for i in range(len(weightData)):
    #     weight = weightData.loc[i]
    #     child = node_map[weight.child]
    #     parent = node_map[weight.parent]
    #     weightValue = weight.weight

    #     g.addEdge(parent, child, weightValue) 

def parseSearchString(searchInput):
    # There are three special cases for searches, "", &&, ||
    import re

    terms = re.findall(r'[^|&]+|\||&', searchInput) # Split up initial input
    terms = [term.strip() for term in terms] # Clean up trailing whitespace
    terms = {
        "searchTerms": [t for t in terms if t not in ["|", "&"]],
        "operators": [t for t in terms if t in ["|", "&"]]
    } # Parse info

    # Save search terms in a list so the searchTerms value in the dict can be reinitialized as an empty list
    searchTerms = terms["searchTerms"]
    terms["searchTerms"] = []

    # For each term in search terms, split them up
    for search in searchTerms:    
        if search.startswith('"') and search.endswith('"'): # Check if wrapped in quotes
            terms["searchTerms"].append([search[1:-1]])
        else:
            search = search.split()
            n = len(search)
            result = []

            for i in range(1, 1 << n):
                subset = [search[j] for j in range(n) if (i & (1 << j))]
                result.append(" ".join(subset))

            terms["searchTerms"].append(result)

    return terms

if __name__ == '__main__':
    # Les try a different type of input (for fun)
    rdf_file = sys.argv[1]
    log_state = sys.argv[2] if len(sys.argv) > 2 else 0
    
    # Parse RDF to graph
    graph_ = parse_rdf_to_graph(rdf_file)
    
    # Print graph information
    if log_state != 0:
        print(f"Graph has {len(graph_.getNodes())} nodes and {len(graph_.getEdges())} edges")
        print(graph_)

    # Open config file
    print("opening config...")
    with open('./conf.json', 'r') as file:
        conf = json.load(file)
        print("config opened!")

    # Initialize Neo4j login parameters
    url = conf["url"]
    neo4jauth = (conf["user"], conf["pass"])

    # Get search query and process it.
    searchIn = input("search:")
    search = parseSearchString(searchIn)
    ontologySearch = []

    for search_group in search["searchTerms"]:
        for search_term in search_group:
            # Find matching nodes in the graph that contain the search term
            matching_nodes = [
                node for node in graph_.getNodes() 
                if search_term.lower() in node.name.lower() or 
                search_term.lower() in node.id.lower()
            ]
            
            # Perform ontology search for each matching node
            for matching_node in matching_nodes:
                res_ = ontsearch(edgesum=1, n=1, x=10, startNode=matching_node, traversed=[])
                
                # Add unique node names to ontologySearch
                for result_node in res_:
                    if result_node.name not in ontologySearch:
                        ontologySearch.append(result_node.name)

    print("keywords found:", ontologySearch)

    searchRes = []

    # Connect to neo4j
    with GraphDatabase.driver(url, auth=neo4jauth) as driver:
        # Verify connection, quit if connection doesn't exist.
        try:
            driver.verify_connectivity()
        except:
            print("\033[91mFATAL: Could not connect to neo4j, perhaps it is offline, or you provided the wrong url.\033[0m")
            exit(0)
        
        searchRes = []
        
        # Use ontologySearch results instead of raw search terms
        for ontology_term in ontologySearch:
            print(ontology_term)
            res = []
            query = """
            MATCH (n:keyword)
            WHERE n.name CONTAINS $term OR n.id CONTAINS $term
            MATCH (n)-[m:in]->(l:paper)
            RETURN DISTINCT l.name
            """
            
            records, summary, keys = driver.execute_query(
                query,
                term=ontology_term,
                database_="neo4j"
            )

            for r in records:
                data = r['l.name']
                if data not in res:
                    res.append(data)
            
            searchRes.append(res)

    # Process and return the results based on the operators
    if not searchRes:  # Handle empty results case
        resultSet = []
    else:
        resultSet = set(searchRes[0])  # Start with first set of results
        
        # Apply operators if we have multiple search terms
        if len(searchRes) > 1 and 'operators' in search:
            for index, s in enumerate(searchRes[1:]):
                operator = search["operators"][index] if index < len(search["operators"]) else "||"
                
                if operator == "&&":
                    resultSet &= set(s)  # Intersection
                elif operator == "||":
                    resultSet |= set(s)  # Union

    # Sort the results (Alphabetical)
    resultSet = list(resultSet) 

    print("Result:", resultSet)
    print("Count:", ontologySearch)