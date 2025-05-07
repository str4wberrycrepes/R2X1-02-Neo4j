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
import csv

from symspellpy.symspellpy import SymSpell, Verbosity # spell checking

import sys  # sys

from neo4j import GraphDatabase # Neo4j
import json # Config

def graphSearch(ontGraph, edgeSummation, nodeCount, decayFactor, currentNode, traversed, subclassEdges, penalty=0.95, svThreshold=0.83):
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
    if not untraversedNeighbors or sv < svThreshold:  # More lenient threshold
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
            graphSearch(ontGraph, edgeSummation, nodeCount, decayFactor, neighbor, traversed, subclassEdges, penalty, svThreshold)
    
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
    subclassEdges = set()  # This will store the subclass relationships
    
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
    equivalentMap = defaultdict(list)
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
        else:  # sanaol may label.
            label = label.text
            rdfNode["name"] = label

        # Check for keywordStatus
        isKeyword = cls.find('./rdfs:comment', namespaces)
        if isKeyword is not None and isKeyword.text == "KEYWORD":
            rdfNode["isKeyword"] = True
        else:
            rdfNode["isKeyword"] = False

        # create a node from the extracted data and add it to the graph
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

        # Check for equivalentClass relationship
        equivalents = cls.findall('./owl:equivalentClass', namespaces)
        for equivalent in equivalents:
            equivUri = equivalent.attrib.get('{http://www.w3.org/1999/02/22-rdf-syntax-ns#}resource', '')
            if equivUri:
                equivId = extractClassName(equivUri)
                equivalentMap[classId].append(equivId)
                equivalentMap[equivId].append(classId)  # bidirectional

    # TEMPORARY
    # Add subclass edges (distinct from equivalent edges)
    for nodeParentName, children in classEdgeMap.items():
        parentNode = next((n for n in nodeMap.values() if n.name == nodeParentName or n.id == nodeParentName), None)
        if parentNode:
            for childName in children:
                childNode = next((n for n in nodeMap.values() if n.name == childName or n.id == childName), None)
                if childNode:
                    rdfGraph.addEdge(parentNode, childNode, 1)
                    subclassEdges.add((childNode.name, parentNode.name))  # Only add for subclass edges

    # Add equivalentClass edges (distinct from subclass edges)
    for sourceName, equivalents in equivalentMap.items():
        sourceNode = next((n for n in nodeMap.values() if n.name == sourceName or n.id == sourceName), None)
        if sourceNode:
            for targetName in equivalents:
                targetNode = next((n for n in nodeMap.values() if n.name == targetName or n.id == targetName), None)
                if targetNode:
                    rdfGraph.addEdge(sourceNode, targetNode, 1)  # You can adjust weight if needed

    return rdfGraph, subclassEdges

def exportRelationshipsToExcel(rdfGraph, subclassEdges, output_path="relationships.xlsx"):
    import pandas as pd
    relationships = []

    for edge in rdfGraph.getEdges():
        parent = edge[0].name
        child = edge[1].name
        weight = edge[2]

        relationships.append({
            "parent": parent,
            "child": child,
            "weight": weight
        })

    df = pd.DataFrame(relationships)
    df.to_excel(output_path, index=False)
    print(f"\033[92mRelationship data exported to {output_path}\033[0m")

def applyEdgeWeightsFromCSV(graph, csv_path):
    with open(csv_path, mode='r') as f:
        reader = csv.DictReader(f)
        for row in reader:
            source = row['parent']
            target = row['child']
            try:
                weight = float(row['weight'])
            except ValueError:
                continue  # skip invalid weights

            sourceNode = next((n for n in graph.getNodes() if n.id == source or n.name == source), None)
            targetNode = next((n for n in graph.getNodes() if n.id == target or n.name == target), None)

            if sourceNode and targetNode:
                # Update the edge if it exists (undirected graph, so check both directions)
                if graph.checkForEdge(sourceNode, targetNode):
                    graph.graph[sourceNode][targetNode] = weight
                    graph.graph[targetNode][sourceNode] = weight
                else:
                    # Add the edge if it doesn't exist
                    graph.addEdge(sourceNode, targetNode, weight)

                    # === START OF GOLDEN STANDARD EVALUATION ===
