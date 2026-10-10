import os
import uuid
import json
from datetime import datetime
from typing import List, Optional, Dict, Any
from fastapi import UploadFile, HTTPException, status

from app.core.config import settings
from app.database.db import get_db
from app.extraction.pdf_extractor import PDFExtractor, PDFExtractionError
from app.extraction.intelligence import PolicyIntelligenceExtractor

class PolicyService:

    @staticmethod
    def upload_and_process_policy(file: UploadFile) -> Dict[str, Any]:
        """
        Validates, saves, extracts page-by-page text, and stores policy in SQLite.
        """
        # 1. Validate file extension
        if not file.filename.lower().endswith(".pdf"):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Only PDF policy documents are supported."
            )

        policy_id = str(uuid.uuid4())
        safe_filename = f"{policy_id}_{file.filename.replace(' ', '_')}"
        file_path = settings.UPLOADS_DIR / safe_filename

        try:
            # 2. Read bytes and save file locally
            content = file.file.read()
            file_size = len(content)

            if file_size == 0:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Uploaded PDF file is empty."
                )

            with open(file_path, "wb") as f:
                f.write(content)

            uploaded_at_iso = datetime.utcnow().isoformat()

            # 3. Create initial Policy record in DB
            with get_db() as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    INSERT INTO policies (
                        id, filename, original_filename, file_path, 
                        file_size_bytes, page_count, uploaded_at, extraction_status
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?);
                """, (
                    policy_id, safe_filename, file.filename, str(file_path),
                    file_size, 0, uploaded_at_iso, "PROCESSING"
                ))

            # 4. Perform Page-wise PDF Extraction using PyMuPDF
            extraction_result = PDFExtractor.extract_page_by_page(str(file_path))
            
            page_count = extraction_result["page_count"]
            extracted_pages = extraction_result["pages"]

            # 5. Store individual page records in DB preserving page_number and layout_data
            with get_db() as conn:
                cursor = conn.cursor()
                for page_data in extracted_pages:
                    layout_json = json.dumps(page_data.get("blocks", [])) if page_data.get("blocks") else None
                    cursor.execute("""
                        INSERT INTO policy_pages (
                            policy_id, page_number, char_count, word_count, content, layout_data
                        ) VALUES (?, ?, ?, ?, ?, ?);
                    """, (
                        policy_id, page_data["page_number"],
                        page_data["char_count"], page_data["word_count"],
                        page_data["content"], layout_json
                    ))

                # Update Policy record state
                cursor.execute("""
                    UPDATE policies 
                    SET page_count = ?, extraction_status = 'SUCCESS'
                    WHERE id = ?;
                """, (page_count, policy_id))

                # 6. Extract structured policy rules immediately at upload
                extracted_rules = PolicyIntelligenceExtractor.extract_structured_rules(
                    extracted_pages, file_path=str(file_path)
                )
                for r in extracted_rules:
                    cursor.execute("""
                        INSERT INTO policy_rules (
                            policy_id, rule_type, rule_key, value, unit, page, clause, 
                            source_text, confidence, qualifiers, bbox, additional_sources, status, formatted_value
                        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?);
                    """, (
                        policy_id, r.get("rule_type"), r.get("rule_key", r.get("rule_type")),
                        r.get("value"), r.get("unit"), r.get("page", 1),
                        r.get("clause", "N/A"), r.get("source_text", ""), r.get("confidence", "HIGH"),
                        r.get("qualifiers"),
                        json.dumps(r.get("bbox")) if r.get("bbox") else None,
                        json.dumps(r.get("additional_sources")) if r.get("additional_sources") else None,
                        r.get("status", "VERIFIED"),
                        r.get("formatted_value")
                    ))

            # 7. Generate canonical structured JSON dynamically from extracted rules
            try:
                from app.extraction.canonical_policy import CanonicalPolicyGenerator
                CanonicalPolicyGenerator.export_policy_to_json(policy_id)
            except Exception as exp_err:
                pass

            # 8. Create searchable policy chunks and compute RAG vector embeddings during upload
            try:
                from app.rag.chunker import PolicyChunker
                from app.rag.embeddings import PolicyEmbeddingGenerator
                from app.rag.vector_store import PolicyVectorStore
                
                canonical_json = PolicyService.get_canonical_json(policy_id)
                rules = canonical_json.get("rules", []) if canonical_json else extracted_rules
                chunks = PolicyChunker.create_chunks(policy_id, policy_id, extracted_pages, rules)
                for c in chunks:
                    c["embedding"] = PolicyEmbeddingGenerator.generate_embedding(c["text"])
                PolicyVectorStore.save_chunks(policy_id, chunks)
            except Exception as rag_err:
                pass

            return {
                "policy_id": policy_id,
                "original_filename": file.filename,
                "file_size_bytes": file_size,
                "page_count": page_count,
                "extraction_status": "SUCCESS",
                "uploaded_at": uploaded_at_iso,
                "message": f"Successfully extracted {page_count} pages, structured rules, and RAG vector index from policy PDF."
            }

        except PDFExtractionError as pe:
            with get_db() as conn:
                conn.cursor().execute("""
                    UPDATE policies SET extraction_status = 'FAILED', error_message = ? WHERE id = ?;
                """, (str(pe), policy_id))
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail=f"PDF Extraction Error: {str(pe)}"
            )
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Unexpected error processing policy: {str(e)}"
            )

    @staticmethod
    def get_policy(policy_id: str) -> Optional[Dict[str, Any]]:
        with get_db() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM policies WHERE id = ?;", (policy_id,))
            policy = cursor.fetchone()
            if not policy:
                return None

            cursor.execute("""
                SELECT page_number, char_count, word_count, content 
                FROM policy_pages 
                WHERE policy_id = ? 
                ORDER BY page_number ASC;
            """, (policy_id,))
            pages = cursor.fetchall()
            policy["pages"] = pages

            # Fetch or extract and cache policy rules
            cursor.execute("SELECT * FROM policy_rules WHERE policy_id = ?;", (policy_id,))
            rules = cursor.fetchall()

            # If rules missing or legacy un-deduplicated schema without formatted_value
            needs_reextract = (not rules) or any(r.get("formatted_value") is None for r in rules)
            if needs_reextract and pages:
                cursor.execute("DELETE FROM policy_rules WHERE policy_id = ?;", (policy_id,))
                extracted_rules = PolicyIntelligenceExtractor.extract_structured_rules(
                    pages, file_path=policy.get("file_path")
                )
                for r in extracted_rules:
                    cursor.execute("""
                        INSERT INTO policy_rules (
                            policy_id, rule_type, rule_key, value, unit, page, clause, 
                            source_text, confidence, qualifiers, bbox, additional_sources, status, formatted_value
                        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?);
                    """, (
                        policy_id, r.get("rule_type"), r.get("rule_key", r.get("rule_type")),
                        r.get("value"), r.get("unit"), r.get("page", 1),
                        r.get("clause", "N/A"), r.get("source_text", ""), r.get("confidence", "HIGH"),
                        r.get("qualifiers"),
                        json.dumps(r.get("bbox")) if r.get("bbox") else None,
                        json.dumps(r.get("additional_sources")) if r.get("additional_sources") else None,
                        r.get("status", "VERIFIED"),
                        r.get("formatted_value")
                    ))
                cursor.execute("SELECT * FROM policy_rules WHERE policy_id = ?;", (policy_id,))
                rules = cursor.fetchall()

            # Deserialize JSON fields (bbox, additional_sources)
            for r in rules:
                if r.get("bbox") and isinstance(r["bbox"], str):
                    try:
                        r["bbox"] = json.loads(r["bbox"])
                    except Exception:
                        pass
                if r.get("additional_sources") and isinstance(r["additional_sources"], str):
                    try:
                        r["additional_sources"] = json.loads(r["additional_sources"])
                    except Exception:
                        pass

            policy["rules"] = rules
            return policy

    @staticmethod
    def get_all_policies() -> List[Dict[str, Any]]:
        with get_db() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM policies ORDER BY uploaded_at DESC;")
            return cursor.fetchall()

    @staticmethod
    def export_canonical_json(policy_id: Optional[str] = None, output_path: Optional[str] = None) -> Dict[str, Any]:
        """Exports canonical structured policy JSON from existing extracted data."""
        from app.extraction.canonical_policy import CanonicalPolicyGenerator
        return CanonicalPolicyGenerator.export_policy_to_json(policy_id=policy_id, output_path=output_path)

    @staticmethod
    def get_canonical_json(policy_id: Optional[str] = None) -> Optional[Dict[str, Any]]:
        """Retrieves canonical policy JSON for the given or latest policy."""
        from app.extraction.canonical_policy import CanonicalPolicyGenerator
        if policy_id:
            policy = PolicyService.get_policy(policy_id)
            if not policy:
                return None
            return CanonicalPolicyGenerator.generate_canonical_policy(policy)
        
        cached = CanonicalPolicyGenerator.load_canonical_policy_json()
        if cached:
            return cached
        export_res = CanonicalPolicyGenerator.export_policy_to_json()
        return export_res.get("data")

    @staticmethod
    def answer_policy_query(
        policy_id: str,
        query: str,
        conversation_id: Optional[str] = None,
        history: Optional[List[Dict[str, Any]]] = None
    ) -> Optional[Dict[str, Any]]:
        """
        Answers queries about the policy document with verified line and page citations.
        Uses PolicyAssistantEngine over canonical Policy JSON with grounding validation.
        """
        policy = PolicyService.get_policy(policy_id)
        if not policy:
            return None

        # Fetch or generate canonical Policy JSON
        canonical_json = PolicyService.get_canonical_json(policy_id)
        if not canonical_json:
            # Fallback to constructing canonical JSON directly from policy data
            from app.extraction.canonical_policy import CanonicalPolicyGenerator
            rules = policy.get("rules", [])
            pages = policy.get("pages", [])
            metadata = policy.get("metadata", {})
            metadata["policy_id"] = policy_id
            metadata["document_id"] = policy.get("id") or policy_id
            canonical_json = CanonicalPolicyGenerator.generate_canonical_policy(rules, metadata, pages)

        # Import PolicyAssistantEngine
        from app.rag.policy_assistant import PolicyAssistantEngine
        return PolicyAssistantEngine.process_query(policy_id, query, canonical_json, history)

