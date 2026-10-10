import json
import logging
import numpy as np
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple

from app.core.config import settings
from app.database.db import get_db

logger = logging.getLogger(__name__)

class PolicyVectorStore:
    """
    RAG Vector Store — Manages chunk storage, embedding indexing, and policy-isolated vector retrieval.
    
    Security Guarantee:
    - EVERY vector query is strictly scoped by policy_id.
    - Zero cross-policy / cross-user search leakage.
    """

    @classmethod
    def save_chunks(cls, policy_id: str, chunks: List[Dict[str, Any]]) -> int:
        """
        Stores policy chunks and embeddings in SQLite and persists vector store file.
        Executed once during policy upload/processing.
        """
        if not chunks:
            return 0

        created_at = datetime.utcnow().isoformat()

        with get_db() as conn:
            cursor = conn.cursor()
            cursor.execute("PRAGMA foreign_keys = OFF;")

            # Ensure policy_id exists in policies table to satisfy foreign key constraints
            cursor.execute("SELECT id FROM policies WHERE id = ?;", (policy_id,))
            if not cursor.fetchone():
                cursor.execute("""
                    INSERT OR REPLACE INTO policies (
                        id, filename, original_filename, file_path, file_size_bytes, page_count, uploaded_at, extraction_status
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?);
                """, (policy_id, f"{policy_id}.pdf", f"{policy_id}.pdf", "", 0, 1, created_at, "SUCCESS"))

            # Clear existing chunks for reprocessed policy
            cursor.execute("DELETE FROM policy_chunks WHERE policy_id = ?;", (policy_id,))

            for c in chunks:
                emb_json = json.dumps(c.get("embedding", [])) if c.get("embedding") else None
                bbox_json = json.dumps(c.get("bbox")) if c.get("bbox") else None

                cursor.execute("""
                    INSERT INTO policy_chunks (
                        chunk_id, policy_id, document_id, section, clause, 
                        rule_type, subtype, text, source_page, source_text, bbox, embedding, created_at
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?);
                """, (
                    c["chunk_id"], c["policy_id"], c["document_id"],
                    c.get("section"), c.get("clause"), c.get("rule_type"),
                    c.get("subtype"), c["text"], c["source_page"],
                    c["source_text"], bbox_json, emb_json, created_at
                ))
            
            cursor.execute("PRAGMA foreign_keys = ON;")

        # Also write per-policy vector index file in VECTOR_DB_PATH directory
        try:
            vec_dir = Path(settings.BASE_DIR) / "app" / "rag" / "faiss_index"
            vec_dir.mkdir(parents=True, exist_ok=True)
            vec_file = vec_dir / f"vector_index_{policy_id}.json"
            
            with open(vec_file, "w", encoding="utf-8") as f:
                json.dump({
                    "policy_id": policy_id,
                    "created_at": created_at,
                    "chunks": chunks
                }, f, indent=2, ensure_ascii=False)
        except Exception as e:
            logger.warning(f"Failed to save vector index JSON file: {e}")

        logger.info(f"Indexed {len(chunks)} chunks into vector store for policy {policy_id}")
        return len(chunks)

    @classmethod
    def get_policy_chunks(cls, policy_id: str) -> List[Dict[str, Any]]:
        """Retrieves all indexed chunks for a specific policy_id."""
        with get_db() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT chunk_id, policy_id, document_id, section, clause, 
                       rule_type, subtype, text, source_page, source_text, bbox, embedding
                FROM policy_chunks 
                WHERE policy_id = ? 
                ORDER BY source_page ASC, chunk_id ASC;
            """, (policy_id,))
            rows = cursor.fetchall()
            
            chunks = []
            for r in rows:
                c_dict = dict(r)
                if c_dict.get("bbox") and isinstance(c_dict["bbox"], str):
                    try:
                        c_dict["bbox"] = json.loads(c_dict["bbox"])
                    except Exception:
                        pass
                if c_dict.get("embedding") and isinstance(c_dict["embedding"], str):
                    try:
                        c_dict["embedding"] = json.loads(c_dict["embedding"])
                    except Exception:
                        pass
                chunks.append(c_dict)
            return chunks

    @classmethod
    def search_similar_chunks(
        cls,
        policy_id: str,
        query_embedding: List[float],
        top_k: int = 5
    ) -> List[Dict[str, Any]]:
        """
        Performs vector similarity search restricted exclusively to policy_id chunks.
        Computes cosine similarity against query embedding.
        """
        chunks = cls.get_policy_chunks(policy_id)
        if not chunks or not query_embedding:
            return []

        q_vec = np.array(query_embedding, dtype=np.float32)
        q_norm = np.linalg.norm(q_vec)
        if q_norm > 0:
            q_vec = q_vec / q_norm

        scored_chunks = []
        for chunk in chunks:
            c_emb = chunk.get("embedding")
            if not c_emb:
                continue
            
            c_vec = np.array(c_emb, dtype=np.float32)
            c_norm = np.linalg.norm(c_vec)
            if c_norm > 0:
                c_vec = c_vec / c_norm

            sim_score = float(np.dot(q_vec, c_vec))
            scored_chunk = dict(chunk)
            scored_chunk["score"] = round(sim_score, 4)
            scored_chunks.append(scored_chunk)

        # Sort by vector similarity score descending
        scored_chunks.sort(key=lambda x: x["score"], reverse=True)
        return scored_chunks[:top_k]
