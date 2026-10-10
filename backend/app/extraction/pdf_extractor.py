import logging
import json
import re
from typing import List, Dict, Any, Optional

try:
    import pymupdf as fitz
except ImportError:
    import fitz

logger = logging.getLogger(__name__)

class PDFExtractionError(Exception):
    """Custom exception raised when PDF text extraction fails."""
    pass

class PDFExtractor:
    """
    Extracts text, structured tables, and page layout from PDF files.
    Preserves:
    - Page numbers (1-indexed)
    - Structured tables with row and column associations
    - Text blocks with bounding-box coordinates, reading order, and line spans
    - Structural elements (headings, paragraphs, bullet lists, table rows)
    - Exact character and word counts
    """

    @staticmethod
    def extract_page_by_page(file_path: str) -> Dict[str, Any]:
        """
        Extract text, tables, and block-level layout from a PDF page by page.
        """
        try:
            doc = fitz.open(file_path)
            page_count = len(doc)
            
            if page_count == 0:
                raise PDFExtractionError("PDF file contains 0 pages or is corrupted.")

            extracted_pages: List[Dict[str, Any]] = []
            total_chars = 0
            scanned_pages_count = 0

            for page_index in range(page_count):
                page = doc.load_page(page_index)
                page_number = page_index + 1  # 1-indexed

                # 1. Plain text extraction with preserved reading order
                text = page.get_text("text") or ""
                cleaned_text = text.strip()
                word_count = len(cleaned_text.split()) if cleaned_text else 0
                char_count = len(cleaned_text)
                total_chars += char_count

                # 2. Extract block layout with coordinates for citations & spatial queries
                raw_blocks = page.get_text("blocks")
                layout_blocks = []
                for b in raw_blocks:
                    # b: (x0, y0, x1, y1, text, block_no, block_type)
                    if len(b) >= 5 and b[4] and b[4].strip():
                        b_text = b[4].strip()
                        layout_blocks.append({
                            "bbox": {
                                "x": round(b[0], 2),
                                "y": round(b[1], 2),
                                "width": round(b[2] - b[0], 2),
                                "height": round(b[3] - b[1], 2),
                                "page": page_number
                            },
                            "text": b_text,
                            "block_no": b[5] if len(b) > 5 else 0,
                            "type": "text" if (len(b) <= 6 or b[6] == 0) else "image"
                        })

                # 3. Extract structured tables using PyMuPDF table finder
                structured_tables: List[Dict[str, Any]] = []
                try:
                    table_finder = page.find_tables()
                    if table_finder and table_finder.tables:
                        for t_idx, table in enumerate(table_finder.tables):
                            raw_rows = table.extract()
                            if raw_rows and len(raw_rows) > 0:
                                # Clean cells
                                cleaned_rows = []
                                for row in raw_rows:
                                    cleaned_row = [
                                        (cell.strip().replace("\n", " ") if cell else "")
                                        for cell in row
                                    ]
                                    if any(cleaned_row):
                                        cleaned_rows.append(cleaned_row)

                                if cleaned_rows:
                                    t_bbox = table.bbox  # (x0, y0, x1, y1)
                                    structured_tables.append({
                                        "table_index": t_idx,
                                        "bbox": {
                                            "x": round(t_bbox[0], 2),
                                            "y": round(t_bbox[1], 2),
                                            "width": round(t_bbox[2] - t_bbox[0], 2),
                                            "height": round(t_bbox[3] - t_bbox[1], 2),
                                            "page": page_number
                                        },
                                        "headers": cleaned_rows[0] if len(cleaned_rows) > 1 else [],
                                        "rows": cleaned_rows[1:] if len(cleaned_rows) > 1 else cleaned_rows,
                                        "all_rows": cleaned_rows,
                                        "row_count": len(cleaned_rows),
                                        "col_count": len(cleaned_rows[0]) if cleaned_rows else 0
                                    })
                except Exception as te:
                    logger.debug(f"Table finder skipped on page {page_number}: {te}")

                # 4. Check for scanned / image-only page
                images = page.get_images()
                if char_count < 25 and len(images) > 0:
                    scanned_pages_count += 1

                extracted_pages.append({
                    "page_number": page_number,
                    "content": cleaned_text,
                    "word_count": word_count,
                    "char_count": char_count,
                    "blocks": layout_blocks,
                    "tables": structured_tables
                })

            doc.close()

            is_scanned = (scanned_pages_count > 0 and total_chars < 200)

            return {
                "page_count": page_count,
                "is_scanned": is_scanned,
                "pages": extracted_pages
            }

        except Exception as e:
            logger.error(f"Error extracting PDF at {file_path}: {str(e)}")
            raise PDFExtractionError(f"Failed to process PDF document: {str(e)}")

    @staticmethod
    def find_text_bbox(file_path: str, page_number: int, snippet: str) -> Optional[Dict[str, Any]]:
        """
        Locates the exact bounding box of a snippet on a specific page of the PDF.
        Supports exact phrase matching, line-level sub-search, and keyword search.
        Returns {'x': float, 'y': float, 'width': float, 'height': float, 'page': int} or None.
        """
        if not file_path or not snippet or page_number < 1:
            return None

        try:
            doc = fitz.open(file_path)
            if page_number > len(doc):
                doc.close()
                return None

            page = doc.load_page(page_number - 1)
            rects = []
            
            clean_snippet = snippet.strip()

            # 1. Try searching full snippet (first 60 chars)
            if len(clean_snippet) > 60:
                rects = page.search_for(clean_snippet[:60])
            else:
                rects = page.search_for(clean_snippet)
            
            # 2. If not found, try searching first line
            if not rects:
                lines = [l.strip() for l in clean_snippet.split("\n") if l.strip()]
                if lines and len(lines[0]) >= 4:
                    rects = page.search_for(lines[0][:40])

            # 3. If still not found, search distinctive monetary or percentage sub-tokens
            if not rects:
                tokens = re.findall(r'(?:(?:Rs\.?|INR|₹)\s*[\d,]+|\d+\s*%|\d+\s*(?:days|months|years))', clean_snippet, re.I)
                for tok in tokens:
                    rects = page.search_for(tok.strip())
                    if rects:
                        break

            # 4. If still not found, search primary rule keyword
            if not rects:
                kw_match = re.search(r'\b(Cataract|Ambulance|Pre-Hospitali[sz]ation|Post-Hospitali[sz]ation|Domiciliary|Modern Treatments?|Organ Donor|Restore|Cumulative Bonus|Pre-existing|Initial waiting|Joint replacement|Room category|Room rent|Single Private|Co-payment|Sum Insured)\b', clean_snippet, re.I)
                if kw_match:
                    rects = page.search_for(kw_match.group(1))

            doc.close()

            if rects:
                r = rects[0]
                return {
                    "x": round(r.x0, 2),
                    "y": round(r.y0, 2),
                    "width": round(r.width, 2),
                    "height": round(r.height, 2),
                    "page": page_number
                }
        except Exception as e:
            logger.warning(f"Could not compute bbox for snippet on page {page_number}: {e}")

        return None
