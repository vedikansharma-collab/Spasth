import re
import logging
from typing import List, Dict, Any, Optional

from app.rag.embeddings import PolicyEmbeddingGenerator
from app.rag.vector_store import PolicyVectorStore

logger = logging.getLogger(__name__)

class PolicyHybridRetriever:
    """
    RAG Hybrid Retriever — Combines Structured Rule Matching, Keyword Matching, and Vector Similarity.
    
    Ranking Priority:
    1. Exact Structured Rule Match (Canonical Policy JSON)
    2. Strong Semantic Match (Vector Embedding Cosine Similarity)
    3. Strong Keyword Match
    4. Generic Document Similarity
    
    Filters & Thresholds:
    - Page 1 disclaimers are strictly filtered out for intent queries.
    - Low relevance evidence below threshold is rejected.
    """

    IRRELEVANT_DISCLAIMER_PATTERNS = [
        r"not a real insurance contract",
        r"sample policy",
        r"for illustration only",
        r"for demonstration",
        r"must not be used to buy, claim or compare",
        r"disclaimer:",
        r"terms and conditions apply",
        r"sample document for testing",
        r"this is a sample"
    ]

    GENERIC_STOP_WORDS = {
        "what", "when", "does", "have", "with", "from", "about", "your", "this",
        "policy", "cover", "covered", "coverage", "limit", "period", "show", "tell",
        "under", "much", "many", "rate", "cost", "type", "rule", "item", "part",
        "claim", "claims", "contract", "contracts", "insurance", "document", "documents",
        "page", "pages", "myself", "any", "how", "do", "i", "to", "pay", "of", "my",
        "the", "a", "an", "is", "are", "there", "disclaimer", "disclaimers", "terms",
        "conditions", "apply", "sample", "illustration", "expenses", "expense",
        "surgery", "treatment", "hospital", "medical", "disease", "care", "service", "procedure", "charges"
    }

    @classmethod
    def is_disclaimer(cls, text: str, page_num: int = 1) -> bool:
        """Returns True if text snippet is generic disclaimer text."""
        t_lower = text.lower()
        if any(re.search(pat, t_lower) for pat in cls.IRRELEVANT_DISCLAIMER_PATTERNS):
            return True
        if page_num == 1 and any(w in t_lower for w in ["not a real insurance", "sample document", "disclaimer"]):
            return True
        return False

    @classmethod
    def retrieve(
        cls,
        policy_id: str,
        query: str,
        canonical_json: Dict[str, Any],
        query_intents: List[str]
    ) -> Dict[str, Any]:
        """
        Executes hybrid retrieval over canonical rules, page chunks, and vector store embeddings.
        Returns top relevant rules and vector chunks with re-ranking scores.
        """
        q_lower = query.lower().strip()
        rules = canonical_json.get("rules", [])
        if not rules:
            all_rules = []
            for g in ["coverage_rules", "waiting_periods", "exclusions", "benefits", "restore_benefits", "bonuses"]:
                all_rules.extend(canonical_json.get(g, []))
            rules = all_rules

        # 1. Structured Canonical Rule Matching
        scored_rules = []
        rejected_rules = []

        for rule in rules:
            score = 0.0
            r_id = (rule.get("rule_id") or rule.get("rule_key") or "").lower()
            name = (rule.get("name") or rule.get("label") or "").lower()
            cat = (rule.get("category") or rule.get("rule_type") or "").lower()
            src = (rule.get("source_text") or "").lower()
            quals = str(rule.get("qualifiers") or "").lower()
            conds = str(rule.get("conditions") or "").lower()

            # A. Intent-Based Match (+0.75 score boost)
            for intent in query_intents:
                if intent == "copay" and any(k in r_id or k in cat or k in name or k in src for k in ["copay", "co_payment", "co-payment", "copayment", "co pay", "cost_sharing", "cost sharing", "deductible"]):
                    score += 0.75
                elif intent == "sum_insured" and any(k in r_id or k in cat or k in name or k in src for k in ["sum_insured", "sum insured", "coverage_limit", "maximum_benefit"]):
                    score += 0.75
                elif intent == "cataract" and "cataract" in (r_id + cat + name + src + quals):
                    score += 0.70
                elif intent == "waiting_period" and any(k in r_id or k in cat or k in name or k in src for k in ["waiting", "ped", "pre-existing"]):
                    score += 0.70
                elif intent in ["sublimits", "deductible", "exclusions", "room_rent", "eligibility", "reimbursement", "network_hospital", "disease_waiting_period"]:
                    if any(k in r_id or k in cat or k in name or k in src for k in [intent, intent.replace("_", " "), intent.replace("_", "")]):
                        score += 0.70
                elif intent != "coverage" and (intent in r_id or intent in cat or intent in name):
                    score += 0.65
                elif any(kw in src or kw in quals for kw in [intent]):
                    score += 0.45

            # B. Specific Term Overlap (+0.15 to +0.25)
            q_words = [w for w in q_lower.split() if len(w) > 2 and w not in cls.GENERIC_STOP_WORDS]
            for qw in q_words:
                if qw in r_id or qw in name:
                    score += 0.25
                elif qw in cat:
                    score += 0.20
                elif qw in src or qw in quals or qw in conds:
                    score += 0.15

            if score >= 0.35:
                scored_rules.append((score, rule))
            else:
                rejected_rules.append((rule.get("name") or r_id, f"Below threshold 0.35 (score={score:.2f})"))

        scored_rules.sort(key=lambda x: x[0], reverse=True)
        matched_rules = [r for score, r in scored_rules[:5]]

        # 2. Vector Semantic Similarity Search (Scoped to policy_id)
        query_emb = PolicyEmbeddingGenerator.generate_embedding(query)
        vector_chunks = PolicyVectorStore.search_similar_chunks(policy_id, query_emb, top_k=5)
        
        # Filter vector chunks for disclaimers and relevance threshold
        filtered_vector_chunks = []
        for v_chunk in vector_chunks:
            if cls.is_disclaimer(v_chunk.get("text", ""), v_chunk.get("source_page", 1)):
                rejected_rules.append((v_chunk.get("chunk_id", "chunk"), "Filtered out as disclaimer pattern"))
                continue
            if v_chunk.get("score", 0.0) >= 0.35:
                filtered_vector_chunks.append(v_chunk)

        return {
            "query": query,
            "matched_rules": matched_rules,
            "scored_rules": [(sc, r.get("rule_id") or r.get("name")) for sc, r in scored_rules[:5]],
            "vector_chunks": filtered_vector_chunks,
            "rejected_rules": rejected_rules
        }
