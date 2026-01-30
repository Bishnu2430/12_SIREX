import json
import os
import logging

from dotenv import load_dotenv
load_dotenv()

print("ENV CHECK:", os.getenv("POSTGRES_HOST"), os.getenv("POSTGRES_PASSWORD"))

try:
    import psycopg2
except Exception:
    psycopg2 = None

import sqlite3

logger = logging.getLogger(__name__)


class PostgresStorage:
    def __init__(self, db=None, user=None, password=None, host=None, port=None):
        self.db = db or os.getenv("POSTGRES_DB", "osint")
        self.user = user or os.getenv("POSTGRES_USER", "postgres")
        self.password = password or os.getenv("POSTGRES_PASSWORD", "password")
        self.host = host or os.getenv("POSTGRES_HOST", "127.0.0.1")
        self.port = port or os.getenv("POSTGRES_PORT", "5432")

        if psycopg2 is None:
            logger.warning("psycopg2 not available; falling back to sqlite3 local storage")
            self._use_sqlite()
            return

        try:
            print(f"Connecting to Postgres → DB:{self.db} HOST:{self.host} PORT:{self.port}")
            self.conn = psycopg2.connect(
                dbname=self.db,
                user=self.user,
                password=self.password,
                host=self.host,
                port=self.port,
            )
            self.backend = "postgres"
            self.create_table()
            print("✓ PostgreSQL initialized")

        except Exception as e:
            logger.exception("Failed to connect to Postgres; falling back to sqlite: %s", e)
            self._use_sqlite()

    def _use_sqlite(self):
        path = os.path.join(os.getcwd(), f"{self.db}.sqlite")
        self.conn = sqlite3.connect(path)
        self.backend = "sqlite"
        self.create_table()
        print("⚠ Using SQLite fallback")

    def create_table(self):
        cur = self.conn.cursor()

        if self.backend == "postgres":
            cur.execute("""
                CREATE TABLE IF NOT EXISTS reports (
                    session_id TEXT PRIMARY KEY,
                    report JSONB
                )
            """)
        else:
            cur.execute("""
                CREATE TABLE IF NOT EXISTS reports (
                    session_id TEXT PRIMARY KEY,
                    report TEXT
                )
            """)

        self.conn.commit()

    def save_report(self, session_id, report):
        cur = self.conn.cursor()
        payload = json.dumps(report)

        if self.backend == "postgres":
            cur.execute(
                """
                INSERT INTO reports (session_id, report)
                VALUES (%s, %s)
                ON CONFLICT (session_id) DO UPDATE SET report = EXCLUDED.report
                """,
                (session_id, payload),
            )
        else:
            cur.execute(
                """
                INSERT OR REPLACE INTO reports (session_id, report)
                VALUES (?, ?)
                """,
                (session_id, payload),
            )

        self.conn.commit()
