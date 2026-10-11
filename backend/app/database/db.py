import os
import sqlite3
import re
from contextlib import contextmanager
from datetime import datetime
from typing import List, Dict, Any, Optional
from app.core.config import settings
from app.database.session import engine

DB_FILE = os.path.join(settings.BASE_DIR, "fin01.db")

def dict_factory(cursor, row):
    d = {}
    for idx, col in enumerate(cursor.description):
        d[col[0]] = row[idx]
    return d

class PgCursorWrapper:
    def __init__(self, raw_cursor):
        self._cursor = raw_cursor

    def execute(self, query: str, params: Any = None):
        # Convert SQLite ? placeholders to %s for PostgreSQL DBAPI
        clean_query = query
        if params is not None and "?" in clean_query:
            clean_query = clean_query.replace("?", "%s")
        # Remove SQLite specific PRAGMA commands
        if clean_query.strip().upper().startswith("PRAGMA"):
            return self

        if params:
            # Convert list to tuple if necessary
            if isinstance(params, list):
                params = tuple(params)
            self._cursor.execute(clean_query, params)
        else:
            self._cursor.execute(clean_query)
        return self

    def executemany(self, query: str, param_seq: Any):
        clean_query = query
        if "?" in clean_query:
            clean_query = clean_query.replace("?", "%s")
        self._cursor.executemany(clean_query, param_seq)
        return self

    def fetchone(self) -> Optional[Dict[str, Any]]:
        row = self._cursor.fetchone()
        if row is None:
            return None
        col_names = [d[0] for d in self._cursor.description]
        return dict(zip(col_names, row))

    def fetchall(self) -> List[Dict[str, Any]]:
        rows = self._cursor.fetchall()
        if not rows:
            return []
        col_names = [d[0] for d in self._cursor.description]
        return [dict(zip(col_names, r)) for r in rows]

    @property
    def rowcount(self):
        return self._cursor.rowcount

class PgConnectionWrapper:
    def __init__(self, raw_conn):
        self.raw_conn = raw_conn

    def cursor(self):
        return PgCursorWrapper(self.raw_conn.cursor())

    def execute(self, query: str, params: Any = None):
        cur = self.cursor()
        return cur.execute(query, params)

    def commit(self):
        self.raw_conn.commit()

    def rollback(self):
        self.raw_conn.rollback()

    def close(self):
        self.raw_conn.close()

@contextmanager
def get_db():
    is_sqlite = settings.DATABASE_URL.startswith("sqlite")
    if is_sqlite:
        conn = sqlite3.connect(DB_FILE)
        conn.row_factory = dict_factory
        conn.execute("PRAGMA foreign_keys = ON;")
        try:
            yield conn
            conn.commit()
        except Exception:
            conn.rollback()
            raise
        finally:
            conn.close()
    else:
        raw_conn = engine.raw_connection()
        wrapped = PgConnectionWrapper(raw_conn)
        try:
            yield wrapped
            wrapped.commit()
        except Exception:
            wrapped.rollback()
            raise
        finally:
            wrapped.close()

def init_db():
    is_sqlite = settings.DATABASE_URL.startswith("sqlite")
    if not is_sqlite:
        # Schema is managed by Alembic migrations
        return

    with get_db() as conn:
        cursor = conn.cursor()
        
        # 1. Policies table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS policies (
                id TEXT PRIMARY KEY,
                filename TEXT NOT NULL,
                original_filename TEXT NOT NULL,
                file_path TEXT NOT NULL,
                file_size_bytes INTEGER NOT NULL,
                page_count INTEGER NOT NULL DEFAULT 0,
                uploaded_at TEXT NOT NULL,
                extraction_status TEXT NOT NULL DEFAULT 'PENDING',
                error_message TEXT
            );
        """)
        
        # 2. Policy pages table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS policy_pages (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                policy_id TEXT NOT NULL,
                page_number INTEGER NOT NULL,
                char_count INTEGER NOT NULL DEFAULT 0,
                word_count INTEGER NOT NULL DEFAULT 0,
                content TEXT NOT NULL,
                FOREIGN KEY (policy_id) REFERENCES policies(id) ON DELETE CASCADE
            );
        """)

        # 3. Policy rules table (extracted by Gemini / RAG)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS policy_rules (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                policy_id TEXT NOT NULL,
                rule_type TEXT NOT NULL,
                rule_key TEXT NOT NULL,
                value REAL,
                unit TEXT,
                page INTEGER NOT NULL,
                clause TEXT,
                source_text TEXT NOT NULL,
                confidence TEXT NOT NULL DEFAULT 'HIGH',
                FOREIGN KEY (policy_id) REFERENCES policies(id) ON DELETE CASCADE
            );
        """)

        # 4. Policy chunks table for RAG Vector Index
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS policy_chunks (
                chunk_id TEXT PRIMARY KEY,
                policy_id TEXT NOT NULL,
                document_id TEXT NOT NULL,
                section TEXT,
                clause TEXT,
                rule_type TEXT,
                subtype TEXT,
                text TEXT NOT NULL,
                source_page INTEGER NOT NULL,
                source_text TEXT NOT NULL,
                bbox TEXT,
                embedding TEXT,
                created_at TEXT NOT NULL,
                FOREIGN KEY (policy_id) REFERENCES policies(id) ON DELETE CASCADE
            );
        """)

        # 5. Treatment costs benchmark dataset table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS treatment_costs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                procedure_name TEXT NOT NULL,
                procedure_code TEXT,
                city TEXT NOT NULL,
                city_tier TEXT NOT NULL,
                min_cost REAL NOT NULL,
                max_cost REAL NOT NULL,
                source TEXT NOT NULL,
                source_date TEXT,
                notes TEXT,
                data_type TEXT NOT NULL DEFAULT 'synthetic',
                UNIQUE(procedure_name, city)
            );
        """)

        # Create indices
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_policy_pages_policy_id ON policy_pages(policy_id);")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_policy_rules_policy_id ON policy_rules(policy_id);")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_policy_chunks_policy_id ON policy_chunks(policy_id);")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_treatment_costs_proc_city ON treatment_costs(procedure_name, city);")
