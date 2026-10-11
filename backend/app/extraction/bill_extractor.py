import logging
import re
from typing import Dict, Any, List, Optional
import fitz  # PyMuPDF
from app.core.config import settings

logger = logging.getLogger(__name__)

# Standard procedures recognized by SPASTH
KNOWN_PROCEDURES = [
    'Angioplasty', 'Appendectomy', 'Arthroscopy', 'C-Section', 'CABG',
    'Cataract Surgery', 'Chemotherapy', 'Cholecystectomy', 'Dialysis',
    'Hemorrhoidectomy', 'Hernia Repair', 'Hip Replacement', 'Hysterectomy',
    'Kidney Stone Removal', 'Knee Replacement', 'Normal Delivery',
    'Septoplasty', 'Thyroidectomy', 'Tonsillectomy', 'Tympanoplasty'
]

PROCEDURE_SYNONYMS = {
    'appendix': 'Appendectomy',
    'appendicitis': 'Appendectomy',
    'appendectomy': 'Appendectomy',
    'cataract': 'Cataract Surgery',
    'phaco': 'Cataract Surgery',
    'knee replacement': 'Knee Replacement',
    'tka': 'Knee Replacement',
    'tkr': 'Knee Replacement',
    'c-section': 'C-Section',
    'cesarean': 'C-Section',
    'caesarean': 'C-Section',
    'lscs': 'C-Section',
    'angioplasty': 'Angioplasty',
    'ptca': 'Angioplasty',
    'stent': 'Angioplasty',
    'hernia': 'Hernia Repair',
    'hernioplasty': 'Hernia Repair',
    'cholecystectomy': 'Cholecystectomy',
    'gallbladder': 'Cholecystectomy',
    'kidney stone': 'Kidney Stone Removal',
    'urssl': 'Kidney Stone Removal',
    'pcnl': 'Kidney Stone Removal',
    'lithotripsy': 'Kidney Stone Removal',
    'hysterectomy': 'Hysterectomy',
    'hip replacement': 'Hip Replacement',
    'tha': 'Hip Replacement',
    'thr': 'Hip Replacement',
    'cabg': 'CABG',
    'bypass': 'CABG',
    'normal delivery': 'Normal Delivery',
    'vaginal delivery': 'Normal Delivery',
    'tonsillectomy': 'Tonsillectomy',
    'tonsil': 'Tonsillectomy',
    'hemorrhoidectomy': 'Hemorrhoidectomy',
    'piles': 'Hemorrhoidectomy',
    'dialysis': 'Dialysis',
    'hemodialysis': 'Dialysis',
    'chemotherapy': 'Chemotherapy',
    'chemo': 'Chemotherapy',
    'tympanoplasty': 'Tympanoplasty',
    'eardrum': 'Tympanoplasty',
    'septoplasty': 'Septoplasty',
    'dns': 'Septoplasty',
    'arthroscopy': 'Arthroscopy',
    'acl': 'Arthroscopy',
    'thyroidectomy': 'Thyroidectomy',
    'thyroid': 'Thyroidectomy',
}

NON_COVERED_KEYWORDS = [
    'consumable', 'non-medical', 'non medical', 'administrative', 'admin fee',
    'admission charge', 'admission fee', 'registration', 'file charge',
    'sanitizer', 'mask', 'ppe', 'gloves', 'thermometer', 'tissue',
    'toiletries', 'gown', 'bedsheet', 'food', 'diet', 'beverage',
    'visitor', 'miscellaneous', 'non-payable', 'not covered'
]

