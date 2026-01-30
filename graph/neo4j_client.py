import os, logging
try:
    from neo4j import GraphDatabase
except:
    GraphDatabase = None

logger = logging.getLogger(__name__)

class Neo4jClient:
    def __init__(self, uri=None, user=None, password=None):
        uri = uri or os.getenv("NEO4J_URI", "bolt://localhost:7687")
        user = user or os.getenv("NEO4J_USER", "neo4j")
        password = password or os.getenv("NEO4J_PASSWORD", "password")

        if GraphDatabase is None:
            logger.warning("neo4j driver not available; Neo4jClient will be a no-op.")
            self.driver = None
            return

        try:
            self.driver = GraphDatabase.driver(uri, auth=(user, password))
            self.driver.verify_connectivity() # Verify actual connection
        except Exception as e:
            logger.warning(f"Failed to create neo4j driver or connect: {e}")
            self.driver = None

    def _is_available(self):
        return self.driver is not None

    def store_entities(self, entities):
        if not self._is_available():
            return
        try:
            with self.driver.session() as session:
                for category in entities.values():
                    for entity in category:
                        session.run(
                            "MERGE (e:Entity {id: $id, type: $type})",
                            id=entity["entity_id"],
                            type=entity["type"]
                        )
        except Exception as e:
            logger.error(f"Failed to store entities: {e}")

    def store_relationships(self, relationships):
        if not self._is_available():
            return
        try:
            with self.driver.session() as session:
                for rel in relationships:
                    session.run("""
                        MATCH (a:Entity {id: $from}), (b:Entity {id: $to})
                        MERGE (a)-[:RELATION {type: $type}]->(b)
                    """, **rel)
        except Exception as e:
            logger.error(f"Failed to store relationships: {e}")

    def store_exposures(self, exposures):
        if not self._is_available():
            return
        try:
            with self.driver.session() as session:
                for exp in exposures:
                    session.run("""
                        MATCH (e:Entity {id: $entity})
                        MERGE (x:Exposure {id: $id, type: $type})
                        MERGE (e)-[:HAS_EXPOSURE]->(x)
                    """, id=exp["exposure_id"], type=exp["type"], entity=exp["entity"])
        except Exception as e:
            logger.error(f"Failed to store exposures: {e}")
    
    def get_graph_data(self):
        """Get graph data for visualization"""
        if not self._is_available():
            return {"nodes": [], "links": []}
        
        try:
            with self.driver.session() as session:
                result = session.run("""
                    MATCH (a)-[r]->(b)
                    RETURN a.id AS source, a.type AS source_type,
                           b.id AS target, b.type AS target_type,
                           type(r) AS relationship
                    LIMIT 100
                """)
                
                nodes = {}
                links = []
                
                for record in result:
                    source = record["source"]
                    target = record["target"]
                    
                    if source not in nodes:
                        nodes[source] = {
                            "id": source,
                            "type": record.get("source_type", "Unknown")
                        }
                    if target not in nodes:
                        nodes[target] = {
                            "id": target,
                            "type": record.get("target_type", "Unknown")
                        }
                    
                    links.append({
                        "source": source,
                        "target": target,
                        "type": record["relationship"]
                    })
                
                return {"nodes": list(nodes.values()), "links": links}
        except Exception as e:
            logger.error(f"Failed to get graph data: {e}")
            return {"nodes": [], "links": []}