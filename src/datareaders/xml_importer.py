# ephemera
# Convert xml to Neo4j Nodes
# IMPORTANT - assumes the neo4j database you are pushing into is empty

# import
import xml.etree.ElementTree as ET # XML
import pandas as pd # Pandas
import json # Config
from neo4j import GraphDatabase # Neo4j

# Take input
fPath = input("Please enter filepath to xml file:")

# Get the xml tree
tree = ET.parse(fPath)
# Get the root node
root = tree.getroot()

rawData = []

# Go through each "paper" node in the tree
for paper in root.findall("paper"):
    print(paper.attrib)
    name = paper.attrib["title"]
    batch = paper.attrib["batch"]
    address = paper.attrib["address"]
    authors = paper.attrib["authors"]
    keywords = paper.findall("keyword")
    keywords_ = []

    # Convert node array to text array
    for i in keywords:
        keywords_.append(i.text)

    # Add to data
    rawData.append({
        "title": name,
        "batch": batch,
        "address": address,
        "authors": authors,
        "keywords": keywords_
    })

# Convert raw data to dataframe
dataframe = pd.DataFrame(rawData)

# Open config file
print("opening config...")
with open('../../conf.json', 'r') as file:
    conf = json.load(file)

# Initialize Neo4j login parameters
url = conf["url"]
neo4jauth = (conf["user"], conf["pass"])

# Connect to neo4j
with GraphDatabase.driver(url, auth=neo4jauth) as driver:
    # Verify connection
    driver.verify_connectivity()

# PAPERS TO NODES

    print("creating paper nodes...")

    # Begin query
    query = "CREATE"

    # Add each paper to query
    for i in range(len(dataframe)):
        # Get research paper data
        paper = dataframe.loc[i]

        # Add to query
        query += ' (:paper {name:"' + str(paper.title) + '", authors:"' + str(paper.authors) + '", batch:"' + str(paper.batch) + '", address:"' + str(paper.address) +'"}),'

    # Get rid of the trailing comma (intentional)
    query = query[:-1]

    # Records store data, summary stores query
    # Send query to Neo4j Database
    records, summary, keys = driver.execute_query(
            query,
            database_="neo4j",
    )

# KEYWORDS TO NODES

    print("creating keyword nodes...")

    query = "CREATE"
    keywords = []

    for i in range(len(dataframe)):
        # Get research paper data
        paper = dataframe.loc[i]

        # Get all keywords from paper and put in list
        keywords_ = paper.keywords

        # Check each keyword if in the master keywords list, if not, add it.
        for j in keywords_:
            if j not in keywords:
                keywords.append(j)

    # create keyword nodes
    for i in keywords:
        query += ' (:keyword {name:"' + i + '"}),'

    # get rid of trailing comma (intentional)
    query = query[:-1]

    # Send query to Neo4j Database
    records, summary, keys = driver.execute_query(
            query,
            database_="neo4j",
    )

# KEYWORD -> PAPER RELATIONSHIPS

    print("creating relationships...")

    # For each node in keywords, connect papers
    for i in keywords:
        # Begin query
        query = 'MATCH (k:keyword {name:"' + i + '"}) MATCH(p:paper) WHERE p.name in ['

        # loop through each paper
        for j in range(len(dataframe)):
            # Get research paper data
            paper = dataframe.loc[j]

            # Get all keywords from paper and put in list
            keywords_ = paper.keywords

            # If the paper has the keyword, add its title to the query
            if i in keywords_:
                query += ' "' + str(paper.title) + '",'

        # Remove trailing comma, add the create relationships to the query
        query = query[:-1] + "] CREATE (k) -[:in]-> (p)"
        
        # Send query to Neo4j Database
        records, summary, keys = driver.execute_query(
            query,
            database_="neo4j",
        )

    print("done !")