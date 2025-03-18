# ephemera

# import
import rdflib # rdflib
from neo4j import GraphDatabase # neo4j
from urllib.parse import urlparse
import json # Config

# parse rdf and return a dict
def parseRdf(fPath):
    # Initialize graph and parse file
    g = rdflib.Graph()
    g.parse(fPath, format="xml") # formatted in xml
    
    # use g.triples to filter datatypes (I think this is how you're supposed to do it)
    # Get classes
    classes = {}
    for s, p, o in g.triples((None, rdflib.RDF.type, rdflib.OWL.Class)):
        classUrl = str(s)
        className = urlparse(classUrl).fragment
        classes[classUrl] = className
    
    # Get subclass and disjoint relationships
    subclasses = []
    for s, p, o in g.triples((None, rdflib.RDFS.subClassOf, None)):
        s = str(s)
        o = str(o)
        if s in classes and o in classes:
            subclasses.append((classes[s], classes[o]))

    disjoints = []
    for s, p, o in g.triples((None, rdflib.OWL.disjointWith, None)):
        s = str(s)
        o = str(o)
        if s in classes and o in classes:
            disjoints.append((classes[s], classes[o]))
    
    # Return dict
    return {
        'classes': list(classes.values()),
        'subclasses': subclasses,
        'disjoints': disjoints
    }

# Import to neo4j
def importToNeo4j(data, conf):
    # Initialize Neo4j login parameters
    url = conf["url"]
    neo4jauth = (conf["user"], conf["pass"])

    # Connect to neo4j
    with GraphDatabase.driver(url, auth=neo4jauth) as driver:
        # Verify connection, quit if connection doesn't exist.
        try:
            driver.verify_connectivity()
        except:
            print("\033[91mFATAL: Could not connect to neo4j, perhaps it is offline, or you provided the wrong url.\033[0m")
            exit(0)

        # clear data
        query = "match (n) detach delete n"

        records, summary, keys = driver.execute_query(
            query,
            database_="neo4j",
        )

        # create class nodes
        query = "create"
        for classN in data["classes"]:
            query += " (:Class {name: \"%s\"})," % (classN)

        records, summary, keys = driver.execute_query(
            query[:-1],
            database_="neo4j",
        )

        # create subclass relations
        for sub, sup in data["subclasses"]:
            query = """
                MATCH (sub:Class {name: \"%s\"})
                MATCH (sup:Class {name: \"%s\"})
                CREATE (sub)-[:SUBCLASS_OF]->(sup)
            """ % (sub, sup)

            records, summary, keys = driver.execute_query(
                query,
                database_="neo4j",
            )

        # create disjoint relationships
        for a, b in data["subclasses"]:
            query = """
                MATCH (a:Class {name: \"%s\"})
                MATCH (b:Class {name: \"%s\"})
                CREATE (a)-[:DISJOINT_WITH]->(b)
            """ % (a, b)

            records, summary, keys = driver.execute_query(
                query,
                database_="neo4j",
            )

        print("Data imported.")

# Main execution
def main():
    # Path to the RDF file
    fPath = "C:/Users/davep/Downloads/bismila.rdf"  # Update with your file path
    
    # Parse the RDF file
    data = parseRdf(fPath)
    
    # Print extracted data
    print("Classes:", data['classes'])
    print("Subclass relations:", data['subclasses'])
    print("Disjoint relations:", data['disjoints'])

    # Open config file
    print("opening config...")
    with open('../../conf.json', 'r') as file:
        conf = json.load(file)
    
    # Import to Neo4j
    importToNeo4j(data, conf)

if __name__ == "__main__":
    main()