import pandas as pd


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
    exportRelationshipsToExcel(ontGraph, subclassEdges)
    
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

    queries = ["3d printing", "abaca fibers", "abaca fibers compound", "aerodynamics", "biomimetics", "biomimicry", "drug delivery", "machine learning", "sea lion-inspired", "snake robot", "sustainable energy", "tubercles wind turbine", "dengue", "forecasting", "heavy metal pollution",  "material science", "polypropylene", "sustainable energy", "dissolvable graphene-oxide silica nanohybrid microneedle", "filament making", "high-level quantum programming", "phtochromism", "microneedle", "biosorption santol peels", "photochromic", "photochromic", "block-based programming languages", "simple quantum computing", "snake drone", "composite materials", "biosorbent Sandorium koetjape"]

    aveP = 0
    aveR = 0
    aveF = 0



    for i in queries:

        # Get search query and process it.
        searchIn = i
        search = parseSearchString(searchIn)

        sym_spell = initializeSymspell()
        if sym_spell:
            for x in search["searchTerms"]:
                for term in x:
                    suggestions = sym_spell.lookup(term, Verbosity.CLOSEST, max_edit_distance=2)
                    if suggestions and suggestions[0].term.lower() != term.lower():
                        print(f"\033[93mCouldn't find '{term}'. Did you mean '{suggestions[0].term}'?\033[0m")

        applyEdgeWeightsFromCSV(ontGraph, "C:/Users/davep/Downloads/edgeweights.csv")

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

        # print("keywords found:", ontologySearch)

        searchRes = []

        if i=="forecasting":
            print("wawa", ontologySearch)

        # Connect to neo4j
        with GraphDatabase.driver(url, auth=neo4jauth) as driver:
            # Verify connection, quit if connection doesn't exist.
            try:
                driver.verify_connectivity()
            except:
                # print("\033[91mFATAL: Could not connect to neo4j, perhaps it is offline, or you provided the wrong url.\033[0m")
                exit(0)
            
            searchRes = []
            
            # Use ontologySearch results instead of raw search terms
            for ontology_term in ontologySearch:
                # print(ontology_term)
                res = []
                query = """
                MATCH (n:keyword)
                WHERE n.name CONTAINS $term OR n.id CONTAINS $term
                MATCH (n)-[m:in]->(l:paper)
                RETURN DISTINCT l.rescode
                """
                
                records, summary, keys = driver.execute_query(
                    query,
                    term=ontology_term,
                    database_="neo4j"
                )

                # Optionally: silence notifications in your own logs
                if summary.notifications:
                    summary.notifications.clear()  # Optional: suppress in custom log display

                for r in records:
                    data = r['l.rescode']
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

        # print("Result:", resultSet)
        # print("Count:", ontologySearch)

        # Load golden standard CSV
        gold_path = "C:/Users/davep/Downloads/Golden_Standard_Semantic_Loose_Matching_CLEANED.csv"
        gold_df = pd.read_csv(gold_path)

        # Ask for the original user query used for this search
        raw_query = searchIn

        # Filter expected codes from the golden standard
        expected_codes = gold_df[gold_df["Query"].str.lower() == raw_query]["Code"].dropna().unique().tolist()
        retrieved_codes = resultSet  # This is your final system result

        # Convert to sets for comparison
        expected_set = set(expected_codes)
        retrieved_set = set(resultSet)

        # Calculate true positives, false positives, and false negatives
        tp = len(expected_set & retrieved_set)
        fp = len(retrieved_set - expected_set)
        fn = len(expected_set - retrieved_set)

        # Special case: both sets are empty (nothing expected, nothing retrieved)
        if not expected_set and not retrieved_set:
            precision = recall = f1_score = 1.0
        else:
            precision = tp / (tp + fp) if (tp + fp) > 0 else 0.0
            recall = tp / (tp + fn) if (tp + fn) > 0 else 0.0
            f1_score = (2 * precision * recall) / (precision + recall) if (precision + recall) > 0 else 0.0

        # Output results
        # print(f"\n=== EVALUATION RESULTS for query '{raw_query}' ===")
        # print(f"Expected codes: {sorted(expected_codes)}")
        # print(f"Retrieved codes: {sorted(retrieved_codes)}")
        # print(f"True Positives: {tp}, False Positives: {fp}, False Negatives: {fn}")
        # print(f"Precision: {precision:.4f}")
        # print(f"Recall: {recall:.4f}")
        # print(f"F1 Score: {f1_score:.4f}")

        with open("demofile.txt", "a") as f:
            f.write(f"\n=== EVALUATION RESULTS for query '{raw_query}' ===")
            f.write(f"\nExpected codes: {sorted(expected_codes)}")
            f.write(f"\nRetrieved codes: {sorted(retrieved_codes)}")
            f.write(f"\nTrue Positives: {tp}, False Positives: {fp}, False Negatives: {fn}")
            f.write(f"\nPrecision: {precision:.4f}")
            f.write(f"\nRecall: {recall:.4f}")
            f.write(f"\nF1 Score: {f1_score:.4f}")

        aveP += precision
        aveR += recall
        aveF += f1_score
        # === END OF GOLDEN STANDARD EVALUATION ===

    print("ave. precision:" + str(aveP/len(queries)), "ave. recall:" + str(aveR/len(queries)), "ave. f1_score:" + str(aveF/len(queries)))
