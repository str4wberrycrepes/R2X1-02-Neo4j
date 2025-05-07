# ephemera

# how to run the program
# cd Neo4j
# python -m src.search.search C:\Users\davep\Downloads\ont1.rdf [or whatever the path to your rdf is]

# Don't remove kailangan magrelapse ng code para gumana
# Paano kung magmahal ka ng isang taong bawal mahalin? Sapagkat siya ay nakalaan na para sa iba...
# Tatanggapin mo ba siyang mawala para hindi magkasala?
# O handa kang magkasala, huwag lang siyang mawala?

# import
from ..traverse.graph import graph, node # undirected weighted graph
import xml.etree.ElementTree as ET
from collections import defaultdict
import pandas

from symspellpy.symspellpy import SymSpell, Verbosity # spell checking

import sys  # sys

from neo4j import GraphDatabase # Neo4j
import json # Config

def graphSearch(ontGraph, edgeSummation, nodeCount, decayFactor, currentNode, traversed, subclassEdges, penalty=0.95):
    # Since I like to tweak, get the actual node if what I input is a string.
    # For reals, we do this so we can just run graphSearch using a node's name or id
    if isinstance(currentNode, str):
        currentNode = next((n for n in ontGraph.getNodes() if n.name == currentNode or n.id == currentNode), None)
        if not currentNode:
            return traversed
        
    # Check if we've already visited this node
    if any(n.name == currentNode.name for n in traversed):
        return traversed
    # If not, add it to traversed so we don't go over it again
    traversed.append(currentNode)
    
    # Get neighbors that haven't been traversed
    neighbors = ontGraph.getNeighbors(currentNode)
    untraversedNeighbors = [
        n for n in neighbors 
        if not any(t.name == n.name for t in traversed)
    ]
    
    # Calculate current search value
    sv = edgeSummation / (nodeCount * decayFactor) if (nodeCount * decayFactor) != 0 else 0

    # print(f"Search value (sv): {sv}")
    
    # Base case - stop if no neighbors or sv too low
    if not untraversedNeighbors or sv < 0.95:  # More lenient threshold
        return traversed
    else:
        # Recursive case
        for neighbor in untraversedNeighbors:
            edgeWeight = neighbors[neighbor]
            isGoingToParent = (currentNode.name, neighbor.name) in subclassEdges
            trueWeight = edgeWeight * penalty if isGoingToParent else edgeWeight

            # print(f"Traversing from '{currentNode.name}' to '{neighbor.name}' ({"↑" if isGoingToParent else "↓"}), base weight: {edgeWeight}, adjusted: {trueWeight}")

            edgeSummation += trueWeight
            nodeCount +=  1
            print(traversed)
            graphSearch(ontGraph, edgeSummation, nodeCount, decayFactor, neighbor, traversed, subclassEdges, penalty)
    
    return traversed

# function to extract class names from rdf uri
def extractClassName(uri):
    if '#' in uri:
        return uri.split('#')[-1]
    else:
        # For URIs without a fragment identifier, use the last path component
        parts = uri.strip('/').split('/')
        return parts[-1]

