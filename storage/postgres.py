import json
import os
import logging

try:
    import psycopg2
except Exception:
    psycopg2 = None

import sqlite3

logger = logging.getLogger(__name__)


class PostgresStorage:
    def __init__(self, db=None, user=None, password=None, host=None):
        db = db or os.getenv("POSTGRES_DB", "osint")
        user = user or os.getenv("POSTGRES_USER", "postgres")
        password = password or os.getenv("POSTGRES_PASSWORD", "password")
        host = host or os.getenv("POSTGRES_HOST", "localhost")

        if psycopg2 is None:
            logger.warning("psycopg2 not available; falling back to sqlite3 local storage")
            self._use_sqlite(db)
            return

        try:
            self.conn = psycopg2.connect(dbname=db, user=user, password=password, host=host)
            self.create_table()
        except Exception as e:
            logger.exception("Failed to connect to Postgres; falling back to sqlite: %s", e)
            self._use_sqlite(db)

    def _use_sqlite(self, db_name):
        path = os.path.join(os.getcwd(), f"{db_name}.sqlite")
        self.conn = sqlite3.connect(path)
        self.create_table()

    def create_table(self):
        cur = self.conn.cursor()
        cur.execute("""
            CREATE TABLE IF NOT EXISTS reports (
                session_id TEXT PRIMARY KEY,
                report TEXT
            )
        """)
        self.conn.commit()

    def save_report(self, session_id, report):
        cur = self.conn.cursor()
        # store JSON as text for sqlite or JSONB for postgres
        payload = json.dumps(report)
        try:
            cur.execute(
                "INSERT INTO reports (session_id, report) VALUES (?, ?) ON CONFLICT(session_id) DO UPDATE SET report=?",
                (session_id, payload, payload)
            )
        except Exception:
            # fallback for psycopg2 parameter style
            cur.execute(
                "INSERT INTO reports (session_id, report) VALUES (%s, %s) ON CONFLICT (session_id) DO UPDATE SET report=%s",
                (session_id, payload, payload)
            )

        self.conn.commit()
