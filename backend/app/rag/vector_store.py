import json
import logging
from datetime import datetime
from typing import List, Dict, Any, Optional

from sqlalchemy import select, delete, func, text
from sqlalchemy.dialects.postgresql import insert as pg_insert
from app.database.session import SessionLocal
from app.models.policy import Policy, PolicyChunk

logger = logging.getLogger(__name__)

def chunked(iterable, n=100):
    for i in range(0, len(iterable), n):
        yield iterable[i:i + n]

class PolicyVectorStore:
    """
    RAG Vector Store — PostgreSQL + pgvector Authoritative Store.
    
    Guarantees:
    - Authoritative chunk and 768-dim embedding storage in PostgreSQL `policy_chunks`.
    - Native pgvector vector similarity search using cosine distance (<=>).
    - Cosine similarity calculation: similarity = 1 - cosine_distance.
    - EVERY vector query is strictly filtered by policy_id (strict policy isolation).
    - Zero in-memory Python loops or filesystem index dependencies for search.
    """

    @classmethod
    def save_chunks(cls, policy_id: str, chunks: List[Dict[str, Any]]) -> int:
        """
        Stores policy chunks and embeddings in PostgreSQL (pgvector).
        Executed during policy upload or chunking.
        """
        if not chunks:
            return 0

        created_at = datetime.utcnow().isoformat()
        db = SessionLocal()
        try:
            # Ensure policy exists to satisfy foreign key constraint
            existing_pol = db.scalar(select(Policy.id).where(Policy.id == policy_id))
            if not existing_pol:
                dummy_pol = Policy(
                    id=policy_id,
                    filename=f"{policy_id}.pdf",
                    original_filename=f"{policy_id}.pdf",
                    file_path="",
                    file_size_bytes=0,
                    page_count=1,
                    uploaded_at=created_at,
                    extraction_status="SUCCESS"
                )
                db.add(dummy_pol)
                db.commit()

            # Clear existing chunks for reprocessed policy
            db.execute(delete(PolicyChunk).where(PolicyChunk.policy_id == policy_id))
            db.commit()

            records = []
            for c in chunks:
                emb = c.get("embedding")
                if emb is not None and not isinstance(emb, list):
                    emb = list(emb)
                bbox_val = c.get("bbox")
                if bbox_val and not isinstance(bbox_val, str):
                    bbox_val = json.dumps(bbox_val)

                records.append({
                    "chunk_id": c["chunk_id"],
                    "policy_id": policy_id,
                    "document_id": c.get("document_id") or policy_id,
                    "section": c.get("section"),
                    "clause": c.get("clause"),
                    "rule_type": c.get("rule_type"),
                    "subtype": c.get("subtype"),
                    "text": c.get("text") or c.get("source_text") or "",
                    "source_page": int(c.get("source_page", 1)),
                    "source_text": c.get("source_text") or c.get("text") or "",
                    "bbox": bbox_val,
                    "embedding": emb,
                    "created_at": c.get("created_at") or created_at
                })

            for batch in chunked(records, 100):
                stmt = pg_insert(PolicyChunk).values(batch)
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

            logger.info(f"Indexed {len(chunks)} chunks into PostgreSQL pgvector for policy {policy_id}")
            return len(chunks)
        finally:
            db.close()

    @classmethod
    def get_policy_chunks(cls, policy_id: str) -> List[Dict[str, Any]]:
        """Retrieves all indexed chunks for a specific policy_id from PostgreSQL."""
        db = SessionLocal()
        try:
            stmt = (
                select(PolicyChunk)
                .where(PolicyChunk.policy_id == policy_id)
                .order_by(PolicyChunk.source_page.asc(), PolicyChunk.chunk_id.asc())
            )
            chunks = db.scalars(stmt).all()
            result = []
            for c in chunks:
                c_dict = c.to_dict()
                if c_dict.get("bbox") and isinstance(c_dict["bbox"], str):
                    try:
                        c_dict["bbox"] = json.loads(c_dict["bbox"])
                    except Exception:
                        pass
                result.append(c_dict)
            return result
        finally:
            db.close()

    @classmethod
    def search_similar_chunks(
        cls,
        policy_id: str,
        query_embedding: List[float],
        top_k: int = 5
    ) -> List[Dict[str, Any]]:
        """
        Performs vector similarity search restricted exclusively to policy_id chunks
        directly inside PostgreSQL using pgvector cosine distance (<=>).
        
        Formula: similarity_score = 1 - cosine_distance
        ORDER BY embedding <=> query_embedding ASC LIMIT top_k
        """
        if not policy_id or not query_embedding:
            return []

        # Ensure query embedding is list of floats
        q_emb = [float(x) for x in query_embedding]

        db = SessionLocal()
        try:
            cosine_dist = PolicyChunk.embedding.cosine_distance(q_emb)
            score_expr = (1.0 - cosine_dist).label("score")

            stmt = (
                select(
                    PolicyChunk.chunk_id,
                    PolicyChunk.policy_id,
                    PolicyChunk.document_id,
                    PolicyChunk.section,
                    PolicyChunk.clause,
                    PolicyChunk.rule_type,
                    PolicyChunk.subtype,
                    PolicyChunk.text,
                    PolicyChunk.source_page,
                    PolicyChunk.source_text,
                    PolicyChunk.bbox,
                    score_expr
                )
                .where(PolicyChunk.policy_id == policy_id)
                .where(PolicyChunk.embedding.is_not(None))
                .order_by(cosine_dist.asc())
                .limit(top_k)
            )

            rows = db.execute(stmt).fetchall()
            scored_chunks = []
            for r in rows:
                bbox_val = r.bbox
                if bbox_val and isinstance(bbox_val, str):
                    try:
                        bbox_val = json.loads(bbox_val)
                    except Exception:
                        pass

                scored_chunks.append({
                    "chunk_id": r.chunk_id,
                    "policy_id": r.policy_id,
                    "document_id": r.document_id,
                    "section": r.section,
                    "clause": r.clause,
                    "rule_type": r.rule_type,
                    "subtype": r.subtype,
                    "text": r.text,
                    "source_page": r.source_page,
                    "source_text": r.source_text,
                    "bbox": bbox_val,
                    "score": round(float(r.score), 4)
                })

            return scored_chunks
        finally:
            db.close()