class HospitalBillExtractor:
    """
    Extracts financial figures, hospital metadata, procedure details,
    and non-covered consumable amounts from uploaded hospital bills (PDF format).
    Uses Gemini API if available, with robust deterministic fallback.
    """

    @classmethod
    def extract_from_bytes(cls, pdf_bytes: bytes, filename: str = "bill.pdf") -> Dict[str, Any]:
        """
        Parses a PDF byte stream and returns structured bill details.
        """
        if not pdf_bytes or len(pdf_bytes) == 0:
            return {
                "status": "ERROR",
                "message": "Uploaded PDF file is empty.",
                "total_amount": 0.0,
                "non_covered_amount": 0.0
            }

        try:
            doc = fitz.open(stream=pdf_bytes, filetype="pdf")
        except Exception as e:
            logger.error(f"Failed to open PDF bill: {e}")
            return {
                "status": "ERROR",
                "message": f"Invalid or corrupted PDF file: {str(e)}",
                "total_amount": 0.0,
                "non_covered_amount": 0.0
            }

        if len(doc) == 0:
            return {
                "status": "ERROR",
                "message": "PDF bill contains no pages.",
                "total_amount": 0.0,
                "non_covered_amount": 0.0
            }

        # 1. Extract text and table rows from all pages
        full_text_pages = []
        table_rows = []
        for p_idx in range(len(doc)):
            page = doc[p_idx]
            p_text = page.get_text("text") or ""
            full_text_pages.append(p_text)

            # PyMuPDF tables
            try:
                tables = page.find_tables()
                if tables and tables.tables:
                    for tbl in tables.tables:
                        rows = tbl.extract()
                        if rows:
                            for r in rows:
                                cleaned = [cell.strip().replace("\n", " ") for cell in r if cell]
                                if cleaned:
                                    table_rows.append(cleaned)
            except Exception:
                pass

        full_text = "\n\n".join(full_text_pages)

        # 2. Run Deterministic Regex & Tabular Parser first (instant, high accuracy on standard hospital invoices)
        det_res = cls._extract_deterministically(full_text, table_rows, filename)
        if det_res.get("confidence") == "HIGH" and det_res.get("total_amount", 0) > 0:
            return det_res

        # 3. Try Gemini Extraction if deterministic parser yielded low confidence
        if settings.GEMINI_API_KEY and settings.GEMINI_API_KEY != "mock_key_for_development":
            try:
                llm_res = cls._extract_with_gemini(full_text)
                if llm_res and llm_res.get("total_amount", 0) > 0:
                    llm_res["status"] = "SUCCESS"
                    llm_res["source"] = "Gemini LLM Extractor"
                    llm_res["filename"] = filename
                    return llm_res
            except Exception as e:
                logger.warning(f"Gemini bill extraction failed, proceeding with deterministic parser: {e}")

        return det_res

    @classmethod
    def _extract_with_gemini(cls, text: str) -> Optional[Dict[str, Any]]:
        import google.generativeai as genai
        genai.configure(api_key=settings.GEMINI_API_KEY)
        model = None
        for m_name in ["gemini-3.8-flash", "gemini-2.5-flash", "gemini-1.5-flash"]:
            try:
                model = genai.GenerativeModel(m_name)
                break
            except Exception:
                pass
        if not model:
            return None

        prompt = f"""You are a specialized medical insurance bill audit engine.
Analyze the following hospital invoice/bill text and extract structured financial details in JSON format:

{text[:8000]}

Respond ONLY with a JSON object matching this exact schema:
{{
  "total_amount": <float, total bill amount or net payable>,
  "non_covered_amount": <float, total of consumables, admin fees, or non-medical items, or 0.0>,
  "hospital_name": "<string or null>",
  "patient_name": "<string or null>",
  "bill_number": "<string or null>",
  "bill_date": "<string or null>",
  "detected_procedure": "<string, one of {KNOWN_PROCEDURES} or null>",
  "confidence": "<HIGH, MEDIUM, or LOW>",
  "line_items_summary": [
    {{"description": "<item name>", "amount": <float>, "is_non_covered": <boolean>}}
  ]
}}
"""
        response = model.generate_content(prompt)
        raw_output = response.text.strip()
        if raw_output.startswith("```json"):
            raw_output = raw_output[7:]
        if raw_output.startswith("```"):
            raw_output = raw_output[3:]
        if raw_output.endswith("```"):
            raw_output = raw_output[:-3]
        data = json_loads_safe(raw_output.strip())
        return data

    @classmethod
    def _extract_deterministically(cls, text: str, table_rows: List[List[str]], filename: str) -> Dict[str, Any]:
        """
        Extract total amount, non-covered charges, hospital name, and procedure deterministically.
        """
        lines = [line.strip() for line in text.split("\n") if line.strip()]

        total_amount = 0.0
        confidence = "LOW"

        # Regex patterns for total amounts
        # Priority 1: Explicit Grand Total / Net Payable / Final Bill Amount
        high_priority_patterns = [
            r'(?i)(?:grand\s*total|net\s*(?:payable|amount|bill)|final\s*(?:bill\s*amount|amount)|total\s*payable|amount\s*payable)\s*[:=\-–]?\s*(?:rs\.?|inr|₹)?\s*([0-9]{1,3}(?:,[0-9]{2,3})*(?:\.[0-9]{1,2})?|[0-9]+(?:\.[0-9]{1,2})?)',
            r'(?i)(?:total\s*(?:bill\s*amount|bill|invoice\s*amount|charges|amount))\s*[:=\-–]?\s*(?:rs\.?|inr|₹)?\s*([0-9]{1,3}(?:,[0-9]{2,3})*(?:\.[0-9]{1,2})?|[0-9]+(?:\.[0-9]{1,2})?)',
            r'(?i)(?:total)\s*[:=\-–]\s*(?:rs\.?|inr|₹)?\s*([0-9]{1,3}(?:,[0-9]{2,3})*(?:\.[0-9]{1,2})?|[0-9]+(?:\.[0-9]{1,2})?)'
        ]

        found_totals = []

        for pat in high_priority_patterns:
            matches = re.finditer(pat, text)
            for m in matches:
                val_str = m.group(1).replace(",", "")
                try:
                    val = float(val_str)
                    if val > 100:  # Reasonable hospital bill minimum
                        found_totals.append((val, "HIGH", m.group(0)))
                except ValueError:
                    pass

        # Also inspect table rows (especially bottom rows where summary totals live)
        for row in reversed(table_rows):
            row_str = " ".join(row).lower()
            if any(term in row_str for term in ["grand total", "net payable", "total amount", "net amount", "total bill", "total"]):
                # Extract numbers from this row
                for cell in reversed(row):
                    clean_cell = cell.replace("₹", "").replace("Rs.", "").replace("INR", "").replace(",", "").strip()
                    try:
                        val = float(clean_cell)
                        if val > 100:
                            found_totals.append((val, "HIGH", f"Table row: {row_str}"))
                            break
                    except ValueError:
                        pass
            if found_totals:
                break

        # Select the most appropriate total amount
        if found_totals:
            # Usually the highest explicit total or last summary total
            total_amount = max([item[0] for item in found_totals])
            confidence = "HIGH"
        else:
            # Fallback: scan for any line with currency and large amounts
            currency_pattern = r'(?i)(?:rs\.?|inr|₹)\s*([0-9]{1,3}(?:,[0-9]{2,3})*(?:\.[0-9]{1,2})?|[0-9]{4,}(?:\.[0-9]{1,2})?)'
            all_amounts = []
            for m in re.finditer(currency_pattern, text):
                clean_num = m.group(1).replace(",", "")
                try:
                    val = float(clean_num)
                    if val > 500:
                        all_amounts.append(val)
                except ValueError:
                    pass
            if all_amounts:
                total_amount = max(all_amounts)
                confidence = "MEDIUM"

        # Extract Non-Covered Items (consumables, admin, etc.)
        non_covered_amount = 0.0
        detected_non_covered_items = []
        for line in lines:
            line_lower = line.lower()
            if any(kw in line_lower for kw in NON_COVERED_KEYWORDS) and not any(tot_kw in line_lower for tot_kw in ["grand total", "net total", "total bill"]):
                # Look for monetary amounts in this line
                amt_matches = re.findall(r'(?:rs\.?|inr|₹)?\s*([0-9]{1,3}(?:,[0-9]{2,3})*(?:\.[0-9]{1,2})?|[0-9]+(?:\.[0-9]{1,2})?)', line)
                for am in amt_matches:
                    am_clean = am.replace(",", "")
                    try:
                        val = float(am_clean)
                        # Ensure reasonable consumable amount (typically < total bill and < 50,000)
                        if 10 <= val <= 50000 and (total_amount == 0 or val < total_amount):
                            non_covered_amount += val
                            detected_non_covered_items.append({"description": line[:60], "amount": val, "is_non_covered": True})
                            break
                    except ValueError:
                        pass

        # Also search table rows for non-covered items
        for row in table_rows:
            row_str = " ".join(row).lower()
            if any(kw in row_str for kw in NON_COVERED_KEYWORDS):
                for cell in reversed(row):
                    clean_cell = cell.replace("₹", "").replace("Rs.", "").replace("INR", "").replace(",", "").strip()
                    try:
                        val = float(clean_cell)
                        if 10 <= val <= 50000 and (total_amount == 0 or val < total_amount):
                            if not any(d["amount"] == val for d in detected_non_covered_items):
                                non_covered_amount += val
                                detected_non_covered_items.append({"description": row_str[:60], "amount": val, "is_non_covered": True})
                            break
                    except ValueError:
                        pass

        # Detect hospital name
        hospital_name = None
        for i in range(min(12, len(lines))):
            l = lines[i]
            if any(h_kw in l.lower() for h_kw in ["hospital", "clinic", "healthcare", "medical centre", "health city", "multispeciality", "institute of medical"]):
                hospital_name = l.strip()
                break

        # Detect Bill / Invoice Number
        bill_number = None
        bill_match = re.search(r'(?i)(?:bill\s*(?:no\.?|number)|invoice\s*(?:no\.?|number)|bill\s*#|invoice\s*#|ipd\s*(?:no\.?|number)|receipt\s*(?:no\.?|number))\s*[:=\-–]?\s*([A-Za-z0-9\-_/]+)', text)
        if bill_match:
            bill_number = bill_match.group(1).strip()

        # Detect Procedure
        detected_procedure = None
        text_lower = text.lower()
        for syn, canonical in PROCEDURE_SYNONYMS.items():
            if re.search(r'\b' + re.escape(syn) + r'\b', text_lower):
                detected_procedure = canonical
                break

        return {
            "status": "SUCCESS" if total_amount > 0 else "PARTIAL",
            "message": f"Successfully extracted total bill amount: ₹{total_amount:,.2f}" if total_amount > 0 else "Could not detect a clear total amount.",
            "total_amount": round(total_amount, 2),
            "non_covered_amount": round(non_covered_amount, 2),
            "hospital_name": hospital_name or "Hospital / Clinic",
            "bill_number": bill_number or "N/A",
            "detected_procedure": detected_procedure,
            "confidence": confidence,
            "source": "Deterministic Pattern & Table Engine",
            "filename": filename,
            "line_items_summary": detected_non_covered_items[:5]
        }

def json_loads_safe(raw: str) -> Optional[Dict[str, Any]]:
    import json
    try:
        return json.loads(raw)
    except Exception:
        # Regex search for JSON object inside output
        match = re.search(r'\{.*\}', raw, re.DOTALL)
        if match:
            try:
                return json.loads(match.group(0))
            except Exception:
                return None
        return None
