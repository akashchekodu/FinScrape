import os
from dotenv import load_dotenv
from neo4j import GraphDatabase

load_dotenv()

URI = os.getenv("NEO4J_URI")
AUTH = (os.getenv("NEO4J_USER"), os.getenv("NEO4J_PASS"))

# Check connection
with GraphDatabase.driver(URI, auth=AUTH) as driver:
    driver.verify_connectivity()
    print("✅ Connected to Neo4j")

class KGBuilder:
    def __init__(self, uri, user, password):
        self.driver = GraphDatabase.driver(uri, auth=(user, password))

    def close(self):
        self.driver.close()

    def add_triple(self, subject, predicate, obj):
        with self.driver.session() as session:
            session.write_transaction(self._create_triple, subject.lower(), predicate.lower(), obj.lower())

    @staticmethod
    def _create_triple(tx, subj, pred, obj):
        tx.run(f"""
            MERGE (s:Entity {{name: $subj}})
            MERGE (o:Entity {{name: $obj}})
            MERGE (s)-[:{pred.upper()}]->(o)
        """, subj=subj, obj=obj)

# ✅ Connect using remote Neo4j URI and credentials
kg = KGBuilder(URI, AUTH[0], AUTH[1])

triples = [
    {
        "subject": "Apple",
        "predicate": "acquired",
        "object": "DarwinAI",
    },
    {
        "subject": "DarwinAI",
        "predicate": "operates_in_sector",
        "object": "Artificial Intelligence",
    },
    {
        "subject": "SpaceX",
        "predicate": "operates_in_sector",
        "object": "Satellite Communications",
    }
]

for triple in triples:
    kg.add_triple(triple["subject"], triple["predicate"], triple["object"])

kg.close()
