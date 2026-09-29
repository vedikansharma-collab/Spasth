import re
import logging
from typing import Optional, Any

logger = logging.getLogger(__name__)

class ValueNormalizer:
    """
    Normalizes raw extracted policy rule values (strings, numbers, formatted text)
    into deterministic numerical types (float for monetary amounts & percentages).
    Prevents clause numbers (e.g. '2.3', '1.1') or unformatted currency strings from corrupting calculations.
    """

    @staticmethod
    def parse_monetary_value(val: Any, source_text: Optional[str] = None, default: Optional[float] = None) -> Optional[float]:
        """
        Parses a monetary value in INR.
        Handles floats/ints, currency strings ('INR 90,000', 'Rs 5 Lakh', '5,00,000').
        Filters out clause numbers (< 100 unless explicitly marked with INR/Rs/₹).
        If val is numeric < 100 (a clause number), falls back to parsing source_text.
        """
        # Helper to parse text string
        def parse_str(text_str: str) -> Optional[float]:
            if not text_str:
                return None
            t = str(text_str).strip()
            if not t:
                return None
            # Strip clause numbering at start (e.g. "2.3 ", "1.1 ", "Clause 2.1 ")
            clean_text = re.sub(r'^\s*(?:clause|section)?\s*\d+(?:\.\d+)*\s*[:\.\-]?\s*', '', t, flags=re.IGNORECASE)

            # Handle Lakhs / Crores
            lakh_match = re.search(r'([\d\.]+)\s*(lakh|lakhs|lac|lacs)', clean_text, re.IGNORECASE)
            if lakh_match:
                try:
                    return float(lakh_match.group(1)) * 100000.0
                except ValueError:
                    pass

            crore_match = re.search(r'([\d\.]+)\s*(crore|crores|cr)', clean_text, re.IGNORECASE)
            if crore_match:
                try:
                    return float(crore_match.group(1)) * 10000000.0
                except ValueError:
                    pass

            # Look for explicit INR / Rs / ₹ amount or comma-separated numbers
            inr_match = re.search(r'(?:inr|rs\.?|₹)\s*([\d,]+(?:\.\d+)?)', clean_text, re.IGNORECASE)
            if inr_match:
                try:
                    parsed = float(inr_match.group(1).replace(",", ""))
                    if parsed >= 100.0:
                        return parsed
                except ValueError:
                    pass

            # Search for any number in the clean_text >= 100 (to avoid clause numbers)
            num_matches = re.findall(r'[\d,]+(?:\.\d+)?', clean_text)
            for num_str in num_matches:
                try:
                    parsed = float(num_str.replace(",", ""))
                    if parsed >= 100.0:
                        return parsed
                except ValueError:
                    continue
            return None

        # 1. If val is numeric float/int >= 100, return it directly
        if isinstance(val, (int, float)):
            num = float(val)
            if num >= 100.0:
                return num
            # If num < 100.0 (e.g., clause number 2.0 or 2.3), do NOT use it. Check source_text below.

        # 2. If val is a string, try parsing it
        if isinstance(val, str):
            res = parse_str(val)
            if res is not None:
                return res

        # 3. Fall back to parsing source_text if provided
        if source_text:
            res = parse_str(source_text)
            if res is not None:
                return res

        return default

    @staticmethod
    def parse_percentage_value(val: Any, source_text: Optional[str] = None, default: float = 0.0) -> float:
        """
        Parses percentage values (e.g. 10.0, "10%", "10.0%", "0.1").
        Returns float between 0.0 and 100.0.
        """
        def parse_pct_str(text_str: str) -> Optional[float]:
            if not text_str:
                return None
            t = str(text_str).strip()
            # Look for explicit percentage symbol first
            pct_match = re.search(r'([\d\.]+)\s*%', t)
            if pct_match:
                try:
                    return float(pct_match.group(1))
                except ValueError:
                    pass

            # Remove clause numbering at start
            clean_text = re.sub(r'^\s*(?:clause|section)?\s*\d+(?:\.\d+)*\s*[:\.\-]?\s*', '', t, flags=re.IGNORECASE)
            num_match = re.search(r'[\d\.]+', clean_text)
            if num_match:
                try:
                    num = float(num_match.group(0))
                    if 0.0 < num < 1.0:
                        return num * 100.0
                    if 0.0 <= num <= 100.0:
                        return num
                except ValueError:
                    pass
            return None

        if isinstance(val, (int, float)):
            num = float(val)
            if 0.0 < num < 1.0:
                return num * 100.0
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