# parsing OWL RDF into a weighted graph
def parseRdfToGraph(rdfFile):
    # Initialize graph and subclass edges
    rdfGraph = graph()
    subclassEdges = set() # I won't lie I just couldn't be bothered to build around the classEdgeMap variable
    
    # Parse RDF file
    tree = ET.parse(rdfFile)
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
    classEdgeMap = defaultdict(list)
    nodeMap = {}

    # Add all classes as nodes first
    for cls in classes:
        className = cls.attrib.get('{http://www.w3.org/1999/02/22-rdf-syntax-ns#}about', '')
        rdfNode = {}
        if className:
            classId = extractClassName(className)
            rdfNode["id"] = classId

        # Check for label
        label = cls.find('./rdfs:label', namespaces)
        if label is None:
            continue
        else: # sanaol may label.
            label = label.text
            rdfNode["name"] = label

        # Check for keywordStatus
        isKeyword = cls.find('./rdfs:comment', namespaces)
        if isKeyword is not None and isKeyword.text == "KEYWORD":
            rdfNode["isKeyword"] = True
        else:
            rdfNode["isKeyword"] = False

        # create a node from the extracted data and add it to the grapph
        rdfNodeObj = node(rdfNode["name"], rdfNode["id"], rdfNode["isKeyword"]) 
        rdfGraph.addNode(rdfNodeObj)
        nodeMap[rdfNode["name"]] = rdfNodeObj 
        
        # Check for subClassOf relationship
        subclasses = cls.findall('./rdfs:subClassOf', namespaces)
        for subclassOf in subclasses:
            nodeParent = subclassOf.attrib.get('{http://www.w3.org/1999/02/22-rdf-syntax-ns#}resource', '')
            if nodeParent:
                nodeParentName = extractClassName(nodeParent)
                classEdgeMap[nodeParentName].append(classId)

    # TEMPORARY
    # Add edges between parent and child classes with weight 1 for now
    for nodeParentName, children in classEdgeMap.items():
        # Find parent node in nodeMap (either by name or ID)
        parentNode = None
        for rdfNodeObj in nodeMap.values():
            if rdfNodeObj.name == nodeParentName or rdfNodeObj.id == nodeParentName:
                parentNode = rdfNodeObj
                break
        
        if parentNode is not None:
            for childName in children:
                # Find child node in nodeMap
                childNode = None
                for rdfNodeObj in nodeMap.values():
                    if rdfNodeObj.name == childName or rdfNodeObj.id == childName:
                        childNode = rdfNodeObj
                        break
                
                if childNode is not None:
                    rdfGraph.addEdge(parentNode, childNode, 1)  # Add edge with weight 1
                    subclassEdges.add((childNode.name, parentNode.name))

    return rdfGraph, subclassEdges

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

def initializeSymspell():
    max_edit_distance = 2
    prefix_length = 7
    sym_spell = SymSpell(max_edit_distance, prefix_length)

    # Load dictionary
    dictionary_path = "D:/Shoko/dev/src/R2X1-02/symspell_frequency_dictionary.txt"  # You can place this locally
    term_index = 0  # column of the term
    count_index = 1  # column of the word frequency

    if not sym_spell.load_dictionary(dictionary_path, term_index, count_index, separator = "|"):
        print("Dictionary file not found")
        return None
    return sym_spell


if __name__ == '__main__':
    # Les try a different type of input (for fun)
    rdfFile = sys.argv[1]
    log_state = sys.argv[2] if len(sys.argv) > 2 else 0
    
    # Parse RDF to graph
    ontGraph, subclassEdges = parseRdfToGraph(rdfFile)
    
    # Print graph information
    if log_state != 0:
        print(f"Graph has {len(ontGraph.getNodes())} nodes and {len(ontGraph.getEdges())} edges")
        print(ontGraph)

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

    sym_spell = initializeSymspell()
    if sym_spell:
        for x in search["searchTerms"]:
            for term in x:
                suggestions = sym_spell.lookup(term, Verbosity.CLOSEST, max_edit_distance=2)
                if suggestions and suggestions[0].term.lower() != term.lower():
                    print(f"\033[93mCouldn't find '{term}'. Did you mean '{suggestions[0].term}'?\033[0m")


    ontologySearch = []

    for searchGroup in search["searchTerms"]:
        for searchTerm in searchGroup:
            searchNodes = [
                node for node in ontGraph.getNodes() 
                if searchTerm.lower() in node.name.lower() or 
                searchTerm.lower() in node.id.lower()
            ]
            
            # Perform ontology search for each matching node
            for searchNode in searchNodes:
                res_ = graphSearch(ontGraph=ontGraph, edgeSummation=1, nodeCount=1, decayFactor=1.2, currentNode=searchNode, traversed=[], subclassEdges=subclassEdges)
                
                # Add unique node names to ontologySearch
                for resultNode in res_:
                    if resultNode.name not in ontologySearch:
                        ontologySearch.append(resultNode.name)

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