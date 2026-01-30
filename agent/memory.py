import sqlite3
import json
import numpy as np

class AgentMemory:
    def __init__(self, db_path="storage/agent_memory.db"):
        self.conn = sqlite3.connect(db_path)
        self.create_tables()

    def create_tables(self):
        cursor = self.conn.cursor()
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS persons (
                entity_id TEXT PRIMARY KEY,
                embedding TEXT,
                last_seen_session TEXT
            )
        """)
        self.conn.commit()

    def store_person(self, entity_id, embedding, session_id):
        cursor = self.conn.cursor()
        cursor.execute("""
            INSERT OR REPLACE INTO persons (entity_id, embedding, last_seen_session)
            VALUES (?, ?, ?)
        """, (entity_id, json.dumps(embedding.tolist()), session_id))
        self.conn.commit()

    def get_all_embeddings(self):
        cursor = self.conn.cursor()
        cursor.execute("SELECT entity_id, embedding FROM persons")
        rows = cursor.fetchall()

        return [
            {"entity_id": row[0], "embedding": np.array(json.loads(row[1]))}
            for row in rows
        ]

    def find_match(self, new_embedding, threshold=0.7):
        stored = self.get_all_embeddings()

        for item in stored:
            sim = np.dot(new_embedding, item["embedding"]) / (
                np.linalg.norm(new_embedding) * np.linalg.norm(item["embedding"])
            )
            if sim > threshold:
                return item["entity_id"]

        return None
