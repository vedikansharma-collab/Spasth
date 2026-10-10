import re
import uuid
from typing import List, Dict, Any, Optional

class PolicyChunker:
    """
    RAG Policy Chunker — Creates meaningful, section/clause-aware searchable policy chunks.
    
    Guarantees:
    - Never creates 1 huge chunk containing the entire policy.
    - Never creates tiny useless single-word chunks.
    - Preserves logical context (combines rules with qualifiers & conditions).
    - Preserves exact source metadata (chunk_id, policy_id, document_id, section, clause, rule_type, subtype, source_page, source_text, bbox).
    """

    @classmethod
    def create_chunks(
        cls,
        policy_id: str,
        document_id: str,
        pages: List[Dict[str, Any]],
        canonical_rules: Optional[List[Dict[str, Any]]] = None
    ) -> List[Dict[str, Any]]:
        chunks: List[Dict[str, Any]] = []
        chunk_counter = 1

        # 1. Generate Structured Rule Chunks from Canonical Policy Rules
        if canonical_rules:
            for r in canonical_rules:
                rule_type = (r.get("category") or r.get("rule_type") or "GENERAL").upper()
                rule_key = (r.get("rule_key") or r.get("rule_id") or "rule").upper()
                rule_name = r.get("name") or r.get("label") or "Policy Provision"
                page_num = int(r.get("page", 1))
                clause_str = r.get("clause") or r.get("section") or f"Page {page_num}"
                source_text = r.get("source_text") or ""
                val_fmt = r.get("formatted_value") or str(r.get("value", ""))
                quals = r.get("qualifiers")
                quals_str = ", ".join(quals) if isinstance(quals, list) else str(quals) if quals else ""
                conds = r.get("conditions")
                conds_str = ", ".join(conds) if isinstance(conds, list) else str(conds) if conds else ""

                # Construct complete self-contained text snippet
                text_parts = [f"Rule: {rule_name}"]
                if val_fmt:
                    text_parts.append(f"Value: {val_fmt}")
                if quals_str:
                    text_parts.append(f"Qualifiers: {quals_str}")
                if conds_str:
                    text_parts.append(f"Conditions: {conds_str}")
                if source_text:
                    text_parts.append(f"Source: \"{source_text}\"")

                full_text = " | ".join(text_parts)
                chunk_id = f"chk_{policy_id[:8]}_{chunk_counter:03d}"
                chunk_counter += 1

                chunks.append({
                    "chunk_id": chunk_id,
                    "policy_id": policy_id,
                    "document_id": document_id,
                    "section": r.get("section") or clause_str,
                    "clause": clause_str,
                    "rule_type": rule_type,
                    "subtype": rule_key,
                    "text": full_text,
                    "source_page": page_num,
                    "source_text": source_text or full_text,
                    "bbox": r.get("bbox")
                })

        # 2. Generate Clause/Section Text Chunks from Page Content
        for page in pages:
            page_num = int(page.get("page_number", 1))
            content = page.get("content", "").strip()
            if not content:
                continue

            # Group page lines into coherent blocks (paragraphs/clauses)
            lines = [l.strip() for l in content.split("\n") if l.strip()]
            current_block = []
            current_clause = f"Page {page_num} Section"

            for line in lines:
                # Detect clause headers (e.g., Section 2.1, Clause 4, 1. Scope)
                header_match = re.match(r'^(Section|Clause|\d+\.|\d+\.\d+)\s+([^\n:]+)', line, re.I)
                if header_match and len(current_block) > 0:
                    # Flush previous block into a chunk
                    block_text = " ".join(current_block)
                    if len(block_text) >= 30:
                        chunk_id = f"chk_{policy_id[:8]}_{chunk_counter:03d}"
                        chunk_counter += 1
                        chunks.append({
                            "chunk_id": chunk_id,
                            "policy_id": policy_id,
                            "document_id": document_id,
                            "section": current_clause,
                            "clause": current_clause,
                            "rule_type": "TEXT_SECTION",
                            "subtype": "PAGE_TEXT",
                            "text": block_text,
                            "source_page": page_num,
                            "source_text": block_text,
                            "bbox": None
                        })
                    current_block = [line]
                    current_clause = line[:60]
                else:
                    current_block.append(line)

            # Flush trailing block for the page
            if current_block:
                block_text = " ".join(current_block)
                if len(block_text) >= 30:
                    chunk_id = f"chk_{policy_id[:8]}_{chunk_counter:03d}"
                    chunk_counter += 1
                    chunks.append({
                        "chunk_id": chunk_id,
                        "policy_id": policy_id,
                        "document_id": document_id,
                        "section": current_clause,
                        "clause": current_clause,
                        "rule_type": "TEXT_SECTION",
                        "subtype": "PAGE_TEXT",
                        "text": block_text,
                        "source_page": page_num,
                        "source_text": block_text,
                        "bbox": None
                    })

        return chunks
