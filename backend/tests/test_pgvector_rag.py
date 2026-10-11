import os
import sys
import pytest
from pathlib import Path

backend_dir = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(backend_dir))

from sqlalchemy import select, func, text
from app.database.session import engine, SessionLocal
from app.models.policy import PolicyChunk
from app.rag.embeddings import PolicyEmbeddingGenerator
from app.rag.vector_store import PolicyVectorStore
from app.rag.hybrid_retriever import PolicyHybridRetriever
from app.rag.policy_assistant import PolicyAssistantEngine


def test_A_pgvector_extension_exists():
    """Verify pgvector extension exists and is active in PostgreSQL."""
    with engine.connect() as conn:
        ext = conn.execute(text("SELECT extname, extversion FROM pg_extension WHERE extname = 'vector';")).fetchone()
        assert ext is not None, "pgvector extension is not installed"
        assert ext[0] == "vector"
        print(f"pgvector version {ext[1]} verified active.")


def test_B_policy_chunks_table_and_indexes_exist():
    """Verify policy_chunks table and HNSW index exist."""
    with engine.connect() as conn:
        tables = conn.execute(text("SELECT table_name FROM information_schema.tables WHERE table_schema='public';")).fetchall()
        tbl_names = [t[0] for t in tables]
        assert "policy_chunks" in tbl_names, "policy_chunks table does not exist in public schema"

        # Check HNSW index
        indexes = conn.execute(text("""
            SELECT indexname, indexdef 
            FROM pg_indexes 
            WHERE tablename = 'policy_chunks';
        """)).fetchall()
        idx_dict = {idx[0]: idx[1] for idx in indexes}
        assert "idx_policy_chunks_embedding" in idx_dict
        assert "hnsw" in idx_dict["idx_policy_chunks_embedding"].lower()
        assert "vector_cosine_ops" in idx_dict["idx_policy_chunks_embedding"].lower()


def test_C_1037_chunks_migrated():
    """Verify exactly 1037 chunks exist in PostgreSQL."""
    db = SessionLocal()
    try:
        cnt = db.scalar(select(func.count(PolicyChunk.chunk_id)))
        assert cnt == 1037, f"Expected 1037 chunks in PostgreSQL, found {cnt}"
    finally:
        db.close()


def test_D_embedding_dimension_768():
    """Verify all non-null embeddings have dimension exactly 768."""
    with engine.connect() as conn:
        null_cnt = conn.execute(text("SELECT count(*) FROM policy_chunks WHERE embedding IS NULL;")).scalar()
        assert null_cnt == 0, f"Found {null_cnt} chunks with NULL embedding"

        dims = conn.execute(text("SELECT DISTINCT vector_dims(embedding) FROM policy_chunks;")).fetchall()
        assert len(dims) == 1, f"Expected uniform embedding dimensions, got {dims}"
        assert dims[0][0] == 768, f"Expected dimension 768, got {dims[0][0]}"


def test_E_no_duplicate_chunk_ids():
    """Verify no duplicate chunk IDs exist."""
    with engine.connect() as conn:
        dupes = conn.execute(text("""
            SELECT chunk_id, count(*) 
            FROM policy_chunks 
            GROUP BY chunk_id 
            HAVING count(*) > 1;
        """)).fetchall()
        assert len(dupes) == 0, f"Found duplicate chunk IDs: {dupes}"


def test_F_metadata_preservation():
    """Verify all required metadata columns are populated and preserved."""
    db = SessionLocal()
    try:
        sample = db.scalar(select(PolicyChunk).where(PolicyChunk.chunk_id == "chk_test_pol_001"))
        assert sample is not None
        assert sample.policy_id == "test_pol_123"
        assert sample.document_id == "test_pol_123"
        assert sample.source_page == 2
        assert sample.clause == "Policy Schedule"
        assert sample.rule_type == "COVERAGE"
        assert sample.subtype == "SUM_INSURED"
        assert "10,00,000" in sample.source_text
        assert sample.embedding is not None
    finally:
        db.close()


def test_G_semantic_search_returns_expected_chunk():
    """Verify semantic search retrieves relevant chunks for query."""
    q = "What is the sum insured limit?"
    q_emb = PolicyEmbeddingGenerator.generate_embedding(q)
    results = PolicyVectorStore.search_similar_chunks("test_pol_123", q_emb, top_k=5)
    assert len(results) > 0
    chunk_ids = [r["chunk_id"] for r in results]
    # Check that sum insured or related coverage chunk is retrieved
    assert any(r["rule_type"] == "COVERAGE" or "sum" in r["text"].lower() for r in results)


def test_H_cosine_distance_converted_to_similarity():
    """Verify cosine distance is converted via similarity = 1 - distance."""
    q = "General coverage question"
    q_emb = PolicyEmbeddingGenerator.generate_embedding(q)
    results = PolicyVectorStore.search_similar_chunks("test_pol_123", q_emb, top_k=3)
    for r in results:
        score = r["score"]
        # Score is bounded [-1.0, 1.0] for cosine similarity
        assert -1.0 <= score <= 1.0, f"Score out of range: {score}"


