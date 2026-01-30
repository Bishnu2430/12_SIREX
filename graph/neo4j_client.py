import os
import logging

try:
    from neo4j import GraphDatabase
except Exception:
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
        except Exception as e:
            logger.exception("Failed to create neo4j driver; Neo4jClient will be a no-op: %s", e)
            self.driver = None

    def _is_available(self):
        return self.driver is not None

    def store_entities(self, entities):
        if not self._is_available():
            logger.debug("store_entities called but driver unavailable; skipping")
            return

        with self.driver.session() as session:
            for category in entities.values():
                for entity in category:
                    session.run(
                        "MERGE (e:Entity {id: $id, type: $type})",
                        id=entity["entity_id"],
                        type=entity["type"]
                    )

    def store_relationships(self, relationships):
        if not self._is_available():
            logger.debug("store_relationships called but driver unavailable; skipping")
            return

        with self.driver.session() as session:
            for rel in relationships:
                session.run(
                    """
                    MATCH (a:Entity {id: $from}), (b:Entity {id: $to})
                    MERGE (a)-[:RELATION {type: $type}]->(b)
                    """,
                    **rel
                )

    def store_exposures(self, exposures):
        if not self._is_available():
            logger.debug("store_exposures called but driver unavailable; skipping")
            return

        with self.driver.session() as session:
            for exp in exposures:
                session.run(
                    """
                    MATCH (e:Entity {id: $entity})
                    MERGE (x:Exposure {id: $id, type: $type})
                    MERGE (e)-[:HAS_EXPOSURE]->(x)
                    """,
                    id=exp["exposure_id"],
                    type=exp["type"],
                    entity=exp["entity"]
                )
