import os
import sys
import sqlite3
import json
from decimal import Decimal
from typing import Dict, Any, List

# Add parent directory to sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from sqlalchemy import select, func, text
from sqlalchemy.dialects.postgresql import insert as pg_insert
from app.database.session import engine, SessionLocal
from app.models.policy import Policy, PolicyPage, PolicyRule, TreatmentCost, PolicyChunk

SQLITE_PATH = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "fin01.db"))

def dict_factory(cursor, row):
    d = {}
    for idx, col in enumerate(cursor.description):
        d[col[0]] = row[idx]
    return d

def chunked(iterable, n=100):
    for i in range(0, len(iterable), n):
        yield iterable[i:i + n]

def migrate():
    print(f"[ETL] Starting fast batched SQLite -> PostgreSQL migration...", flush=True)

    if not os.path.exists(SQLITE_PATH):
        raise FileNotFoundError(f"Source database not found: {SQLITE_PATH}")

    sqlite_conn = sqlite3.connect(f"file:{SQLITE_PATH}?mode=ro", uri=True)
    sqlite_conn.row_factory = dict_factory
    sqlite_cur = sqlite_conn.cursor()

    db = SessionLocal()

    try:
        # 1. Policies (102 rows)
        sqlite_cur.execute("SELECT * FROM policies ORDER BY uploaded_at ASC;")
        policies = sqlite_cur.fetchall()
        print(f"[ETL] Read {len(policies)} policies from SQLite.", flush=True)

        for batch in chunked(policies, 50):
            records = [{
                "id": p["id"],
                "filename": p["filename"],
                "original_filename": p["original_filename"],
                "file_path": p["file_path"],
                "file_size_bytes": p["file_size_bytes"],
                "page_count": p["page_count"],
                "uploaded_at": p["uploaded_at"],
                "extraction_status": p["extraction_status"],
                "error_message": p.get("error_message")
            } for p in batch]

            stmt = pg_insert(Policy).values(records)
            stmt = stmt.on_conflict_do_update(
                index_elements=[Policy.id],
                set_={
                    "filename": stmt.excluded.filename,
                    "original_filename": stmt.excluded.original_filename,
                    "file_path": stmt.excluded.file_path,
                    "file_size_bytes": stmt.excluded.file_size_bytes,
                    "page_count": stmt.excluded.page_count,
                    "uploaded_at": stmt.excluded.uploaded_at,
                    "extraction_status": stmt.excluded.extraction_status,
                    "error_message": stmt.excluded.error_message,
                }
            )
            db.execute(stmt)
            db.commit()
        print(f"[ETL] Policies migration committed successfully.", flush=True)

        # 2. Policy Pages (575 rows)
        sqlite_cur.execute("SELECT * FROM policy_pages ORDER BY id ASC;")
        pages = sqlite_cur.fetchall()
        print(f"[ETL] Read {len(pages)} policy_pages from SQLite.", flush=True)

        for batch in chunked(pages, 100):
            records = [{
                "id": pg["id"],
                "policy_id": pg["policy_id"],
                "page_number": pg["page_number"],
                "char_count": pg.get("char_count", 0),
                "word_count": pg.get("word_count", 0),
                "content": pg["content"],
                "layout_data": pg.get("layout_data")
            } for pg in batch]

            stmt = pg_insert(PolicyPage).values(records)
            stmt = stmt.on_conflict_do_update(
                index_elements=[PolicyPage.id],
                set_={
                    "policy_id": stmt.excluded.policy_id,
                    "page_number": stmt.excluded.page_number,
                    "char_count": stmt.excluded.char_count,
                    "word_count": stmt.excluded.word_count,
                    "content": stmt.excluded.content,
                    "layout_data": stmt.excluded.layout_data,
                }
            )
            db.execute(stmt)
            db.commit()
        print(f"[ETL] Policy pages migration committed successfully.", flush=True)

        # 3. Policy Rules (1,023 rows)
        sqlite_cur.execute("SELECT * FROM policy_rules ORDER BY id ASC;")
        rules = sqlite_cur.fetchall()
        print(f"[ETL] Read {len(rules)} policy_rules from SQLite.", flush=True)

        for batch in chunked(rules, 100):
            records = []
            for r in batch:
                raw_val = r.get("value")
                numeric_val = None
                if raw_val is not None and not isinstance(raw_val, str):
                    try:
                        numeric_val = Decimal(str(raw_val))
                    except Exception:
                        numeric_val = None

                records.append({
                    "id": r["id"],
                    "policy_id": r["policy_id"],
                    "rule_type": r["rule_type"],
                    "rule_key": r["rule_key"],
                    "value": numeric_val,
                    "unit": r.get("unit"),
                    "page": r.get("page", 1),
                    "clause": r.get("clause"),
                    "source_text": r.get("source_text", ""),
                    "confidence": r.get("confidence", "HIGH"),
                    "qualifiers": r.get("qualifiers"),
                    "bbox": r.get("bbox"),
                    "additional_sources": r.get("additional_sources"),
                    "status": r.get("status", "VERIFIED"),
                    "formatted_value": r.get("formatted_value") or (str(raw_val) if raw_val is not None else None)
                })

            stmt = pg_insert(PolicyRule).values(records)
            stmt = stmt.on_conflict_do_update(
                index_elements=[PolicyRule.id],
                set_={
                    "policy_id": stmt.excluded.policy_id,
                    "rule_type": stmt.excluded.rule_type,
                    "rule_key": stmt.excluded.rule_key,
                    "value": stmt.excluded.value,
                    "unit": stmt.excluded.unit,
                    "page": stmt.excluded.page,
                    "clause": stmt.excluded.clause,
                    "source_text": stmt.excluded.source_text,
                    "confidence": stmt.excluded.confidence,
                    "qualifiers": stmt.excluded.qualifiers,
                    "bbox": stmt.excluded.bbox,
                    "additional_sources": stmt.excluded.additional_sources,
                    "status": stmt.excluded.status,
                    "formatted_value": stmt.excluded.formatted_value,
                }
            )
            db.execute(stmt)
            db.commit()
        print(f"[ETL] Policy rules migration committed successfully.", flush=True)

        # 4. Treatment Costs (60 rows)
        sqlite_cur.execute("SELECT * FROM treatment_costs ORDER BY id ASC;")
        costs = sqlite_cur.fetchall()
        print(f"[ETL] Read {len(costs)} treatment_costs from SQLite.", flush=True)

        for batch in chunked(costs, 60):
            records = [{
                "id": tc["id"],
                "procedure_name": tc["procedure_name"],
                "procedure_code": tc.get("procedure_code"),
                "city": tc["city"],
                "city_tier": tc["city_tier"],
                "min_cost": Decimal(str(tc["min_cost"])),
                "max_cost": Decimal(str(tc["max_cost"])),
                "source": tc["source"],
                "source_date": tc.get("source_date"),
                "notes": tc.get("notes"),
                "data_type": tc.get("data_type", "synthetic")
            } for tc in batch]

            stmt = pg_insert(TreatmentCost).values(records)
            stmt = stmt.on_conflict_do_update(
                index_elements=[TreatmentCost.id],
                set_={
                    "procedure_name": stmt.excluded.procedure_name,
                    "procedure_code": stmt.excluded.procedure_code,
                    "city": stmt.excluded.city,
                    "city_tier": stmt.excluded.city_tier,
                    "min_cost": stmt.excluded.min_cost,
                    "max_cost": stmt.excluded.max_cost,
                    "source": stmt.excluded.source,
                    "source_date": stmt.excluded.source_date,
                    "notes": stmt.excluded.notes,
                    "data_type": stmt.excluded.data_type,
                }
            )
            db.execute(stmt)
            db.commit()
        print(f"[ETL] Treatment costs migration committed successfully.", flush=True)

        # 5. Policy Chunks (1037 rows)
        sqlite_cur.execute("SELECT * FROM policy_chunks ORDER BY chunk_id ASC;")
        chunks = sqlite_cur.fetchall()
        print(f"[ETL] Read {len(chunks)} policy_chunks from SQLite.", flush=True)

        for batch in chunked(chunks, 100):
            records = [{
                "chunk_id": c["chunk_id"],
                "policy_id": c["policy_id"],
                "document_id": c["document_id"],
                "section": c.get("section"),
                "clause": c.get("clause"),
                "rule_type": c.get("rule_type"),
                "subtype": c.get("subtype"),
                "text": c["text"],
                "source_page": c["source_page"],
                "source_text": c["source_text"],
                "bbox": c.get("bbox"),
                "embedding": json.loads(c["embedding"]) if c.get("embedding") else None,
                "created_at": c["created_at"]
            } for c in batch]

            stmt = pg_insert(PolicyChunk).values(records)
            stmt = stmt.on_conflict_do_update(
                index_elements=[PolicyChunk.chunk_id],
                set_={
                    "policy_id": stmt.excluded.policy_id,
                    "document_id": stmt.excluded.document_id,
                    "section": stmt.excluded.section,
                    "clause": stmt.excluded.clause,
                    "rule_type": stmt.excluded.rule_type,
                    "subtype": stmt.excluded.subtype,
                    "text": stmt.excluded.text,
                    "source_page": stmt.excluded.source_page,
                    "source_text": stmt.excluded.source_text,
                    "bbox": stmt.excluded.bbox,
                    "embedding": stmt.excluded.embedding,
                    "created_at": stmt.excluded.created_at,
                }
            )
            db.execute(stmt)
            db.commit()
        print(f"[ETL] Policy chunks migration committed successfully.", flush=True)

        # Reset serial sequences
        for tbl, seq in [
            ("policy_pages", "policy_pages_id_seq"),
            ("policy_rules", "policy_rules_id_seq"),
            ("treatment_costs", "treatment_costs_id_seq")
        ]:
            db.execute(text(f"SELECT setval('{seq}', (SELECT COALESCE(MAX(id), 1) FROM {tbl}));"))
        db.commit()
        print(f"[ETL] Serial sequences updated.", flush=True)

        # Final Verification
        pg_policies_count = db.scalar(select(func.count(Policy.id)))
        pg_pages_count = db.scalar(select(func.count(PolicyPage.id)))
        pg_rules_count = db.scalar(select(func.count(PolicyRule.id)))
        pg_costs_count = db.scalar(select(func.count(TreatmentCost.id)))
        pg_chunks_count = db.scalar(select(func.count(PolicyChunk.chunk_id)))

        print("\n================== POST-MIGRATION ROW COUNTS ==================", flush=True)
        print(f"policies        : {pg_policies_count} (Expected: 102)", flush=True)
        print(f"policy_pages    : {pg_pages_count} (Expected: 575)", flush=True)
        print(f"policy_rules    : {pg_rules_count} (Expected: 1023)", flush=True)
        print(f"treatment_costs : {pg_costs_count} (Expected: 60)", flush=True)
        print(f"policy_chunks   : {pg_chunks_count} (Expected: 1037)", flush=True)
        print("================================================================\n", flush=True)

        assert pg_policies_count == 102, f"Policies mismatch: got {pg_policies_count}, expected 102"
        assert pg_pages_count == 575, f"Policy pages mismatch: got {pg_pages_count}, expected 575"
        assert pg_rules_count == 1023, f"Policy rules mismatch: got {pg_rules_count}, expected 1023"
        assert pg_costs_count == 60, f"Treatment costs mismatch: got {pg_costs_count}, expected 60"
        assert pg_chunks_count == 1037, f"Policy chunks mismatch: got {pg_chunks_count}, expected 1037"
        print("[ETL] SUCCESS: All baseline counts verified exactly!", flush=True)

    finally:
        db.close()
        sqlite_conn.close()

if __name__ == "__main__":
    migrate()
