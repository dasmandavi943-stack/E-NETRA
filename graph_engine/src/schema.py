import os
import pandas as pd
from dotenv import load_dotenv
from neo4j import GraphDatabase

load_dotenv("graph_engine/.env")

NEO4J_URI = os.getenv("NEO4J_URI", "bolt://localhost:7687")
NEO4J_USER = os.getenv("NEO4J_USER", "neo4j")
NEO4J_PASSWORD = os.getenv("NEO4J_PASSWORD", "password123")

class Neo4jVendorGraph:
    def __init__(self, uri, user, password):
        self.driver = GraphDatabase.driver(uri, auth=(user, password))

    def close(self):
        self.driver.close()

    def create_constraints(self):
        queries = [
            "CREATE CONSTRAINT IF NOT EXISTS FOR (p:Project) REQUIRE p.project_id IS UNIQUE",
            "CREATE CONSTRAINT IF NOT EXISTS FOR (t:Tender) REQUIRE t.tender_id IS UNIQUE",
            "CREATE CONSTRAINT IF NOT EXISTS FOR (c:Contractor) REQUIRE c.contractor_id IS UNIQUE",
            "CREATE CONSTRAINT IF NOT EXISTS FOR (b:BankAccount) REQUIRE b.bank_hash IS UNIQUE",
            "CREATE CONSTRAINT IF NOT EXISTS FOR (a:Address) REQUIRE a.address IS UNIQUE"
        ]
        with self.driver.session() as session:
            for q in queries:
                session.run(q)

    def load_csv(self, csv_path="graph_engine/data/sample_vendors.csv"):
        df = pd.read_csv(csv_path)
        cypher = """
        MERGE (p:Project {project_id: })
          SET p.district = , p.work_category = , p.sanctioned_amount = 
        MERGE (t:Tender {tender_id: })
        MERGE (t)-[:PART_OF]->(p)
        MERGE (c:Contractor {contractor_id: })
          SET c.name = , c.gstin = 
        MERGE (b:BankAccount {bank_hash: })
        MERGE (a:Address {address: })
        MERGE (c)-[:BID_ON {bid_amount: , is_winner: }]->(t)
        MERGE (c)-[:USES_ACCOUNT]->(b)
        MERGE (c)-[:LOCATED_AT]->(a)
        """
        with self.driver.session() as session:
            for _, row in df.iterrows():
                session.run(cypher, **row.to_dict())
        print(f"Loaded {len(df)} records into Neo4j graph database.")

if __name__ == "__main__":
    try:
        graph = Neo4jVendorGraph(NEO4J_URI, NEO4J_USER, NEO4J_PASSWORD)
        graph.create_constraints()
        graph.load_csv()
        graph.close()
    except Exception as e:
        print(f"Neo4j server not running locally yet ({e}). Local NetworkX graph engine is ready to use!")
