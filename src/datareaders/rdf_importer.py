# ephemera

# import
import rdflib # rdflib
from neo4j import GraphDatabase # neo4j
from urllib.parse import urlparse
import json # Config

def queryDatabase(driver, query):
    records, summary, keys = driver.execute_query(
        query,
        database_="neo4j",
    )

    return [records, summary, keys]

def getRelationships(g, classes, relation):
    res = []
    for s, p, o in g.triples((None, relation, None)): # get triples with a certain relation
        s = str(s)
        o = str(o)
        if s in classes and o in classes:
            res.append((classes[s], classes[o]))

    return res

# parse rdf and return a dict
def parseRdf(fPath):
    # Initialize graph and parse file
    g = rdflib.Graph().parse(fPath, format="xml")

    # Get classes
    classes = {}
    for s, p, o in g.triples((None, rdflib.RDF.type, rdflib.OWL.Class)):
        classUrl = str(s)
        className = urlparse(classUrl).fragment
        classes[classUrl] = className
    
    # Get subclass and disjoint relationships
    subclasses = getRelationships(g, classes, rdflib.RDFS.subClassOf)
    disjoints = getRelationships(g, classes, rdflib.OWL.disjointWith)
    
    # Return dict
    return {
        'classes': list(classes.values()),
        'subclasses': subclasses,
        'disjoints': disjoints
    }

# Import to neo4j
def importToNeo4j(data, conf):
    # Initialize Neo4j login parameters and login
    url = conf["url"]
    neo4jauth = (conf["user"], conf["pass"])

    with GraphDatabase.driver(url, auth=neo4jauth) as driver:
        # Verify connection, quit if connection doesn't exist.
        try:
            driver.verify_connectivity()
        except:
            print("\033[91mFATAL: Could not connect to neo4j, perhaps it is offline, or you provided the wrong url.\033[0m")
            exit(0)

        # clear data
        query = "match (n) detach delete n"

        # create class nodes
        query = "create"
        for classN in data["classes"]:
            query += " (:Class {name: \"%s\"})," % (classN)

        queryDatabase(driver, query[:-1])

        # create subclass relations
        for sub, sup in data["subclasses"]:
            query = """
                MATCH (sub:Class {name: \"%s\"})
                MATCH (sup:Class {name: \"%s\"})
                CREATE (sub)-[:SUBCLASS_OF]->(sup)
            """ % (sub, sup)

            queryDatabase(driver, query)

        # create disjoint relationships
        for a, b in data["subclasses"]:
            query = """
                MATCH (a:Class {name: \"%s\"})
                MATCH (b:Class {name: \"%s\"})
                CREATE (a)-[:DISJOINT_WITH]->(b)
            """ % (a, b)

            queryDatabase(driver, query)

        print("Data imported.")

if __name__ == "__main__":
    # path to rdf
    fPath = "C:/Users/davep/Downloads/bismila.rdf"
    
    # parse rdf
    data = parseRdf(fPath)
    
    # print extracted data
    print("Classes:", data['classes'])
    print("Subclass relations:", data['subclasses'])
    print("Disjoint relations:", data['disjoints'])

    # Open config file
    print("opening config...")
    with open('../../conf.json', 'r') as file:
        conf = json.load(file)
    
    # Import to Neo4j
    importToNeo4j(data, conf)