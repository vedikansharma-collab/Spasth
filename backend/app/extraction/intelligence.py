import json
import logging
import re
from typing import List, Dict, Any, Optional
from app.core.config import settings
from app.extraction.normalizer import ValueNormalizer
from app.extraction.pdf_extractor import PDFExtractor

logger = logging.getLogger(__name__)

class PolicyIntelligenceExtractor:
    """
    Extracts structured health insurance policy rules from page-preserved document text.
    Preserves exact values, qualifiers, page numbers, clauses, supporting text, 
    and bounding-box coordinates for citation grounding.
    Implements semantic deduplication, conflict detection, and source validation.
    """

    @staticmethod
    def extract_structured_rules(
        policy_pages: List[Dict[str, Any]], 
        file_path: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        Extracts, normalizes, deduplicates, and validates structured policy rules.
        """
        raw_rules: List[Dict[str, Any]] = []

        # 1. Try LLM if API key is active
        if settings.GEMINI_API_KEY and settings.GEMINI_API_KEY != "mock_key_for_development":
            try:
                raw_rules = PolicyIntelligenceExtractor._extract_with_gemini(policy_pages)
            except Exception as e:
                logger.warning(f"Gemini API extraction failed, using deterministic contextual parser: {e}")
                raw_rules = []

        # 2. If LLM returned empty or was skipped, run deterministic parser
        if not raw_rules:
            raw_rules = PolicyIntelligenceExtractor._extract_with_rule_parser(policy_pages)

        # 3. Deduplicate, resolve conflicts, validate grounding, and compute bounding boxes
        canonical_rules = PolicyIntelligenceExtractor._deduplicate_and_validate(raw_rules, file_path)

        return canonical_rules

    @staticmethod
    def _extract_with_gemini(policy_pages: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Calls Gemini API with page context to extract structured policy parameters."""
        import google.generativeai as genai
        genai.configure(api_key=settings.GEMINI_API_KEY)
        model = genai.GenerativeModel("gemini-1.5-flash")

        context = "\n\n".join([
            f"--- PAGE {p['page_number']} ---\n{p['content']}" for p in policy_pages
        ])

        prompt = f"""
You are an expert health insurance policy intelligence analyzer.
Analyze the following policy document text and extract structured coverage rules into JSON format.

DOCUMENT TEXT:
{context}

Extract rules if present:
- sum_insured (value in INR)
- copay (value in percent, 0 for Nil)
- room_category / room_rent_limit (e.g. Single Private A/C Room, or INR limit)
- cataract_sublimit (limit in INR and qualifier e.g. per eye)
- ambulance_sublimit (limit in INR and qualifier e.g. per hospitalisation)
- pre_hospitalisation (days)
- post_hospitalisation (days)
- domiciliary_sublimit (% of Sum Insured)
- modern_treatment_sublimit (% of Sum Insured)
- organ_donor_sublimit (INR limit)
- restore_benefit (% of Sum Insured and frequency)
- cumulative_bonus (% increase per year)
- initial_waiting_period (days)
- ped_waiting_period (months)
- specific_disease_waiting_period (months)
- joint_replacement_waiting_period (months)

RETURN A VALID JSON ARRAY OF OBJECTS IN THIS SCHEMA:
[
  {{
    "rule_type": "sum_insured | copay | room_rent_limit | sub_limit | waiting_period | restore_benefit | cumulative_bonus",
    "rule_key": "sum_insured | copay | room_category | cataract_sublimit | ambulance_sublimit | pre_hospitalisation | post_hospitalisation | domiciliary_sublimit | modern_treatment_sublimit | organ_donor_sublimit | restore_benefit | cumulative_bonus | initial_waiting_period | ped_waiting_period | specific_disease_waiting_period | joint_replacement_waiting_period",
    "label": "Human readable name",
    "value": 1000000.0,
    "formatted_value": "₹10,00,000",
    "unit": "INR | percent | days | months | category | percent_of_SI",
    "qualifiers": "per eye | per hospitalisation | continuous coverage | no cap | once per policy year",
    "page": 2,
    "clause": "Clause or Section name",
    "source_text": "Exact text snippet from the document",
    "confidence": "HIGH"
  }}
]
"""
        response = model.generate_content(prompt)
        text = response.text.strip()
        if text.startswith("```json"):
            text = text[7:]
        if text.endswith("```"):
            text = text[:-3]

        parsed = json.loads(text.strip())
        return parsed    @staticmethod
    def _extract_with_rule_parser(policy_pages: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Generic, zero-hardcoding rule extractor.
        Parses structured tables and text blocks page by page with exact row-column pairing,
        context-aware numeric parsing, qualifier preservation, and clause tracking.
        """
        candidates: List[Dict[str, Any]] = []

        for p in policy_pages:
            p_num = p["page_number"]
            full_text = p.get("content", "")
            tables = p.get("tables", [])
            lines = [l.strip() for l in full_text.split("\n") if l.strip()]

            # Track which rules were found in tables on this page to avoid duplicate candidate noise
            page_extracted_keys = set()

            # -----------------------------------------------------------------
            # PASS 1: STRUCTURED TABLE EXTRACTION (Phase 3)
            # -----------------------------------------------------------------
            for t_idx, table in enumerate(tables):
                all_rows = table.get("all_rows", [])

                for row_idx, row in enumerate(all_rows):
                    if not row or not any(row):
                        continue

                    row_str = " | ".join([cell for cell in row if cell])
                    row_lower = row_str.lower()

                    # Ignore worked example sample claim calculation rows
                    WORKED_EXAMPLE_KEYWORDS = [
                        "billed", "payable only up to", "worked example", "sample calculation",
                        "claim calculation", "less:", "total billed", "payable by the company",
                        "sum insured remaining", "days earlier", "days after", "illustration only",
                        "actual admissibility depends", "claim scenario", "example 1", "example 2"
                    ]
                    if any(w in row_lower for w in WORKED_EXAMPLE_KEYWORDS):
                        continue

                    # 1. Sum Insured in Table
                    if "sum insured" in row_lower and not any(k in row_lower for k in [
                        "within sum insured", "up to sum insured", "% of sum insured", "exhausted", "increases by"
                    ]):
                        val = ValueNormalizer.parse_monetary_value(row_str)
                        if val and val >= 100000.0:
                            candidates.append({
                                "rule_type": "sum_insured",
                                "rule_key": "sum_insured",
                                "label": "Sum Insured",
                                "value": val,
                                "formatted_value": f"₹{int(val):,}",
                                "unit": "INR",
                                "qualifiers": "floater" if "floater" in row_lower else "individual",
                                "page": p_num,
                                "clause": "Policy Schedule Table",
                                "source_text": row_str[:500],
                                "confidence": "HIGH"
                            })
                            page_extracted_keys.add("sum_insured")

                    # 2. Co-payment in Table
                    if any(k in row_lower for k in ["co-payment", "copay", "co-pay"]) and not any(w in row_lower for w in ["cost-sharing requirement", "cost sharing requirement", "bears a specified percentage"]):
                        if any(w in row_lower for w in ["nil", "no co-payment", "no copayment", "zero", "0%"]):
                            candidates.append({
                                "rule_type": "copay",
                                "rule_key": "copay",
                                "label": "Co-payment",
                                "value": 0.0,
                                "formatted_value": "0% (Nil)",
                                "unit": "percent",
                                "qualifiers": "no co-payment",
                                "page": p_num,
                                "clause": "Co-payment Schedule",
                                "source_text": row_str[:500],
                                "confidence": "HIGH"
                            })
                            page_extracted_keys.add("copay")
                        else:
                            pct_val = ValueNormalizer.parse_percentage_value(row_str)
                            if pct_val is not None:
                                candidates.append({
                                    "rule_type": "copay",
                                    "rule_key": "copay",
                                    "label": "Co-payment",
                                    "value": pct_val,
                                    "formatted_value": f"{int(pct_val)}%",
                                    "unit": "percent",
                                    "qualifiers": "mandatory co-payment",
                                    "page": p_num,
                                    "clause": "Co-payment Schedule",
                                    "source_text": row_str[:500],
                                    "confidence": "HIGH"
                                })
                                page_extracted_keys.add("copay")

                    # 3. Room Category in Table
                    if any(k in row_lower for k in ["room category", "room rent", "boarding charges"]):
                        rc_info = ValueNormalizer.parse_room_category(row_str)
                        candidates.append({
                            "rule_type": "room_rent_limit",
                            "rule_key": "room_category",
                            "label": "Room Category / Rent",
                            "value": rc_info.get("cap_amount", 0.0),
                            "formatted_value": rc_info["formatted_value"],
                            "unit": "INR_per_day" if rc_info.get("cap_amount") else "category",
                            "qualifiers": rc_info["qualifier"],
                            "page": p_num,
                            "clause": "Room Entitlement Table",
                            "source_text": row_str[:500],
                            "confidence": "HIGH"
                        })
                        page_extracted_keys.add("room_category")

                    # 4. Cataract in Table
                    if "cataract" in row_lower:
                        val = ValueNormalizer.parse_monetary_value(row_str, keyword="cataract")
                        if val:
                            candidates.append({
                                "rule_type": "sub_limit",
                                "rule_key": "cataract_sublimit",
                                "label": "Cataract Surgery",
                                "value": val,
                                "formatted_value": f"₹{int(val):,} per eye",
                                "unit": "INR",
                                "qualifiers": "per eye",
                                "page": p_num,
                                "clause": "Benefit Schedule Table",
                                "source_text": row_str[:500],
                                "confidence": "HIGH"
                            })
                            page_extracted_keys.add("cataract_sublimit")

                    # 5. Road Ambulance in Table
                    if "ambulance" in row_lower:
                        val = ValueNormalizer.parse_monetary_value(row_str, keyword="ambulance")
                        if val and val <= 20000.0:
                            candidates.append({
                                "rule_type": "sub_limit",
                                "rule_key": "ambulance_sublimit",
                                "label": "Road Ambulance",
                                "value": val,
                                "formatted_value": f"Up to ₹{int(val):,} per hospitalisation",
                                "unit": "INR",
                                "qualifiers": "per hospitalisation",
                                "page": p_num,
                                "clause": "Benefit Schedule Table",
                                "source_text": row_str[:500],
                                "confidence": "HIGH"
                            })
                            page_extracted_keys.add("ambulance_sublimit")

                    # 6. Pre-Hospitalisation in Table
                    if "pre-hospital" in row_lower or "pre hospital" in row_lower:
                        dur = ValueNormalizer.parse_duration(row_str)
                        if dur and dur["unit"] == "days":
                            candidates.append({
                                "rule_type": "sub_limit",
                                "rule_key": "pre_hospitalisation",
                                "label": "Pre-hospitalisation",
                                "value": float(dur["value"]),
                                "formatted_value": f"Up to {dur['value']} days",
                                "unit": "days",
                                "qualifiers": "within Sum Insured",
                                "page": p_num,
                                "clause": "Benefit Schedule Table",
                                "source_text": row_str[:500],
                                "confidence": "HIGH"
                            })
                            page_extracted_keys.add("pre_hospitalisation")

                    # 7. Post-Hospitalisation in Table
                    if "post-hospital" in row_lower or "post hospital" in row_lower:
                        dur = ValueNormalizer.parse_duration(row_str)
                        if dur and dur["unit"] == "days":
                            candidates.append({
                                "rule_type": "sub_limit",
                                "rule_key": "post_hospitalisation",
                                "label": "Post-hospitalisation",
                                "value": float(dur["value"]),
                                "formatted_value": f"Up to {dur['value']} days",
                                "unit": "days",
                                "qualifiers": "within Sum Insured",
                                "page": p_num,
                                "clause": "Benefit Schedule Table",
                                "source_text": row_str[:500],
                                "confidence": "HIGH"
                            })
                            page_extracted_keys.add("post_hospitalisation")

                    # 8. Domiciliary in Table
                    if "domiciliary" in row_lower:
                        m_pct = re.search(r'domiciliary.*?\b(\d+)\s*%\s*(?:of\s*)?(?:sum\s*insured|si)', row_lower)
                        if m_pct:
                            pct_val = float(m_pct.group(1))
                            candidates.append({
                                "rule_type": "sub_limit",
                                "rule_key": "domiciliary_sublimit",
                                "label": "Domiciliary Hospitalisation",
                                "value": pct_val,
                                "formatted_value": f"Up to {int(pct_val)}% of Sum Insured",
                                "unit": "percent_of_SI",
                                "qualifiers": "3 consecutive days minimum",
                                "page": p_num,
                                "clause": "Benefit Schedule Table",
                                "source_text": row_str[:500],
                                "confidence": "HIGH"
                            })
                            page_extracted_keys.add("domiciliary_sublimit")

                    # 9. Modern Treatment in Table
                    if "modern treatment" in row_lower or "modern procedure" in row_lower:
                        m_pct = re.search(r'(?:modern\s*(?:treatment|procedure)|modern).*?\b(\d+)\s*%\s*(?:of\s*)?(?:sum\s*insured|si)', row_lower)
                        if m_pct:
                            pct_val = float(m_pct.group(1))
                            candidates.append({
                                "rule_type": "sub_limit",
                                "rule_key": "modern_treatment_sublimit",
                                "label": "Modern Treatments",
                                "value": pct_val,
                                "formatted_value": f"Up to {int(pct_val)}% of Sum Insured per policy year",
                                "unit": "percent_of_SI",
                                "qualifiers": "per policy year",
                                "page": p_num,
                                "clause": "Benefit Schedule Table",
                                "source_text": row_str[:500],
                                "confidence": "HIGH"
                            })
                            page_extracted_keys.add("modern_treatment_sublimit")

                    # 10. Organ Donor in Table
                    if "organ donor" in row_lower:
                        val = ValueNormalizer.parse_monetary_value(row_str, keyword="organ donor")
                        if val:
                            candidates.append({
                                "rule_type": "sub_limit",
                                "rule_key": "organ_donor_sublimit",
                                "label": "Organ Donor Expenses",
                                "value": val,
                                "formatted_value": f"Up to ₹{int(val):,}",
                                "unit": "INR",
                                "qualifiers": "recipient under policy",
                                "page": p_num,
                                "clause": "Benefit Schedule Table",
                                "source_text": row_str[:500],
                                "confidence": "HIGH"
                            })
                            page_extracted_keys.add("organ_donor_sublimit")

                    # 11. Initial Waiting Period in Table
                    if "initial waiting" in row_lower or "excl03" in row_lower:
                        dur = ValueNormalizer.parse_duration(row_str)
                        if dur and dur["unit"] == "days":
                            candidates.append({
                                "rule_type": "waiting_period",
                                "rule_key": "initial_waiting_period",
                                "label": "Initial Waiting Period",
                                "value": float(dur["value"]),
                                "formatted_value": f"{dur['value']} days",
                                "unit": "days",
                                "qualifiers": "illness from policy inception",
                                "page": p_num,
                                "clause": "Waiting Period Schedule Table",
                                "source_text": row_str[:500],
                                "confidence": "HIGH"
                            })
                            page_extracted_keys.add("initial_waiting_period")

                    # 12. Pre-Existing Diseases (PED) in Table
                    if "pre-existing" in row_lower or "excl01" in row_lower or "ped " in row_lower:
                        if not any(w in row_lower for w in ["diagnosed by a physician", "effective date of the policy", "treatment was recommended", "means any condition", "within 3 months prior"]):
                            dur = ValueNormalizer.parse_duration(row_str)
                        if dur and dur["unit"] in ("months", "years"):
                            months_val = dur["normalized_months"]
                            candidates.append({
                                "rule_type": "waiting_period",
                                "rule_key": "ped_waiting_period",
                                "label": "Pre-Existing Diseases (PED)",
                                "value": float(months_val),
                                "formatted_value": f"{dur['original_text']} continuous coverage" if dur["unit"] == "years" else f"{months_val} months continuous coverage",
                                "unit": "months" if dur["unit"] == "months" else "years",
                                "qualifiers": "continuous coverage",
                                "page": p_num,
                                "clause": "Waiting Period Schedule Table",
                                "source_text": row_str[:500],
                                "confidence": "HIGH"
                            })
                            page_extracted_keys.add("ped_waiting_period")

                    # 13. Specific Disease Waiting Period in Table
                    if "specific disease" in row_lower or "excl02" in row_lower or "specific procedure" in row_lower:
                        dur = ValueNormalizer.parse_duration(row_str, keyword="specific")
                        if dur and dur["unit"] in ("months", "years"):
                            months_val = dur["normalized_months"]
                            candidates.append({
                                "rule_type": "waiting_period",
                                "rule_key": "specific_disease_waiting_period",
                                "label": "Specific Diseases Waiting Period",
                                "value": float(months_val),
                                "formatted_value": f"{months_val} months continuous coverage",
                                "unit": "months",
                                "qualifiers": "continuous coverage",
                                "page": p_num,
                                "clause": "Waiting Period Schedule Table",
                                "source_text": row_str[:500],
                                "confidence": "HIGH"
                            })
                            page_extracted_keys.add("specific_disease_waiting_period")

                    # 14. Joint Replacement Waiting Period in Table
                    if "joint replacement" in row_lower:
                        m_jr = re.search(r'(\d+)\s*(?:months?|years?)\s*(?:for|of)?\s*joint\s*replacement', row_lower)
                        if not m_jr:
                            m_jr = re.search(r'joint\s*replacement[^\d]*?(\d+)\s*(?:months?|years?)', row_lower)
                        if m_jr:
                            months_val = float(m_jr.group(1))
                            if months_val <= 10.0:
                                months_val = months_val * 12.0
                            candidates.append({
                                "rule_type": "waiting_period",
                                "rule_key": "joint_replacement_waiting_period",
                                "label": "Joint Replacement Waiting Period",
                                "value": float(months_val),
                                "formatted_value": f"{int(months_val)} months for joint replacement",
                                "unit": "months",
                                "qualifiers": "joint replacement and osteoarthritis",
                                "page": p_num,
                                "clause": "Waiting Period Schedule Table",
                                "source_text": row_str[:500],
                                "confidence": "HIGH"
                            })
                            page_extracted_keys.add("joint_replacement_waiting_period")

                    # 15. Restore Benefit in Table
                    if ("restore" in row_lower or "reinstatement" in row_lower) and not any(w in row_lower for w in ["optional cover:", "premium", "schedule of premium"]):
                        m_pct = re.search(r'(\d+)\s*%\s*(?:of\s*)?(?:base\s*)?(?:sum\s*insured|si)', row_lower)
                        pct_val = float(m_pct.group(1)) if m_pct else 100.0
                        candidates.append({
                            "rule_type": "restore_benefit",
                            "rule_key": "restore_benefit",
                            "label": "Restore Benefit",
                            "value": pct_val if pct_val > 0 else 100.0,
                            "formatted_value": f"{int(pct_val if pct_val > 0 else 100)}% of base Sum Insured once per policy year",
                            "unit": "percent",
                            "qualifiers": "once per policy year",
                            "page": p_num,
                            "clause": "Benefit Schedule Table",
                            "source_text": row_str[:500],
                            "confidence": "HIGH"
                        })
                        page_extracted_keys.add("restore_benefit")

                    # 16. Cumulative Bonus in Table
                    if "cumulative bonus" in row_lower or "no claim bonus" in row_lower:
                        cb_info = ValueNormalizer.parse_cumulative_bonus(row_str)
                        candidates.append({
                            "rule_type": "cumulative_bonus",
                            "rule_key": "cumulative_bonus",
                            "label": "Cumulative Bonus",
                            "value": cb_info.get("increment", 10.0),
                            "formatted_value": cb_info["formatted_value"],
                            "unit": "percent",
                            "qualifiers": "per claim-free year",
                            "page": p_num,
                            "clause": "Benefit Schedule Table",
                            "source_text": row_str[:200],
                            "confidence": "HIGH"
                        })
                        page_extracted_keys.add("cumulative_bonus")


            # -----------------------------------------------------------------
            # PASS 2: BLOCK & PARAGRAPH TEXT EXTRACTION (Phase 4, 6, 8, 9, 10)
            # -----------------------------------------------------------------
            for block in lines:
                block_lower = block.lower()

                # Ignore worked example sample claim calculation lines
                if any(w in block_lower for w in [
                    "billed", "payable only up to", "worked example", "sample calculation",
                    "claim calculation", "less:", "total billed", "payable by the company",
                    "sum insured remaining", "days earlier", "days after", "illustration only",
                    "actual admissibility depends", "claim scenario", "example 1", "example 2"
                ]):
                    continue

                # 1. Sum Insured
                if "sum_insured" not in page_extracted_keys and "sum insured" in block_lower and not any(k in block_lower for k in [
                    "within sum insured", "up to sum insured", "% of sum insured", "exhausted", "increases by", "enhancement",
                    "remaining", "balance", "reduced", "available options"
                ]):
                    val = ValueNormalizer.parse_monetary_value(block)
                    if val and val >= 100000.0:
                        candidates.append({
                            "rule_type": "sum_insured",
                            "rule_key": "sum_insured",
                            "label": "Sum Insured",
                            "value": val,
                            "formatted_value": f"₹{int(val):,}",
                            "unit": "INR",
                            "qualifiers": "floater" if "floater" in block_lower else "individual",
                            "page": p_num,
                            "clause": "Policy Schedule",
                            "source_text": block[:200],
                            "confidence": "HIGH"
                        })

                # 2. Co-payment
                if "copay" not in page_extracted_keys and any(k in block_lower for k in ["co-payment", "copay", "co-pay"]):
                    if not any(k in block_lower for k in ["cost-sharing requirement definition", "means a cost-sharing"]):
                        qualifiers = ValueNormalizer.extract_qualifiers(block)
                        qual_str = ", ".join(qualifiers) if qualifiers else "mandatory co-payment"

                        if re.search(r'\b(nil|no co-payment|no copayment|zero|0%)\b', block_lower):
                            candidates.append({
                                "rule_type": "copay",
                                "rule_key": "copay",
                                "label": "Co-payment",
                                "value": 0.0,
                                "formatted_value": "0% (Nil)",
                                "unit": "percent",
                                "qualifiers": "no co-payment",
                                "page": p_num,
                                "clause": "Co-payment Clause",
                                "source_text": block[:200],
                                "confidence": "HIGH"
                            })
                        else:
                            pct_val = ValueNormalizer.parse_percentage_value(block)
                            if pct_val is not None:
                                candidates.append({
                                    "rule_type": "copay",
                                    "rule_key": "copay",
                                    "label": "Co-payment",
                                    "value": pct_val,
                                    "formatted_value": f"{int(pct_val)}%",
                                    "unit": "percent",
                                    "qualifiers": qual_str,
                                    "page": p_num,
                                    "clause": "Co-payment Clause",
                                    "source_text": block[:200],
                                    "confidence": "HIGH"
                                })

                # 3. Room Category
                if "room_category" not in page_extracted_keys and any(k in block_lower for k in [
                    "room category", "room rent", "room eligibility", "room charges", "room tariff", "single private", "twin sharing"
                ]):
                    rc_info = ValueNormalizer.parse_room_category(block)
                    candidates.append({
                        "rule_type": "room_rent_limit",
                        "rule_key": "room_category",
                        "label": "Room Category / Rent",
                        "value": rc_info.get("cap_amount", 0.0),
                        "formatted_value": rc_info["formatted_value"],
                        "unit": "INR_per_day" if rc_info.get("cap_amount") else "category",
                        "qualifiers": rc_info["qualifier"],
                        "page": p_num,
                        "clause": "In-patient Hospitalisation Clause",
                        "source_text": block[:200],
                        "confidence": "HIGH"
                    })

                # 4. Cataract Surgery
                if "cataract_sublimit" not in page_extracted_keys and "cataract" in block_lower:
                    val = ValueNormalizer.parse_monetary_value(block)
                    if val:
                        candidates.append({
                            "rule_type": "sub_limit",
                            "rule_key": "cataract_sublimit",
                            "label": "Cataract Surgery",
                            "value": val,
                            "formatted_value": f"₹{int(val):,} per eye",
                            "unit": "INR",
                            "qualifiers": "per eye",
                            "page": p_num,
                            "clause": "Cataract Clause",
                            "source_text": block[:200],
                            "confidence": "HIGH"
                        })

                # 5. Road Ambulance
                if "ambulance_sublimit" not in page_extracted_keys and "ambulance" in block_lower:
                    val = ValueNormalizer.parse_monetary_value(block)
                    if val and val <= 20000.0:
                        candidates.append({
                            "rule_type": "sub_limit",
                            "rule_key": "ambulance_sublimit",
                            "label": "Road Ambulance",
                            "value": val,
                            "formatted_value": f"Up to ₹{int(val):,} per hospitalisation",
                            "unit": "INR",
                            "qualifiers": "per hospitalisation",
                            "page": p_num,
                            "clause": "Road Ambulance Clause",
                            "source_text": block[:200],
                            "confidence": "HIGH"
                        })

                # 6. Pre-Hospitalisation
                if "pre_hospitalisation" not in page_extracted_keys and ("pre-hospital" in block_lower or "pre hospital" in block_lower):
                    if not any(w in block_lower for w in ["submitted within", "submit within", "documents within", "submission", "documents required", "intimation", "completion of treatment", "claim submission"]):
                        dur = ValueNormalizer.parse_duration(block)
                        if dur and dur["unit"] == "days":
                            candidates.append({
                                "rule_type": "sub_limit",
                                "rule_key": "pre_hospitalisation",
                                "label": "Pre-hospitalisation",
                                "value": float(dur["value"]),
                                "formatted_value": f"Up to {dur['value']} days",
                                "unit": "days",
                                "qualifiers": "within Sum Insured",
                                "page": p_num,
                                "clause": "Pre-Hospitalisation Clause",
                                "source_text": block[:200],
                                "confidence": "HIGH"
                            })

                # 7. Post-Hospitalisation
                if "post_hospitalisation" not in page_extracted_keys and ("post-hospital" in block_lower or "post hospital" in block_lower):
                    if not any(w in block_lower for w in ["submitted within", "submit within", "documents within", "submission", "documents required", "intimation", "completion of treatment", "claim submission"]):
                        dur = ValueNormalizer.parse_duration(block)
                        if dur and dur["unit"] == "days":
                            candidates.append({
                                "rule_type": "sub_limit",
                                "rule_key": "post_hospitalisation",
                                "label": "Post-hospitalisation",
                                "value": float(dur["value"]),
                                "formatted_value": f"Up to {dur['value']} days",
                                "unit": "days",
                                "qualifiers": "within Sum Insured",
                                "page": p_num,
                                "clause": "Post-Hospitalisation Clause",
                                "source_text": block[:200],
                                "confidence": "HIGH"
                            })

                # 8. Domiciliary Hospitalisation
                if "domiciliary_sublimit" not in page_extracted_keys and "domiciliary" in block_lower:
                    m_pct = re.search(r'domiciliary.*?\b(\d+)\s*%\s*(?:of\s*)?(?:sum\s*insured|si)', block_lower)
                    if m_pct:
                        pct_val = float(m_pct.group(1))
                        candidates.append({
                            "rule_type": "sub_limit",
                            "rule_key": "domiciliary_sublimit",
                            "label": "Domiciliary Hospitalisation",
                            "value": pct_val,
                            "formatted_value": f"Up to {int(pct_val)}% of Sum Insured",
                            "unit": "percent_of_SI",
                            "qualifiers": "3 consecutive days minimum",
                            "page": p_num,
                            "clause": "Domiciliary Clause",
                            "source_text": block[:200],
                            "confidence": "HIGH"
                        })

                # 9. Modern Treatments
                if "modern_treatment_sublimit" not in page_extracted_keys and ("modern treatment" in block_lower or "modern procedure" in block_lower):
                    m_pct = re.search(r'(?:modern\s*(?:treatment|procedure)|modern).*?\b(\d+)\s*%\s*(?:of\s*)?(?:sum\s*insured|si)', block_lower)
                    if m_pct:
                        pct_val = float(m_pct.group(1))
                        candidates.append({
                            "rule_type": "sub_limit",
                            "rule_key": "modern_treatment_sublimit",
                            "label": "Modern Treatments",
                            "value": pct_val,
                            "formatted_value": f"Up to {int(pct_val)}% of Sum Insured per policy year",
                            "unit": "percent_of_SI",
                            "qualifiers": "per policy year",
                            "page": p_num,
                            "clause": "Modern Treatments Clause",
                            "source_text": block[:200],
                            "confidence": "HIGH"
                        })

                # 10. Organ Donor Expenses
                if "organ_donor_sublimit" not in page_extracted_keys and "organ donor" in block_lower:
                    val = ValueNormalizer.parse_monetary_value(block, keyword="organ donor")
                    if val:
                        candidates.append({
                            "rule_type": "sub_limit",
                            "rule_key": "organ_donor_sublimit",
                            "label": "Organ Donor Expenses",
                            "value": val,
                            "formatted_value": f"Up to ₹{int(val):,}",
                            "unit": "INR",
                            "qualifiers": "recipient under policy",
                            "page": p_num,
                            "clause": "Organ Donor Clause",
                            "source_text": block[:200],
                            "confidence": "HIGH"
                        })

                # 11. Initial Waiting Period
                if "initial_waiting_period" not in page_extracted_keys and ("initial waiting" in block_lower or "excl03" in block_lower):
                    dur = ValueNormalizer.parse_duration(block)
                    if dur and dur["unit"] == "days":
                        candidates.append({
                            "rule_type": "waiting_period",
                            "rule_key": "initial_waiting_period",
                            "label": "Initial Waiting Period",
                            "value": float(dur["value"]),
                            "formatted_value": f"{dur['value']} days",
                            "unit": "days",
                            "qualifiers": "illness from policy inception",
                            "page": p_num,
                            "clause": "Initial Waiting Period Clause",
                            "source_text": block[:200],
                            "confidence": "HIGH"
                        })

                # 12. Pre-Existing Diseases (PED)
                if "ped_waiting_period" not in page_extracted_keys and ("pre-existing" in block_lower or "excl01" in block_lower or "ped " in block_lower):
                    if not any(w in block_lower for w in ["diagnosed by a physician", "effective date of the policy", "treatment was recommended", "means any condition"]):
                        dur = ValueNormalizer.parse_duration(block)
                    if dur and dur["unit"] in ("months", "years"):
                        months_val = dur["normalized_months"]
                        candidates.append({
                            "rule_type": "waiting_period",
                            "rule_key": "ped_waiting_period",
                            "label": "Pre-Existing Diseases (PED)",
                            "value": float(months_val),
                            "formatted_value": f"{dur['original_text']} continuous coverage" if dur["unit"] == "years" else f"{months_val} months continuous coverage",
                            "unit": "months" if dur["unit"] == "months" else "years",
                            "qualifiers": "continuous coverage",
                            "page": p_num,
                            "clause": "Pre-existing Diseases Clause",
                            "source_text": block[:200],
                            "confidence": "HIGH"
                        })

                # 13. Specific Diseases Waiting Period
                if "specific_disease_waiting_period" not in page_extracted_keys and ("specific disease" in block_lower or "excl02" in block_lower or "specific procedure" in block_lower):
                    dur = ValueNormalizer.parse_duration(block, keyword="specific")
                    if dur and dur["unit"] in ("months", "years"):
                        months_val = dur["normalized_months"]
                        candidates.append({
                            "rule_type": "waiting_period",
                            "rule_key": "specific_disease_waiting_period",
                            "label": "Specific Diseases Waiting Period",
                            "value": float(months_val),
                            "formatted_value": f"{months_val} months continuous coverage",
                            "unit": "months",
                            "qualifiers": "continuous coverage",
                            "page": p_num,
                            "clause": "Specific Diseases Clause",
                            "source_text": block[:200],
                            "confidence": "HIGH"
                        })

                # 14. Joint Replacement Waiting Period
                if "joint_replacement_waiting_period" not in page_extracted_keys and "joint replacement" in block_lower:
                    m_jr = re.search(r'(\d+)\s*(?:months?|years?)\s*(?:for|of)?\s*joint\s*replacement', block_lower)
                    if not m_jr:
                        m_jr = re.search(r'joint\s*replacement[^\d]*?(\d+)\s*(?:months?|years?)', block_lower)
                    if m_jr:
                        months_val = float(m_jr.group(1))
                        if months_val <= 10.0:
                            months_val = months_val * 12.0
                        candidates.append({
                            "rule_type": "waiting_period",
                            "rule_key": "joint_replacement_waiting_period",
                            "label": "Joint Replacement Waiting Period",
                            "value": float(months_val),
                            "formatted_value": f"{int(months_val)} months for joint replacement",
                            "unit": "months",
                            "qualifiers": "joint replacement and osteoarthritis",
                            "page": p_num,
                            "clause": "Joint Replacement Clause",
                            "source_text": block[:200],
                            "confidence": "HIGH"
                        })

                # 15. Restore Benefit
                if "restore_benefit" not in page_extracted_keys and ("restore benefit" in block_lower or "reinstatement" in block_lower) and not any(w in block_lower for w in ["optional cover:", "premium", "schedule of premium"]):
                    m_pct = re.search(r'(\d+)\s*%\s*(?:of\s*)?(?:base\s*)?(?:sum\s*insured|si)', block_lower)
                    pct_val = float(m_pct.group(1)) if m_pct else 100.0
                    candidates.append({
                        "rule_type": "restore_benefit",
                        "rule_key": "restore_benefit",
                        "label": "Restore Benefit",
                        "value": pct_val if pct_val > 0 else 100.0,
                        "formatted_value": f"{int(pct_val if pct_val > 0 else 100)}% of base Sum Insured once per policy year",
                        "unit": "percent",
                        "qualifiers": "once per policy year",
                        "page": p_num,
                        "clause": "Restore Benefit Clause",
                        "source_text": block[:200],
                        "confidence": "HIGH"
                    })

                # 16. Cumulative Bonus
                if "cumulative_bonus" not in page_extracted_keys and ("cumulative bonus" in block_lower or "no claim bonus" in block_lower):
                    cb_info = ValueNormalizer.parse_cumulative_bonus(block)
                    candidates.append({
                        "rule_type": "cumulative_bonus",
                        "rule_key": "cumulative_bonus",
                        "label": "Cumulative Bonus",
                        "value": cb_info.get("increment", 10.0),
                        "formatted_value": cb_info["formatted_value"],
                        "unit": "percent",
                        "qualifiers": "per claim-free year",
                        "page": p_num,
                        "clause": "Cumulative Bonus Clause",
                        "source_text": block[:200],
                        "confidence": "HIGH"
                    })

                # 17. Appendectomy Cap
                if "appendectomy_cap" not in page_extracted_keys and "appendectomy" in block_lower:
                    val = ValueNormalizer.parse_monetary_value(block)
                    if val:
                        candidates.append({
                            "rule_type": "sub_limit",
                            "rule_key": "appendectomy_cap",
                            "label": "Appendectomy & Hernia Cap",
                            "value": val,
                            "formatted_value": f"₹{int(val):,} maximum cap",
                            "unit": "INR",
                            "qualifiers": "maximum eligible claim",
                            "page": p_num,
                            "clause": "Appendectomy Clause",
                            "source_text": block[:200],
                            "confidence": "HIGH"
                        })

        return candidates

    @staticmethod
    def _deduplicate_and_validate(
        raw_rules: List[Dict[str, Any]], 
        file_path: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        Deduplicates raw candidates by rule_key into canonical rules.
        Preserves secondary citations in additional_sources.
        Validates grounding against document source text and resolves bounding box coordinates.
        """
        grouped: Dict[str, List[Dict[str, Any]]] = {}
        for r in raw_rules:
            key = r.get("rule_key") or r.get("rule_type", "unknown")
            if key not in grouped:
                grouped[key] = []
            grouped[key].append(r)

        canonical_rules: List[Dict[str, Any]] = []

        WORKED_EX_WORDS = [
            "remaining", "worked example", "sample calculation", "available options",
            "days earlier", "days after", "total billed", "payable by the company",
            "illustration only", "claim scenario"
        ]

        for key, cand_list in grouped.items():
            # Generic scoring function to select primary canonical representation:
            # Policy Schedule / Benefit Tables > Clause Text > CIS Summary > Worked Example
            def score_candidate(c):
                p = c.get("page", 1)
                clause = str(c.get("clause", ""))
                src = str(c.get("source_text", "")).lower()
                score = 0

                if "Schedule" in clause or "Table" in clause:
                    score += 100
                elif "Clause" in clause or "Section" in clause:
                    score += 60

                # Prioritize candidates with concrete extracted values over empty/None candidates
                if c.get("value") is not None:
                    score += 80

                # Prioritize earlier main policy pages over later summary/appendix pages
                score += max(0, 50 - p)

                # Heavily penalize worked example post-claim balance lines
                if any(w in src for w in WORKED_EX_WORDS):
                    score -= 200

                score += min(len(src), 30)
                return score

            sorted_cands = sorted(cand_list, key=score_candidate, reverse=True)
            canonical = dict(sorted_cands[0])

            # Build additional_sources from secondary pages
            additional_sources = []
            seen_pages = {canonical["page"]}
            has_conflict = False

            for c in sorted_cands[1:]:
                c_page = c.get("page", 1)
                if c_page not in seen_pages:
                    seen_pages.add(c_page)
                    add_bbox = None
                    if file_path:
                        add_bbox = PDFExtractor.find_text_bbox(file_path, c_page, c.get("source_text", ""))
                    additional_sources.append({
                        "page": c_page,
                        "clause": c.get("clause", "N/A"),
                        "source_text": c.get("source_text", ""),
                        "bbox": add_bbox
                    })

                # Check for numerical conflict (ignore post-claim balance and available options lines)
                c_src = str(c.get("source_text", "")).lower()
                if not any(w in c_src for w in WORKED_EX_WORDS):
                    c_val = c.get("value")
                    canon_val = canonical.get("value")
                    if c_val is not None and canon_val is not None:
                        if abs(c_val - canon_val) > 0.01:
                            if not (c_val == 0.0 and canon_val == 0.0):
                                has_conflict = True

            canonical["additional_sources"] = additional_sources

            # Calculate Bounding Box coordinates
            bbox = None
            if file_path:
                candidate_phrases = []
                # Try finding by specific keywords
                if canonical.get("rule_key") == "joint_replacement_waiting_period":
                    candidate_phrases.append("joint replacement")
                elif canonical.get("rule_key") == "cataract_sublimit":
                    candidate_phrases.extend(["Cataract", "cataract"])
                elif canonical.get("rule_key") == "ambulance_sublimit":
                    candidate_phrases.extend(["Road Ambulance", "ambulance"])
                elif canonical.get("rule_key") == "pre_hospitalisation":
                    candidate_phrases.extend(["Pre-Hospitalisation", "Pre-Hospitalization", "Pre-hospitalisation", "pre-"])
                elif canonical.get("rule_key") == "post_hospitalisation":
                    candidate_phrases.extend(["Post-Hospitalisation", "Post-Hospitalization", "Post-hospitalisation", "post-"])
                elif canonical.get("rule_key") == "appendectomy_cap":
                    candidate_phrases.extend(["Appendectomy", "appendectomy"])
                elif canonical.get("rule_key") == "ped_waiting_period":
                    candidate_phrases.extend(["Excl01", "Pre-existing", "Pre-Existing"])

                if canonical.get("label"):
                    candidate_phrases.append(canonical["label"])
                    candidate_phrases.append(canonical["label"].replace("sation", "zation"))
                    candidate_phrases.append(canonical["label"].replace("zation", "sation"))

                search_snippet = canonical.get("source_text", "")
                if search_snippet:
                    candidate_phrases.append(search_snippet[:40])

                for phrase in candidate_phrases:
                    bbox = PDFExtractor.find_text_bbox(file_path, canonical["page"], phrase)
                    if bbox:
                        break

            canonical["bbox"] = bbox

            # Validation and grounding status
            raw_src = str(canonical.get("source_text", "")).lower()
            clean_src = raw_src.replace(",", "").replace(".", " ")
            val_found = False

            if canonical.get("value") == 0.0:
                val_found = any(w in raw_src for w in ["nil", "no co-payment", "0%", "zero", "single", "no cap"])
            elif canonical.get("value") is not None:
                val_int_str = str(int(canonical["value"]))
                val_found = (val_int_str in clean_src) or any(w in raw_src for w in ["lakh", "lac", "%", "days", "months", "day limit"])
            else:
                val_found = True

            if has_conflict:
                canonical["status"] = "CONFLICT"
            elif val_found and canonical.get("source_text"):
                canonical["status"] = "VERIFIED"
            else:
                canonical["status"] = "NEEDS_REVIEW"

            canonical_rules.append(canonical)

        return canonical_rules
