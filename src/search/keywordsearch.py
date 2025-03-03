# ephemera

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
    # import
    from neo4j import GraphDatabase # Neo4j
    import json # Config

    # Open config file
    print("opening config...")
    with open('../../conf.json', 'r') as file:
        conf = json.load(file)
        print("config opened!")

    # Initialize Neo4j login parameters
    url = conf["url"]
    neo4jauth = (conf["user"], conf["pass"])

    # Get search query and process it.
    searchIn = input("search:")
    search = parseSearchString(searchIn)

    searchRes = []

    # Connect to neo4j
    with GraphDatabase.driver(url, auth=neo4jauth) as driver:
        # Verify connection, quit if connection doesn't exist.
        try:
            driver.verify_connectivity()
        except:
            print("\033[91mFATAL: Could not connect to neo4j, perhaps it is offline, or you provided the wrong url.\033[0m")
            exit(0)
        
        for s_ in search["searchTerms"]:
            res = []
            for s in s_:
                query = 'match(n:keyword)'
                query += 'where n.name CONTAINS "' + s + '"'
                query += """
                match(n) -[m:in]-> (l:paper)
                return n,m,l
                """

                records, summary, keys = driver.execute_query(
                    query,
                    database_ = "neo4j"
                )


                for r in records:
                    data = r.data()['l']['rescode']
                    if data not in res:
                        res.append(data)

            searchRes.append(res)
                    

    # Process and return the results based on the operators
    resultSet = set(searchRes[0])  # We begin the operations with the first set

    for index, s in enumerate(searchRes[1:]):  # We loop through the second set and onwards
        operator = search["operators"][index]  # Get the operator
        
        # Handle the operations
        if operator == "&&":
            resultSet &= set(s)  # Intersection
        elif operator == "||":
            resultSet |= set(s)  # Union

    # Sort the results (Alphabetical)
    resultSet = list(resultSet) 
    resultSet.sort()

    print("Result:", resultSet)  # Bask in glory