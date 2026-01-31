from dotenv import load_dotenv
import os
from neo4j import GraphDatabase

load_dotenv()

uri = os.getenv("NEO4J_URI", "bolt://localhost:7687")
user = os.getenv("NEO4J_USER", "neo4j")
password = os.getenv("NEO4J_PASSWORD", "password")

print(f"Testing Config: URI={uri}, User={user}, Password={'*' * len(password)}")

try:
    driver = GraphDatabase.driver(uri, auth=(user, password))
    with driver.session() as session:
        result = session.run("RETURN 1 AS num")
        record = result.single()
        print(f"Connection Successful! Result: {record['num']}")
    driver.close()
except Exception as e:
    print(f"Connection Failed: {e}")
