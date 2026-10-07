import os
import uuid
from datetime import datetime
from typing import List, Optional, Dict, Any
from fastapi import UploadFile, HTTPException, status

from app.core.config import settings
from app.database.db import get_db
from app.extraction.pdf_extractor import PDFExtractor, PDFExtractionError

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

            # 5. Store individual page records in DB preserving page_number
            with get_db() as conn:
                cursor = conn.cursor()
                for page_data in extracted_pages:
                    cursor.execute("""
                        INSERT INTO policy_pages (
                            policy_id, page_number, char_count, word_count, content
                        ) VALUES (?, ?, ?, ?, ?);
                    """, (
                        policy_id, page_data["page_number"],
                        page_data["char_count"], page_data["word_count"],
                        page_data["content"]
                    ))

                # Update Policy record state
                cursor.execute("""
                    UPDATE policies 
                    SET page_count = ?, extraction_status = 'SUCCESS'
                    WHERE id = ?;
                """, (page_count, policy_id))

            return {
                "policy_id": policy_id,
                "original_filename": file.filename,
                "file_size_bytes": file_size,
                "page_count": page_count,
                "extraction_status": "SUCCESS",
                "uploaded_at": uploaded_at_iso,
                "message": f"Successfully extracted {page_count} pages from policy PDF."
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
            if not rules and pages:
                from app.extraction.intelligence import PolicyIntelligenceExtractor
                extracted_rules = PolicyIntelligenceExtractor.extract_structured_rules(pages)
                for r in extracted_rules:
                    cursor.execute("""
                        INSERT INTO policy_rules (
                            policy_id, rule_type, rule_key, value, unit, page, clause, source_text, confidence
                        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?);
                    """, (
                        policy_id, r["rule_type"], r.get("rule_key", r["rule_type"]),
                        r.get("value"), r.get("unit"), r.get("page", 1),
                        r.get("clause", "N/A"), r.get("source_text", ""), r.get("confidence", "HIGH")
                    ))
                rules = extracted_rules
            policy["rules"] = rules
            return policy

    @staticmethod
    def get_all_policies() -> List[Dict[str, Any]]:
        with get_db() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM policies ORDER BY uploaded_at DESC;")
            return cursor.fetchall()
