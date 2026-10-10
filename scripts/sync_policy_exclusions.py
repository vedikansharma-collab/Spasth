"""
Sync policy exclusions from policy_pages in SQLite into policy_rules.
Scans policy pages for IRDAI standard exclusions (e.g. Excl18 Maternity, Excl08 Cosmetic, Excl06 Obesity, etc.)
and inserts them into policy_rules for each policy in fin01.db.
"""
import sys
import sqlite3
import re
from pathlib import Path

# Add backend to path
sys.path.insert(0, str(Path(__file__).parent.parent / "backend"))

from app.extraction.intelligence import PolicyIntelligenceExtractor

def main():
    db_path = Path(__file__).parent.parent / "backend" / "fin01.db"
    conn = sqlite3.connect(str(db_path))
    conn.row_factory = sqlite3.Row
    cur = conn.cursor()

    policies = cur.execute("SELECT id, filename FROM policies").fetchall()
    print(f"Total policies to check: {len(policies)}")

    inserted_total = 0

    for pol in policies:
        pol_id = pol["id"]
        # Fetch pages
        pages = cur.execute(
            "SELECT page_number, content FROM policy_pages WHERE policy_id = ? ORDER BY page_number",
            (pol_id,)
        ).fetchall()

        if not pages:
            continue

        policy_pages = []
        for p in pages:
            policy_pages.append({
                "page_number": p["page_number"],
                "content": p["content"] or "",
                "tables": []
            })

        # Run deterministic rule extraction
        raw_rules = PolicyIntelligenceExtractor._extract_with_rule_parser(policy_pages)
        extracted_rules = PolicyIntelligenceExtractor._deduplicate_and_validate(raw_rules, None)

        # Filter exclusion rules
        excl_rules = [r for r in extracted_rules if r.get("rule_type") == "exclusion"]

        for rule in excl_rules:
            # Check if already exists in DB
            exists = cur.execute(
                "SELECT id FROM policy_rules WHERE policy_id = ? AND rule_type = 'exclusion' AND rule_key = ?",
                (pol_id, rule.get("rule_key"))
            ).fetchone()

            if not exists:
                cur.execute(
                    """
                    INSERT INTO policy_rules (
                        policy_id, rule_type, rule_key, value, unit,
                        page, clause, source_text, confidence, qualifiers,
                        status, formatted_value
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        pol_id,
                        "exclusion",
                        rule.get("rule_key"),
                        0.0,
                        rule.get("unit"),
                        rule.get("page"),
                        rule.get("clause"),
                        rule.get("source_text"),
                        rule.get("confidence", "HIGH"),
                        rule.get("qualifiers"),
                        rule.get("status", "VERIFIED"),
                        rule.get("formatted_value")
                    )
                )
                inserted_total += 1
                print(f"[{pol['filename'][:30]}] Inserted exclusion: {rule.get('rule_key')} on Page {rule.get('page')}")

    conn.commit()
    conn.close()
    print(f"Total exclusions inserted: {inserted_total}")

if __name__ == "__main__":
    main()
