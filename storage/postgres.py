import json, os, logging, sqlite3
from dotenv import load_dotenv
load_dotenv()

logger = logging.getLogger(__name__)

try:
    import psycopg2
except ImportError:
    psycopg2 = None


class PostgresStorage:
    def __init__(self, db=None, user=None, password=None, host=None):
        self.conn = None
        self.is_postgres = False

        db = db or os.getenv("POSTGRES_DB", "osint")
        user = user or os.getenv("POSTGRES_USER", "postgres")
        password = password or os.getenv("POSTGRES_PASSWORD", "password")
        host = host or os.getenv("POSTGRES_HOST", "localhost")

        # Try Postgres first
        if psycopg2:
            try:
                self.conn = psycopg2.connect(
                    dbname=db,
                    user=user,
                    password=password,
                    host=host
                )
                self.is_postgres = True
                logger.info("Connected to PostgreSQL")
                self.create_table()
                return
            except Exception as e:
                logger.warning(f"Postgres failed, falling back to SQLite: {e}")

        # Fallback to SQLite
        self._use_sqlite(db)

    def _use_sqlite(self, db_name):
        os.makedirs("storage", exist_ok=True)
        path = os.path.join("storage", f"{db_name}.sqlite")
        self.conn = sqlite3.connect(path, check_same_thread=False)
        self.is_postgres = False
        logger.info(f"Using SQLite database at {path}")
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
        payload = json.dumps(report, default=str)

        try:
            if self.is_postgres:
                cur.execute(
                    """INSERT INTO reports (session_id, report)
                       VALUES (%s, %s)
                       ON CONFLICT (session_id)
                       DO UPDATE SET report = EXCLUDED.report""",
                    (session_id, payload)
                )
            else:
                cur.execute(
                    "INSERT OR REPLACE INTO reports (session_id, report) VALUES (?, ?)",
                    (session_id, payload)
                )
            self.conn.commit()
        except Exception as e:
            logger.error(f"Failed to save report: {e}")

    def get_report(self, session_id):
        cur = self.conn.cursor()
        if self.is_postgres:
            cur.execute("SELECT report FROM reports WHERE session_id = %s", (session_id,))
        else:
            cur.execute("SELECT report FROM reports WHERE session_id = ?", (session_id,))

        result = cur.fetchone()
        return json.loads(result[0]) if result else None
