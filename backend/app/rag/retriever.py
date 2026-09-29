from typing import List, Dict, Any
import re

class PolicyRetriever:
    """
    RAG & Clause Retriever for searching preserved policy page chunks.
    Maintains page numbers, clauses, and source text for citations.
    """

    KEYWORDS = {
        "sum_insured": ["sum insured", "coverage limit", "policy schedule", "maximum benefit", "insured amount"],
        "copay": ["co-payment", "co-pay", "copay", "mandatory co-payment", "insured contribution"],
        "room_rent": ["room rent", "room limit", "room category", "icu charges", "daily room", "proportionate"],
        "sub_limit": ["sub-limit", "sub limit", "cataract", "appendectomy", "procedure cap", "capped at"],
        "waiting_period": ["waiting period", "initial waiting", "pre-existing", "months waiting"],
        "exclusions": ["exclusion", "exclusions", "not covered", "shall not be liable", "excluded"]
    }

    @staticmethod
    def retrieve_relevant_chunks(pages: List[Dict[str, Any]], rule_type: str = None) -> List[Dict[str, Any]]:
        """
        Retrieves pages containing relevant keywords with exact page number tracking.
        """
        if not pages:
            return []

        if not rule_type or rule_type not in PolicyRetriever.KEYWORDS:
            # Return all pages if no specific filter
            return pages

        target_keywords = PolicyRetriever.KEYWORDS[rule_type]
        relevant_pages = []

        for page in pages:
            text_lower = page["content"].lower()
            if any(kw in text_lower for kw in target_keywords):
                relevant_pages.append(page)

        # Fallback to all pages if keyword search produced empty set
        return relevant_pages if relevant_pages else pages