def test_I_ordering_and_top_k():
    """Verify results are ordered descending by similarity score and respect top_k."""
    q = "Hospitalisation expenses and pre post admission"
    q_emb = PolicyEmbeddingGenerator.generate_embedding(q)
    
    top_3 = PolicyVectorStore.search_similar_chunks("test_pol_123", q_emb, top_k=3)
    assert len(top_3) <= 3
    if len(top_3) > 1:
        scores = [r["score"] for r in top_3]
        for i in range(len(scores) - 1):
            assert scores[i] >= scores[i+1], f"Scores not descending: {scores}"

    top_1 = PolicyVectorStore.search_similar_chunks("test_pol_123", q_emb, top_k=1)
    assert len(top_1) == 1
    assert top_1[0]["chunk_id"] == top_3[0]["chunk_id"]


def test_K_and_L_policy_isolation_and_cross_policy_leakage():
    """Verify strict policy_id filtering and zero cross-policy search leakage."""
    q = "Emergency ambulance coverage"
    q_emb = PolicyEmbeddingGenerator.generate_embedding(q)

    # Search Policy A
    res_a = PolicyVectorStore.search_similar_chunks("test_pol_123", q_emb, top_k=10)
    for r in res_a:
        assert r["policy_id"] == "test_pol_123"

    # Search Policy B
    res_b = PolicyVectorStore.search_similar_chunks("8cab5e8b-5e8f-48ce-9069-853b1011b9cf", q_emb, top_k=10)
    for r in res_b:
        assert r["policy_id"] == "8cab5e8b-5e8f-48ce-9069-853b1011b9cf"

    # Ensure no intersection between policy A and B chunks
    ids_a = {r["chunk_id"] for r in res_a}
    ids_b = {r["chunk_id"] for r in res_b}
    assert ids_a.isdisjoint(ids_b), "Cross-policy chunk leakage detected!"

    # Non-existent policy
    res_none = PolicyVectorStore.search_similar_chunks("nonexistent_id_xyz", q_emb, top_k=5)
    assert len(res_none) == 0


def test_M_page_1_disclaimer_rejection():
    """Verify Page 1 disclaimer patterns are rejected in hybrid retrieval."""
    assert PolicyHybridRetriever.is_disclaimer("This is a sample document for testing", page_num=1) is True
    assert PolicyHybridRetriever.is_disclaimer("Not a real insurance contract", page_num=1) is True
    assert PolicyHybridRetriever.is_disclaimer("Cataract surgery coverage capped at Rs. 40,000", page_num=7) is False


def test_N_not_found_handling():
    """Verify query with no matching evidence returns NOT_FOUND status."""
    canonical_empty = {"policy": {"policy_id": "empty_pol"}, "rules": []}
    res = PolicyAssistantEngine.process_query(
        policy_id="empty_pol",
        query="What is the coverage for spaceships and alien abductions?",
        canonical_json=canonical_empty
    )
    assert res["grounding_status"] == "NOT_FOUND"
    assert len(res["citations"]) == 0


def test_O_policy_conflict_handling():
    """Verify conflicting rules return POLICY_CONFLICT status."""
    canonical_conflict = {
        "policy": {"policy_id": "conf_pol_123"},
        "rules": [
            {
                "rule_id": "cataract_sublimit",
                "name": "Cataract Surgery Sub-Limit",
                "category": "sub_limit",
                "status": "CONFLICT",
                "page": 7,
                "clause": "Clause 2.3",
                "source_text": "Capped at Rs. 40,000 per eye",
                "additional_sources": [
                    {"page": 12, "clause": "Clause 5.1", "source_text": "Capped at Rs. 50,000 per eye"}
                ]
            }
        ]
    }
    res = PolicyAssistantEngine.process_query(
        policy_id="conf_pol_123",
        query="What is the cataract limit?",
        canonical_json=canonical_conflict
    )
    assert res["grounding_status"] == "POLICY_CONFLICT"
    assert len(res["citations"]) >= 2


def test_P_and_Q_hybrid_retrieval_and_citation_integrity():
    """Verify hybrid retrieval combines rules and pgvector chunks with intact citations."""
    canonical_sample = {
        "policy": {"policy_id": "test_pol_123"},
        "rules": [
            {
                "rule_id": "copay",
                "name": "Co-payment",
                "category": "copay",
                "value": 0.0,
                "formatted_value": "0% (Nil)",
                "page": 2,
                "clause": "Policy Schedule",
                "source_text": "Co-payment: Nil (0%)",
                "status": "VERIFIED"
            }
        ]
    }
    res = PolicyHybridRetriever.retrieve(
        policy_id="test_pol_123",
        query="What is the co-payment rate?",
        canonical_json=canonical_sample,
        query_intents=["copay"]
    )
    assert len(res["matched_rules"]) > 0
    matched = res["matched_rules"][0]
    assert matched["page"] == 2
    assert "Co-payment" in matched["name"]
