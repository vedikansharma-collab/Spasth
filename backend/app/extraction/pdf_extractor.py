try:
    import pymupdf as fitz
except ImportError:
    import fitz

import logging
from typing import List, Dict, Any

logger = logging.getLogger(__name__)

class PDFExtractionError(Exception):
    """Custom exception raised when PDF text extraction fails."""
    pass

class PDFExtractor:
    """
    Extracts text page-by-page from PDF files preserving page numbers and document structure.
    Uses PyMuPDF (fitz) for fast, reliable extraction.
    """

    @staticmethod
    def extract_page_by_page(file_path: str) -> Dict[str, Any]:
        """
        Extract text from a PDF document page by page.
        
        Returns:
            Dict containing:
            - page_count: Total number of pages
            - pages: List of Dicts with keys: page_number, content, char_count, word_count
        """
        try:
            doc = fitz.open(file_path)
            page_count = len(doc)
            
            if page_count == 0:
                raise PDFExtractionError("PDF file contains 0 pages or is corrupted.")

            extracted_pages: List[Dict[str, Any]] = []

            for page_index in range(page_count):
                page = doc.load_page(page_index)
                page_number = page_index + 1  # 1-indexed for human-readable policy citations
                
                # Extract clean text from page
                text = page.get_text("text") or ""
                
                # Normalize text line endings and basic whitespace without destroying section structure
                cleaned_text = text.strip()
                
                word_count = len(cleaned_text.split()) if cleaned_text else 0
                char_count = len(cleaned_text)

                extracted_pages.append({
                    "page_number": page_number,
                    "content": cleaned_text,
                    "word_count": word_count,
                    "char_count": char_count
                })

            doc.close()

            return {
                "page_count": page_count,
                "pages": extracted_pages
            }

        except Exception as e:
            logger.error(f"Error extracting PDF at {file_path}: {str(e)}")
            raise PDFExtractionError(f"Failed to process PDF document: {str(e)}")
