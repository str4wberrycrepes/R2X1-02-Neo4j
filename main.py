# if docker container doesn't exist:
#   docker-compose up -d

# oh my gah
from neo4j import GraphDatabase
import json

with open('conf.json', 'r') as file:
    conf = json.load(file)

# Connect to the database
url = conf["url"]
neo4jauth = (conf["user"], conf["pass"])

with GraphDatabase.driver(url, auth=neo4jauth) as driver:
    #Verify connection
    driver.verify_connectivity()

    # #Records store data, summary stores query
    # records, summary, keys = driver.execute_query(
    #         "MATCH (n:user) RETURN n.name AS name",
    #         database_="neo4j",
    # )

    # #take input and make a node if it doesn't exist, if it does, return its data
    # for record in records:
    #     inp = input()
    #     if(record.data()['name'] == inp):
    #         print("yuh")