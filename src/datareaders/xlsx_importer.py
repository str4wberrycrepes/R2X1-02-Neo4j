# ephemera

# For importing research paper table into neo4j nodes
# IMPORTANT - assumes the neo4j database you are pushing into is empty

# import
from neo4j import GraphDatabase # Neo4j
import pandas # Pandas
import json # Config

# Take filepath to excel file
excelFilePath = input("Enter filepath to excel file:")

# Open config file
print("opening config...")
with open('../../conf.json', 'r') as file:
    conf = json.load(file)

# Initialize Neo4j login parameters
url = conf["url"]
neo4jauth = (conf["user"], conf["pass"])

# Import data using panda
print("reading excel file...")
data = pandas.read_excel(excelFilePath)

# Connect to neo4j
with GraphDatabase.driver(url, auth=neo4jauth) as driver:
    # Verify connection
    driver.verify_connectivity()

# PAPERS TO NODES

    print("creating paper nodes...")

    # Begin query
    query = "CREATE"

    print(data)

    # Add each paper to query
    for i in range(len(data)):
        # Get research paper data
        paper = data.loc[i]

        # Add to query
        query += ' (:paper {name:"' + str(paper.title) + '", rescode:"' + str(paper.batch) + "_" + paper.rescode + '", authors:"' + str(paper.authors) + '", batch:"' + str(paper.batch) + '"}),'
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

    for i in range(len(data)):
        # Get research paper data
        paper = data.loc[i]

        # Get all keywords from paper and put in list
        keywords_ = []
        keywords_ = paper.keywords.split(", ")

        # Check each keyword if in the master keywords list, if not, add it.
        for j in keywords_:
            if j not in keywords:
                keywords.append(j) #O(n^2) t.c.

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
        for j in range(len(data)):
            # Get research paper data
            paper = data.loc[j]

            # Get all keywords from paper and put in list
            keywords_ = []
            keywords_ = paper.keywords.split(", ")

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