import sqlite3
import os
from contextlib import contextmanager
from datetime import datetime
from typing import List, Dict, Any, Optional
from app.core.config import settings

DB_FILE = os.path.join(settings.BASE_DIR, "fin01.db")

def dict_factory(cursor, row):
    d = {}
    for idx, col in enumerate(cursor.description):
        d[col[0]] = row[idx]
    return d

@contextmanager
def get_db():
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

def init_db():
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

        # 4. Treatment costs benchmark dataset table
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

        # Add optional columns if migrating an older database
        cursor.execute("PRAGMA table_info(treatment_costs);")
        columns = [col["name"] for col in cursor.fetchall()]
        if "procedure_code" not in columns:
            cursor.execute("ALTER TABLE treatment_costs ADD COLUMN procedure_code TEXT;")
        if "source_date" not in columns:
            cursor.execute("ALTER TABLE treatment_costs ADD COLUMN source_date TEXT;")
        if "notes" not in columns:
            cursor.execute("ALTER TABLE treatment_costs ADD COLUMN notes TEXT;")

        # Create indices
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_policy_pages_policy_id ON policy_pages(policy_id);")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_policy_rules_policy_id ON policy_rules(policy_id);")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_treatment_costs_proc_city ON treatment_costs(procedure_name, city);")

        # Seed treatment costs dataset if empty or refresh synthetic benchmarks
        cursor.execute("SELECT COUNT(*) as cnt FROM treatment_costs;")
        count = cursor.fetchone()["cnt"]
        if count == 0:
            seed_treatment_costs(cursor)

def seed_treatment_costs(cursor):
    """Seed MVP benchmark treatment cost dataset supporting procedure_code, city_tier, source_date, notes, and explicit synthetic data_type."""
    import json
    benchmarks_path = settings.DATA_DIR / "treatment_costs" / "benchmarks.json"
    
    if benchmarks_path.exists():
        try:
            with open(benchmarks_path, "r", encoding="utf-8") as f:
                data = json.load(f)
                for item in data:
                    cursor.execute("""
                        INSERT OR REPLACE INTO treatment_costs (
                            procedure_name, procedure_code, city, city_tier, min_cost, max_cost, source, source_date, notes, data_type
                        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?);
                    """, (
                        item["procedure"],
                        item.get("procedure_code"),
                        item["city"],
                        item["city_tier"],
                        float(item["cost_min"]),
                        float(item["cost_max"]),
                        item["source"],
                        item.get("source_date"),
                        item.get("notes"),
                        item.get("data_type", "synthetic")
                    ))
                return
        except Exception as e:
            pass

    # Fallback default seed
    sample_costs = [
        # Appendectomy
        ("Appendectomy", "SURG-APP-001", "Pune", "Tier-1", 75000.0, 95000.0, "State Healthcare Package Benchmark 2025", "2025-01-15", "Synthetic benchmark", "synthetic"),
        ("Appendectomy", "SURG-APP-001", "Mumbai", "Tier-1 Metro", 110000.0, 145000.0, "State Healthcare Package Benchmark 2025", "2025-01-15", "Synthetic benchmark", "synthetic"),
        ("Appendectomy", "SURG-APP-001", "Nagpur", "Tier-2", 55000.0, 72000.0, "State Healthcare Package Benchmark 2025", "2025-01-15", "Synthetic benchmark", "synthetic"),

        # Cataract Surgery
        ("Cataract Surgery", "OPH-CAT-002", "Pune", "Tier-1", 32000.0, 48000.0, "Ophthalmology Tariff Guidelines 2025", "2025-02-01", "Synthetic benchmark", "synthetic"),
        ("Cataract Surgery", "OPH-CAT-002", "Mumbai", "Tier-1 Metro", 45000.0, 65000.0, "Ophthalmology Tariff Guidelines 2025", "2025-02-01", "Synthetic benchmark", "synthetic"),
        ("Cataract Surgery", "OPH-CAT-002", "Nagpur", "Tier-2", 25000.0, 38000.0, "Ophthalmology Tariff Guidelines 2025", "2025-02-01", "Synthetic benchmark", "synthetic"),

        # Knee Replacement
        ("Knee Replacement", "ORTH-TKR-003", "Pune", "Tier-1", 180000.0, 240000.0, "Orthopedic Package Benchmarks 2025", "2025-01-20", "Synthetic benchmark", "synthetic"),
        ("Knee Replacement", "ORTH-TKR-003", "Mumbai", "Tier-1 Metro", 260000.0, 350000.0, "Orthopedic Package Benchmarks 2025", "2025-01-20", "Synthetic benchmark", "synthetic"),
        ("Knee Replacement", "ORTH-TKR-003", "Nagpur", "Tier-2", 140000.0, 190000.0, "Orthopedic Package Benchmarks 2025", "2025-01-20", "Synthetic benchmark", "synthetic"),

        # C-Section
        ("C-Section", "OBS-CS-004", "Pune", "Tier-1", 60000.0, 85000.0, "Maternity Care Package Cost Index 2025", "2025-01-10", "Synthetic benchmark", "synthetic"),
        ("C-Section", "OBS-CS-004", "Mumbai", "Tier-1 Metro", 90000.0, 130000.0, "Maternity Care Package Cost Index 2025", "2025-01-10", "Synthetic benchmark", "synthetic"),
        ("C-Section", "OBS-CS-004", "Nagpur", "Tier-2", 42000.0, 60000.0, "Maternity Care Package Cost Index 2025", "2025-01-10", "Synthetic benchmark", "synthetic"),

        # Angioplasty
        ("Angioplasty", "CARD-PTCA-005", "Pune", "Tier-1", 160000.0, 220000.0, "Cardiology Procedure Benchmarks 2025", "2025-02-15", "Synthetic benchmark", "synthetic"),
        ("Angioplasty", "CARD-PTCA-005", "Mumbai", "Tier-1 Metro", 220000.0, 310000.0, "Cardiology Procedure Benchmarks 2025", "2025-02-15", "Synthetic benchmark", "synthetic"),
        ("Angioplasty", "CARD-PTCA-005", "Nagpur", "Tier-2", 125000.0, 175000.0, "Cardiology Procedure Benchmarks 2025", "2025-02-15", "Synthetic benchmark", "synthetic"),
    ]

    cursor.executemany("""
        INSERT OR REPLACE INTO treatment_costs (
            procedure_name, procedure_code, city, city_tier, min_cost, max_cost, source, source_date, notes, data_type
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?);
    """, sample_costs)
