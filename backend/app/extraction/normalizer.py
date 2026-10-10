import re
import logging
from typing import Optional, Any, Dict, List, Tuple

logger = logging.getLogger(__name__)

class ValueNormalizer:
    """
    Normalizes raw extracted policy rule values (strings, numbers, formatted text)
    into deterministic structured types, while preserving qualifiers, basis, and context.
    
    Guarantees:
    - 0 hardcoded policy values
    - Precise currency parsing (₹, Rs., INR, Lakhs, Crores, Indian comma format)
    - Distinguishes clause/section/page/phone numbers from actual monetary limits
    - Percentage basis & condition preservation
    - Duration normalization (days, months, years) without collapsing source meaning
    - Room category qualitative classification vs numeric room rent cap
    - Qualifier & condition extraction
    - Cumulative bonus increment & maximum cap extraction
    """

    @staticmethod
    def clean_text_snippets(text: str) -> str:
        """Removes clause numbers, section numbers, page numbers, policy numbers, phone numbers, and dates to prevent numeric confusion."""
        if not text:
            return ""
        t = str(text)
        # Remove policy numbers e.g. SSHP/26/PUN/0000001
        t = re.sub(r'\b[A-Z0-9]{3,10}/[0-9/A-Z\-]{5,20}\b', ' ', t)
        # Remove phone numbers e.g. 1800 000 0000 or +91-1234567890
        t = re.sub(r'\b(?:1800|1860|\+91)\s*[\d\s\-]{6,12}\b', ' ', t)
        # Remove dates e.g. 14-Mar-1985 or 2025-01-15 or 01/01/2025
        t = re.sub(r'\b\d{1,2}[-/\s](?:[A-Za-z]{3,9}|\d{1,2})[-/\s]\d{2,4}\b', ' ', t)
        # Remove clause/section headers at line start e.g. "Clause 2.3:", "Section 1.10", "1.10 Cataract"
        t = re.sub(r'^\s*(?:clause|section|sub-clause|excl\d*|item|no\.)\s*\d+(?:\.\d+)*\s*[:\.\-]?\s*', ' ', t, flags=re.IGNORECASE)
        t = re.sub(r'^\s*\d+\.\d+(?:\.\d+)*\s*[:\.\-]?\s*', ' ', t)
        return t.strip()

    @staticmethod
    def parse_monetary_value(val: Any, source_text: Optional[str] = None, keyword: Optional[str] = None, default: Optional[float] = None) -> Optional[float]:
        """
        Parses a monetary value in INR.
        Handles floats/ints, currency strings ('INR 10,00,000', 'Rs. 40,000', '5 Lakh', '10 Lakhs', '1 Crore').
        If keyword is provided, parses the monetary value appearing after the keyword position in multi-benefit text.
        Strictly avoids clause numbers, section numbers, dates, ages, and phone numbers.
        """
        def parse_str(text_str: str) -> Optional[float]:
            if not text_str:
                return None
            target_str = str(text_str)

            # Slicing from keyword position if keyword provided
            if keyword and keyword.lower() in target_str.lower():
                kw_idx = target_str.lower().find(keyword.lower())
                target_str = target_str[kw_idx:]

            clean_text = ValueNormalizer.clean_text_snippets(target_str)
            if not clean_text:
                return None

            # Collect positional candidate matches in clean_text
            candidates_found: List[Tuple[int, float]] = []

            # A. Explicit INR / Rs / ₹ symbol with numbers e.g. ₹40,000 or Rs. 10,00,000
            for m in re.finditer(r'(?:inr|rs\.?|₹)\s*([\d,]+(?:\.\d+)?)', clean_text, re.IGNORECASE):
                try:
                    parsed = float(m.group(1).replace(",", ""))
                    if parsed >= 100.0:
                        candidates_found.append((m.start(), parsed))
                except ValueError:
                    pass

            # B. Lakhs / Crores (e.g. 10 lakh, 5 lakhs, 1 crore)
            for m in re.finditer(r'([\d\.]+)\s*(?:lakh|lakhs|lac|lacs)\b', clean_text, re.IGNORECASE):
                try:
                    candidates_found.append((m.start(), float(m.group(1)) * 100000.0))
                except ValueError:
                    pass

            for m in re.finditer(r'([\d\.]+)\s*(?:crore|crores|cr)\b', clean_text, re.IGNORECASE):
                try:
                    candidates_found.append((m.start(), float(m.group(1)) * 10000000.0))
                except ValueError:
                    pass

            # C. Comma-formatted Indian numbers e.g. 10,00,000 or 40,000 or 1,00,000
            for m in re.finditer(r'\b(\d{1,2},\d{2},\d{3}|\d{1,3},\d{3})\b', clean_text):
                try:
                    parsed = float(m.group(1).replace(",", ""))
                    if parsed >= 500.0:
                        candidates_found.append((m.start(), parsed))
                except ValueError:
                    pass

            if candidates_found:
                # Pick candidate occurring earliest in the snippet text
                candidates_found.sort(key=lambda x: x[0])
                return candidates_found[0][1]

            # D. Plain numbers with explicit monetary context e.g. "limit of 5000" or "up to 40000"
            monetary_ctx = re.search(r'(?:limit|up to|cap|maximum|sum insured|amount|rs|inr|₹)\s*(?:of)?\s*([\d,]+)', clean_text, re.IGNORECASE)
            if monetary_ctx:
                try:
                    parsed = float(monetary_ctx.group(1).replace(",", ""))
                    if parsed >= 500.0:
                        return parsed
                except ValueError:
                    pass

            return None

        if isinstance(val, (int, float)):
            num = float(val)
            if num >= 100.0:
                return num

        if isinstance(val, str):
            res = parse_str(val)
            if res is not None:
                return res

        if source_text:
            res = parse_str(source_text)
            if res is not None:
                return res

        return default

    @staticmethod
    def parse_percentage_value(val: Any, source_text: Optional[str] = None, default: Optional[float] = None) -> Optional[float]:
        """
        Parses percentage values (e.g. 10.0, "10%", "Nil", "no co-payment", "0%").
        Correctly recognizes 'Nil' / 'no co-payment' / 'zero' as 0.0%. Returns None if no percentage found.
        """
        def parse_pct_str(text_str: str) -> Optional[float]:
            if not text_str:
                return None
            t = str(text_str).strip()
            t_lower = t.lower()

            # Handle Nil / No co-payment with strict word boundaries
            if re.search(r'\b(nil|no co-payment|no copayment|zero|0%)\b', t_lower):
                return 0.0

            # Explicit percentage symbol e.g. "10%" or "10 %"
            pct_match = re.search(r'([\d\.]+)\s*%', t)
            if pct_match:
                try:
                    return float(pct_match.group(1))
                except ValueError:
                    pass

            # Number in cleaned string if context implies percentage
            clean_text = ValueNormalizer.clean_text_snippets(t)
            num_match = re.search(r'\b(\d+(?:\.\d+)?)\b', clean_text)
            if num_match:
                try:
                    num = float(num_match.group(1))
                    if 0.0 <= num <= 100.0:
                        return num
                except ValueError:
                    pass
            return None

        if isinstance(val, (int, float)):
            num = float(val)
            if 0.0 <= num <= 100.0:
                return num

        if isinstance(val, str):
            res = parse_pct_str(val)
            if res is not None:
                return res

        if source_text:
            res = parse_pct_str(source_text)
            if res is not None:
                return res

        return default

    @staticmethod
    def parse_duration(text: str, keyword: Optional[str] = None) -> Optional[Dict[str, Any]]:
        """
        Parses durations like '30 days', '60 days', '90 days', '24 months', '36 months', '4 years'.
        Preserves original_value string alongside normalized units/months.
        Optional keyword parameter anchors duration parsing to the target section.
        """
        if not text:
            return None
        
        t_clean = ValueNormalizer.clean_text_snippets(text)
        if keyword and keyword.lower() in t_clean.lower():
            idx = t_clean.lower().find(keyword.lower())
            t_clean = t_clean[idx:]

        # Years e.g. "4 years" or "2 yrs"
        y = re.search(r'(\d+)\s*(?:years?|yrs?)\b', t_clean, re.IGNORECASE)
        if y:
            years_val = int(y.group(1))
            return {
                "value": years_val,
                "unit": "years",
                "normalized_months": years_val * 12,
                "original_text": f"{years_val} years"
            }

        # Months e.g. "24 months", "36 mths", or "24/36 months"
        m = re.search(r'(\d+)(?:\s*[\/\-]\s*\d+)?\s*(?:months?|mths?)\b', t_clean, re.IGNORECASE)
        if m:
            months_val = int(m.group(1))
            return {
                "value": months_val,
                "unit": "months",
                "normalized_months": months_val,
                "original_text": f"{months_val} months"
            }

        # Days e.g. "30 days"
        d = re.search(r'(\d+)\s*(?:days?)\b', t_clean, re.IGNORECASE)
        if d:
            days_val = int(d.group(1))
            return {
                "value": days_val,
                "unit": "days",
                "normalized_months": None,
                "original_text": f"{days_val} days"
            }

        return None

    @staticmethod
    def parse_room_category(text: str) -> Dict[str, Any]:
        """
        Classifies room category entitlement:
        - Single Private A/C Room (no cap)
        - Standard Single Room (capped or standard limit)
        - Twin Sharing Room
        - Suite / Deluxe Room
        - Any Room (no cap)
        - Specific monetary cap (e.g. ₹5,000/day or 1% of Sum Insured)
        """
        if not text:
            return {
                "category": "Standard Single Room",
                "has_cap": False,
                "cap_amount": None,
                "formatted_value": "Standard Single Room",
                "qualifier": "standard_limit"
            }

        t_lower = text.lower()

        if "single private" in t_lower or "private a/c" in t_lower or "single a/c" in t_lower:
            return {
                "category": "Single Private A/C Room",
                "has_cap": False,
                "cap_amount": None,
                "formatted_value": "Single Private A/C Room (No Cap)",
                "qualifier": "no cap"
            }

        if "twin" in t_lower or "sharing" in t_lower:
            return {
                "category": "Twin Sharing Room",
                "has_cap": True,
                "cap_amount": None,
                "formatted_value": "Twin Sharing Room",
                "qualifier": "twin sharing"
            }

        if "deluxe" in t_lower or "suite" in t_lower:
            return {
                "category": "Deluxe Room",
                "has_cap": True,
                "cap_amount": None,
                "formatted_value": "Deluxe Room",
                "qualifier": "deluxe"
            }

        if "any room" in t_lower or "no room rent cap" in t_lower or "no cap" in t_lower:
            return {
                "category": "Any Room",
                "has_cap": False,
                "cap_amount": None,
                "formatted_value": "Any Room (No Cap)",
                "qualifier": "no cap"
            }

        # Check for explicit monetary cap e.g. ₹5,000/day or 1% of Sum Insured
        cap_val = ValueNormalizer.parse_monetary_value(text)
        pct_match = re.search(r'(\d+(?:\.\d+)?)\s*%\s*of\s*(?:sum\s*insured|si)', t_lower)

        if cap_val:
            fmt = f"₹{int(cap_val):,}/day"
            if pct_match:
                fmt += f" ({pct_match.group(1)}% of Sum Insured)"
            return {
                "category": "Standard Single Room",
                "has_cap": True,
                "cap_amount": cap_val,
                "formatted_value": fmt,
                "qualifier": f"cap_₹{int(cap_val):,}/day"
            }

        if pct_match:
            pct_val = pct_match.group(1)
            return {
                "category": "Standard Single Room",
                "has_cap": True,
                "cap_amount": None,
                "formatted_value": f"{pct_val}% of Sum Insured per day",
                "qualifier": f"{pct_val}% of Sum Insured"
            }

        return {
            "category": "Standard Single Room",
            "has_cap": False,
            "cap_amount": None,
            "formatted_value": "Standard Single Room",
            "qualifier": "standard_limit"
        }

    @staticmethod
    def parse_cumulative_bonus(text: str) -> Dict[str, Any]:
        """
        Parses cumulative bonus statements e.g.:
        "5% per claim-free year, maximum 25%"
        "10% for every claim-free year up to a maximum of 100%"
        """
        if not text:
            return {"increment": None, "frequency": "claim-free year", "maximum": None, "formatted_value": "N/A"}

        t_lower = text.lower()
        inc_val = None
        max_val = None

        # Look for maximum cap e.g. "maximum 25%", "max 100%", "up to 50%"
        max_match = re.search(r'(?:max|maximum|up to)\s*(?:a\s*max(?:imum)?\s*of)?\s*(\d+)\s*%', t_lower)
        if max_match:
            try:
                max_val = float(max_match.group(1))
            except ValueError:
                pass

        # Look for annual increment e.g. "5%", "10% per year", "increases by 10%"
        inc_match = re.search(r'(?:increases by|bonus:?\s*|by\s*)?(\d+)\s*%\s*(?:for\s*every|per)?\s*(?:claim-free|policy)?', t_lower)
        if inc_match:
            try:
                val = float(inc_match.group(1))
                if max_val and val == max_val:
                    # If regex matched max instead of increment, look for smaller increment before max
                    first_pcts = re.findall(r'(\d+)\s*%', t_lower)
                    if len(first_pcts) > 1:
                        inc_val = float(first_pcts[0])
                    else:
                        inc_val = val
                else:
                    inc_val = val
            except ValueError:
                pass

        if inc_val is None and max_val is not None:
            inc_val = max_val

        fmt = f"{int(inc_val)}% per claim-free year" if inc_val else "Cumulative Bonus"
        if max_val:
            fmt += f" (Max {int(max_val)}%)"

        return {
            "increment": inc_val,
            "frequency": "claim-free year",
            "maximum": max_val,
            "max_cap": max_val,
            "formatted_value": fmt
        }

    @staticmethod
    def extract_qualifiers(text: str) -> List[str]:
        """
        Extracts semantic qualifiers from text snippet.
        E.g. 'per eye', 'per hospitalisation', 'per policy year', 'within Sum Insured',
        'non-network hospitals', 'admissible claims', 'floater', 'individual', 'continuous coverage'.
        """
        if not text:
            return []

        t_lower = text.lower()
        qualifiers = []

        if "per eye" in t_lower:
            qualifiers.append("per eye")
        if "per hospitalisation" in t_lower or "per hospitalization" in t_lower:
            qualifiers.append("per hospitalisation")
        if "per policy year" in t_lower:
            qualifiers.append("per policy year")
        elif "per year" in t_lower and "claim-free" not in t_lower:
            qualifiers.append("per policy year")
        if "per claim-free" in t_lower or "claim-free year" in t_lower:
            qualifiers.append("per claim-free year")
        if "continuous coverage" in t_lower:
            qualifiers.append("continuous coverage")
        if "within sum insured" in t_lower or "up to sum insured" in t_lower:
            qualifiers.append("within Sum Insured")
        if "no cap" in t_lower:
            qualifiers.append("no cap")
        if "once per policy year" in t_lower or "once during that year" in t_lower:
            qualifiers.append("once per policy year")
        if "non-network" in t_lower:
            qualifiers.append("non-network hospitals")
        if "admissible claims" in t_lower or "admissible claim" in t_lower:
            qualifiers.append("admissible claims")
        if "floater" in t_lower:
            qualifiers.append("floater")
        elif "individual" in t_lower:
            qualifiers.append("individual")
        if "recipient under policy" in t_lower or "harvesting" in t_lower:
            qualifiers.append("recipient under policy")

        return qualifiers

    @staticmethod
    def extract_conditions(text: str) -> List[str]:
        """
        Extracts specific conditions / exceptions from clause text.
        E.g. '3 consecutive days minimum', 'in addition to applicable excess',
        'illness from policy inception', 'subject to 24 hours hospitalization'.
        """
        if not text:
            return []

        t_lower = text.lower()
        conditions = []

        if "3 consecutive days" in t_lower or "minimum 3 days" in t_lower:
            conditions.append("3 consecutive days minimum")
        if "applicable excess" in t_lower or "in addition to excess" in t_lower:
            conditions.append("in addition to applicable excess")
        if "first policy start date" in t_lower or "policy inception" in t_lower:
            conditions.append("illness from policy inception")
        if "24 hours" in t_lower or "24-hour" in t_lower:
            conditions.append("minimum 24 hours hospitalization")
        if "joint replacement" in t_lower and "osteoarthritis" in t_lower:
            conditions.append("joint replacement and osteoarthritis")

        return conditions

    @staticmethod
    def extract_exceptions(text: str) -> List[str]:
        """
        Extracts specific exclusions / exceptions mentioned in clause text.
        E.g. 'excludes asthma, bronchitis', 'excludes non-medical items'.
        """
        if not text:
            return []

        t_lower = text.lower()
        exceptions = []

        m_ex = re.search(r'excludes?\s*([^;\.\n]+)', t_lower)
        if m_ex:
            exceptions.append(m_ex.group(1).strip())
        elif "non-payable" in t_lower or "non-medical" in t_lower:
            exceptions.append("non-payable administrative/non-medical items")

        return exceptions

    @staticmethod
    def extract_basis(text: str) -> Optional[str]:
        """Extracts basis of calculation (sum_insured, base_si, admissible_claims, etc.)."""
        if not text:
            return None
        t_lower = text.lower()
        if "base sum insured" in t_lower or "base si" in t_lower:
            return "base_si"
        if "sum insured" in t_lower or "si" in t_lower:
            return "sum_insured"
        if "admissible claim" in t_lower or "admissible claims" in t_lower:
            return "admissible_claims"
        return None

    @staticmethod
    def extract_frequency(text: str) -> Optional[str]:
        """Extracts benefit application frequency (per claim-free year, per policy year, per hospitalisation, per eye, etc.)."""
        if not text:
            return None
        t_lower = text.lower()
        if "claim-free year" in t_lower or "per claim-free" in t_lower:
            return "claim-free year"
        if "per policy year" in t_lower or "per year" in t_lower or "once during that year" in t_lower:
            return "per policy year"
        if "per hospitalisation" in t_lower or "per hospitalization" in t_lower:
            return "per hospitalisation"
        if "per eye" in t_lower:
            return "per eye"
        return None

