import re
import logging
from typing import List, Dict, Any, Optional, Tuple
from app.core.config import settings

logger = logging.getLogger("spasth.policy_assistant")
logger.setLevel(logging.DEBUG)

class PolicyAssistantEngine:
    """
    Spasth Policy Assistant RAG Engine — Enhanced Intent & Grounding Layer.
    
    Principles:
    1. Grounded strictly on canonical Policy JSON and preserved source text chunks.
    2. Policy Isolation: Operations scoped exclusively to current policy_id.
    3. Concept & Intent Normalization: Maps natural-language variations (e.g., "pay any percentage",
       "cost sharing", "out of pocket") to canonical rule categories (co-payment, sum insured, etc.).
    4. Structured Rule Priority: Ranks canonical Policy JSON rules over raw text page snippets.
    5. Irrelevance Filtering & Thresholding: Rejects weak evidence, generic disclaimers, and ungrounded queries.
    6. Semantic Relationship Preservation (Cumulative Bonus, Dual Limits, Conditions).
    7. Zero Financial Payout Calculation (Math Engine handles calculation).
    """

    INTENT_MAP = {
        "copay": [
            "co-payment", "copay", "co pay", "co-pay", "deductible", "cost sharing", 
            "mandatory co-payment", "claim contribution", "pay percentage", "pay myself",
            "pay out of pocket", "percentage of my claim", "share claim", "my share",
            "patient share", "insured share", "contribution", "pay any percentage",
            "percentage do i have to pay", "how much of the claim do i pay", "pay any percentage of my claim"
        ],
        "sum_insured": [
            "sum insured", "maximum benefit", "coverage limit", "policy limit", 
            "insured amount", "total coverage", "how much coverage", "overall limit",
            "policy amount", "total limit", "maximum cover", "how much cover", "coverage do i have"
        ],
        "room_rent": [
            "room rent", "room category", "room limit", "icu", "icu charges", 
            "daily room", "proportionate", "deluxe", "suite", "single private",
            "room charge", "bed charge", "hospital room", "rent limit"
        ],
        "cataract": [
            "cataract", "cataract surgery", "eye surgery", "lens replacement", "cataract limit"
        ],
        "ambulance": [
            "ambulance", "road ambulance", "emergency transport"
        ],
        "cumulative_bonus": [
            "cumulative bonus", "no claim bonus", "ncb", "bonus", "claim-free year", "no claims"
        ],
        "waiting_period": [
            "waiting period", "initial waiting", "ped", "pre-existing", "months waiting", 
            "years waiting", "specific disease waiting", "waiting time"
        ],
        "exclusions": [
            "exclusion", "exclusions", "not covered", "shall not be liable", "excluded", 
            "uncovered", "not payable", "what is not paid"
        ],
        "pre_hospitalisation": [
            "pre-hospitalisation", "pre hospitalisation", "pre-hospital", "before admission",
            "prior to hospital", "days before hospitalization", "before hospitalization"
        ],
        "post_hospitalisation": [
            "post-hospitalisation", "post hospitalisation", "post-hospital", "after discharge",
            "expenses after hospitalization", "after hospitalization"
        ],
        "restore": [
            "restore", "reinstatement", "refill", "automatic restoration", "restore benefit"
        ],
        "domiciliary": [
            "domiciliary", "home treatment"
        ],
        "modern_treatment": [
            "modern treatment", "robotic", "stem cell"
        ],
        "organ_donor": [
            "organ donor", "donor expenses"
        ],
        "knee": [
            "knee", "knee replacement", "arthroplasty", "joint replacement"
        ],
        "maternity": [
            "maternity", "c-section", "delivery", "newborn"
        ],
        "ayush": [
            "ayush", "ayurveda", "unani", "siddha", "homeopathy"
        ],
        "daycare": [
            "daycare", "day care", "24 hours"
        ],
        "policy_metadata": [
            "policy number", "policy period", "policy holder", "insured name", "expiry", 
            "start date", "zone", "product name"
        ]
    }

    IRRELEVANT_DISCLAIMER_PATTERNS = [
        r"not a real insurance contract",
        r"sample policy",
        r"for illustration only",
        r"for demonstration",
        r"must not be used to buy, claim or compare",
        r"disclaimer:",
        r"terms and conditions apply"
    ]

    GENERIC_STOP_WORDS = {
        "what", "when", "does", "have", "with", "from", "about", "your", "this",
        "policy", "cover", "covered", "coverage", "limit", "period", "show", "tell",
        "under", "much", "many", "rate", "cost", "type", "rule", "item", "part",
        "claim", "contract", "insurance", "document", "page", "myself", "any", "how",
        "do", "i", "to", "pay", "of", "my", "the", "a", "an", "is", "are", "there"
    }

    @classmethod
    def resolve_followup_query(cls, query: str, history: Optional[List[Dict[str, Any]]]) -> Tuple[str, Optional[str]]:
        """
        Resolves query intent using conversation history if query is an ambiguous follow-up.
        """
        query_lower = query.lower().strip()
        if not history:
            return query, None

        is_ambiguous = any(phrase in query_lower for phrase in [
            "what is the waiting period", "what about waiting period", "is it covered",
            "what is the limit", "what is the sublimit", "how much", "what is the cap",
            "is there a cap", "how many days", "how many months", "what about this"
        ]) or len(query_lower.split()) <= 4

        if not is_ambiguous:
            return query, None

        last_user_query = ""
        for msg in reversed(history):
            if msg.get("sender") == "user" or msg.get("role") == "user":
                last_user_query = msg.get("text") or msg.get("content") or ""
                break

        if not last_user_query:
            return query, None

        last_lower = last_user_query.lower()
        subject = None
        for key in ["knee replacement", "knee", "cataract", "ambulance", "ayush", "maternity", "c-section", "hernia", "angioplasty", "ped", "diabetes", "hypertension"]:
            if key in last_lower:
                subject = key
                break

        if subject:
            resolved_query = f"{query} for {subject}"
            return resolved_query, subject

        return query, None

    @classmethod
    def normalize_query_intents(cls, query: str) -> List[str]:
        """
        Identifies conceptual intents from natural language query.
        Combines exact phrase matching with semantic keyword combinations.
        """
        q_lower = query.lower().strip()
        matched_intents = set()
        
        # 1. Exact phrase matching from INTENT_MAP
        for intent, phrases in cls.INTENT_MAP.items():
            for phrase in phrases:
                if re.search(r'\b' + re.escape(phrase) + r'\b', q_lower) or phrase in q_lower:
                    matched_intents.add(intent)
                    break

        # 2. Dynamic combination rules
        # Co-payment / Cost-sharing combinations:
        if any(w in q_lower for w in ["pay", "paid", "paying", "contribution", "share"]):
            if any(w in q_lower for w in ["percentage", "claim", "myself", "out of pocket", "how much", "amount", "cost"]):
                matched_intents.add("copay")

        # Sum Insured combinations:
        if any(w in q_lower for w in ["coverage", "cover", "insured"]):
            if any(w in q_lower for w in ["how much", "total", "overall", "maximum", "amount"]):
                matched_intents.add("sum_insured")

        # Pre/Post hospitalisation combinations:
        if "hospitalization" in q_lower or "hospitalisation" in q_lower or "hospital" in q_lower:
            if any(w in q_lower for w in ["before", "prior", "days before"]):
                matched_intents.add("pre_hospitalisation")
            if any(w in q_lower for w in ["after", "discharge", "following"]):
                matched_intents.add("post_hospitalisation")

        return list(matched_intents)

    @classmethod
    def is_disclaimer_snippet(cls, text: str) -> bool:
        """
        Checks if text is a generic header/disclaimer snippet to prevent irrelevant retrieval.
        """
        t_lower = text.lower()
        return any(re.search(pat, t_lower) for pat in cls.IRRELEVANT_DISCLAIMER_PATTERNS)

    @classmethod
    def retrieve_relevant_rules(
        cls,
        canonical_json: Dict[str, Any],
        query: str,
        history: Optional[List[Dict[str, Any]]] = None
    ) -> Dict[str, Any]:
        """
        Searches canonical Policy JSON rules and pages for query-relevant rules.
        Implements concept mapping, structured rule priority, and strict relevance thresholding.
        """
        effective_query, resolved_subject = cls.resolve_followup_query(query, history)
        q_lower = effective_query.lower().strip()
        query_intents = cls.normalize_query_intents(effective_query)

        metadata = canonical_json.get("policy_metadata", {})
        rules = canonical_json.get("rules", [])
        
        # Flatten grouped rules if present
        if not rules:
            all_rules = []
            for group in ["coverage_rules", "waiting_periods", "exclusions", "benefits", "restore_benefits", "bonuses"]:
                all_rules.extend(canonical_json.get(group, []))
            rules = all_rules

        pages = canonical_json.get("pages", [])

        matched_rules = []
        matched_metadata = {}
        matched_snippets = []
        rejected_rules = []

        logger.debug("--- SPASTH POLICY ASSISTANT RETRIEVAL DEBUG LOG ---")
        logger.debug("QUESTION: %s", query)
        logger.debug("EFFECTIVE QUERY: %s", effective_query)
        logger.debug("NORMALIZED INTENTS: %s", query_intents)

        # 1. Match Policy Metadata queries
        for meta_key, meta_val in metadata.items():
            if meta_val and meta_key.replace("_", " ") in q_lower:
                matched_metadata[meta_key] = meta_val

        # 2. Rule keyword & semantic matching over structured Canonical Policy JSON
        scored_rules = []
        for rule in rules:
            score = 0
            rule_id = (rule.get("rule_id") or rule.get("rule_key") or "").lower()
            name = (rule.get("name") or rule.get("label") or "").lower()
            category = (rule.get("category") or rule.get("rule_type") or "").lower()
            source_text = (rule.get("source_text") or "").lower()
            qualifiers = str(rule.get("qualifiers") or "").lower()
            conditions = str(rule.get("conditions") or "").lower()

            # A. Intent-based Concept Matching (+60 points)
            for intent in query_intents:
                if intent == "copay" and ("copay" in rule_id or "copay" in category or "co-payment" in name or "co_payment" in rule_id or "copay" in name):
                    score += 65
                elif intent in rule_id or intent in category or intent in name:
                    score += 60
                elif any(kw in source_text or kw in qualifiers for kw in cls.INTENT_MAP.get(intent, [])):
                    score += 40

            # B. Specific Query Terms Matching (+15 to +25 points)
            query_words = [w for w in q_lower.split() if len(w) > 2 and w not in cls.GENERIC_STOP_WORDS]
            for qw in query_words:
                if qw in rule_id or qw in name:
                    score += 25
                elif qw in category:
                    score += 20
                elif qw in source_text:
                    score += 15
                elif qw in qualifiers or qw in conditions:
                    score += 15

            if score >= 25:
                scored_rules.append((score, rule))
            else:
                rejected_rules.append((score, rule.get("name") or rule.get("rule_id"), "Below relevance threshold 25"))

        # Sort rules by score descending
        scored_rules.sort(key=lambda x: x[0], reverse=True)
        matched_rules = [r for score, r in scored_rules[:5]]

        for sc, r in scored_rules[:5]:
            logger.debug("RETRIEVED RULE: %s (Score: %d, Page: %s)", r.get("name"), sc, r.get("page"))

        # 3. Fallback page snippet matching (Strict threshold + disclaimer filter)
        if not matched_rules and not matched_metadata and pages:
            search_words = [w for w in q_lower.split() if len(w) > 3 and w not in cls.GENERIC_STOP_WORDS]
            if search_words:
                for page in pages:
                    content = page.get("content", "")
                    for line in content.split("\n"):
                        line_clean = line.strip()
                        if len(line_clean) > 15:
                            # Reject disclaimers
                            if cls.is_disclaimer_snippet(line_clean):
                                rejected_rules.append((0, line_clean, "Filtered out as disclaimer pattern"))
                                continue
                            
                            # Score line snippet
                            snip_score = sum(30 for w in search_words if re.search(r'\b' + re.escape(w) + r'\b', line_clean.lower()))
                            if snip_score >= 50:
                                matched_snippets.append({
                                    "page": page.get("page_number", 1),
                                    "clause": "Policy Document Text",
                                    "source_text": line_clean,
                                    "score": snip_score
                                })
                                if len(matched_snippets) >= 3:
                                    break
                    if len(matched_snippets) >= 3:
                        break

        logger.debug("REJECTED RESULTS COUNT: %d", len(rejected_rules))

        return {
            "query": query,
            "effective_query": effective_query,
            "resolved_subject": resolved_subject,
            "matched_rules": matched_rules,
            "matched_metadata": matched_metadata,
            "matched_snippets": matched_snippets,
            "rejected_rules": rejected_rules,
            "metadata": metadata
        }

    @classmethod
    def generate_grounded_answer(
        cls,
        policy_id: str,
        query: str,
        retrieval_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Generates grounded answer using LLM (if available) or deterministic fallback.
        """
        matched_rules = retrieval_data["matched_rules"]
        matched_metadata = retrieval_data["matched_metadata"]
        matched_snippets = retrieval_data["matched_snippets"]
        effective_query = retrieval_data["effective_query"]
        metadata = retrieval_data["metadata"]

        conflict_rules = [r for r in matched_rules if r.get("status") == "CONFLICT"]

        # Try Gemini LLM if API Key is configured
        if settings.GEMINI_API_KEY and settings.GEMINI_API_KEY != "mock_key_for_development":
            try:
                import google.generativeai as genai
                genai.configure(api_key=settings.GEMINI_API_KEY)
                model = genai.GenerativeModel("gemini-1.5-flash")

                rules_context = []
                for r in matched_rules:
                    rules_context.append(
                        f"Rule ID: {r.get('rule_id') or r.get('name')}\n"
                        f"Name: {r.get('name')}\n"
                        f"Category: {r.get('category')}\n"
                        f"Value: {r.get('formatted_value') or r.get('value')}\n"
                        f"Values Structure: {r.get('values')}\n"
                        f"Limits: {r.get('limits')}\n"
                        f"Conditions: {r.get('conditions')}\n"
                        f"Qualifiers: {r.get('qualifiers')}\n"
                        f"Page: {r.get('page')}\n"
                        f"Clause: {r.get('clause')}\n"
                        f"Source Text: {r.get('source_text')}\n"
                        f"Status: {r.get('status')}\n"
                    )

                prompt = f"""
You are the SPASTH Policy Assistant.
Answer the user query grounded STRICTLY on the retrieved policy rules evidence provided below.

RULES & METADATA EVIDENCE:
Policy Metadata: {metadata}
Retrieved Rules:
{"---".join(rules_context) if rules_context else "None"}
Retrieved Snippets: {matched_snippets}

USER QUERY: {query} (Effective Context Query: {effective_query})

STRICT INSTRUCTIONS:
1. Answer ONLY using the provided evidence. Do NOT use outside insurance knowledge.
2. DO NOT perform financial payout or final bill calculations.
3. Preserve all semantic relationships (e.g. cumulative bonus increment vs max cap, sublimit caps vs SI percentage, copay conditions).
4. If status is CONFLICT, explicitly state that conflicting values exist in the policy.
5. If status is NEEDS_REVIEW, mention that the rule requires manual verification.
6. If evidence is missing or not found, explicitly state that information is NOT AVAILABLE in the uploaded policy.
7. Always provide structured JSON with keys:
   - "answer": string
   - "citations": list of objects (page, clause, rule, source_text, bbox)
   - "confidence": float between 0.0 and 1.0
   - "grounding_status": "GROUNDED" | "NOT_FOUND" | "NEEDS_REVIEW" | "CONFLICT"
   - "rules_used": list of rule names/IDs
   - "missing_information": list of missing fields if any
"""
                response = model.generate_content(prompt)
                resp_text = response.text.strip()
                if resp_text.startswith("```json"):
                    resp_text = resp_text[7:]
                if resp_text.endswith("```"):
                    resp_text = resp_text[:-3]

                import json
                parsed = json.loads(resp_text.strip())
                return {
                    "policy_id": policy_id,
                    "query": query,
                    "answer": parsed.get("answer", "Answer unavailable."),
                    "citations": parsed.get("citations", []),
                    "confidence": float(parsed.get("confidence", 0.95)),
                    "grounding_status": parsed.get("grounding_status", "GROUNDED"),
                    "rules_used": parsed.get("rules_used", []),
                    "missing_information": parsed.get("missing_information", [])
                }
            except Exception:
                pass  # Fall through to deterministic engine on Gemini error or API limit

        # -------------------------------------------------------------
        # Deterministic Grounded RAG Response Generator
        # -------------------------------------------------------------
        citations = []
        rules_used = []
        missing_information = []
        answer = ""
        grounding_status = "GROUNDED"
        confidence = 0.95

        # Handle CONFLICT status
        if conflict_rules:
            grounding_status = "CONFLICT"
            confidence = 0.60
            c_rule = conflict_rules[0]
            rules_used.append(c_rule.get("name") or c_rule.get("rule_id"))
            add_srcs = c_rule.get("additional_sources", [])
            
            src_desc = [f"Page {c_rule.get('page')}: \"{c_rule.get('source_text')}\""]
            for a in add_srcs:
                src_desc.append(f"Page {a.get('page')}: \"{a.get('source_text')}\"")
                
            answer = (
                f"Conflict Detected in Policy: The uploaded policy document contains conflicting information for '{c_rule.get('name') or 'this rule'}'. "
                f"Discrepancy found between " + " AND ".join(src_desc) + ". Please review the source pages to verify."
            )
            citations.append({
                "page": c_rule.get("page", 1),
                "clause": c_rule.get("clause", "N/A"),
                "rule": c_rule.get("name", "Conflicting Rule"),
                "source_text": c_rule.get("source_text", ""),
                "bbox": c_rule.get("bbox")
            })

        # Handle matched rules
        elif matched_rules:
            parts = []
            for r in matched_rules:
                r_name = r.get("name") or r.get("rule_id") or "Policy Rule"
                rules_used.append(r_name)
                page = r.get("page", 1)
                clause = r.get("clause", "Policy Schedule")
                src = r.get("source_text") or ""
                bbox = r.get("bbox")

                # Handle Co-Payment Rule specifically
                elif any(k in (r.get("rule_id") or "").lower() or k in (r.get("rule_key") or "").lower() or k in r_name.lower() or k in (r.get("category") or "").lower() for k in ["copay", "co_payment", "co-payment", "copayment"]):
                    val = r.get("value", 0.0)
                    fmt = r.get("formatted_value") or (f"{int(val)}%" if val > 0 else "0% (Nil)")
                    raw_quals = r.get('qualifiers')
                    quals_str = ", ".join(raw_quals) if isinstance(raw_quals, list) else str(raw_quals) if raw_quals else ""
                    quals = f" ({quals_str})" if quals_str else ""
                    if val == 0.0 or "nil" in fmt.lower() or "0%" in fmt:
                        parts.append(f"Under your policy ({clause}, Page {page}), the mandatory co-payment is {fmt}{quals}. There is no cost-sharing co-payment deduction required on admissible claims, and eligible hospitalisation expenses are payable up to the Sum Insured.")
                    else:
                        parts.append(f"Under your policy ({clause}, Page {page}), a mandatory co-payment of {fmt}{quals} applies to admissible claims. The policyholder is responsible for paying this percentage out of pocket.")

                # Handle NEEDS_REVIEW
                elif r.get("status") == "NEEDS_REVIEW":
                    grounding_status = "NEEDS_REVIEW"
                    confidence = 0.70
                    parts.append(f"[{r_name}] (Needs Review): {r.get('formatted_value') or r.get('value')} ({clause}, Page {page}). Source text: \"{src}\"")
                
                # Handle Cumulative Bonus
                elif "bonus" in r_name.lower() or "cumulative" in r_name.lower():
                    vals = r.get("values", {})
                    inc = vals.get("increment", {}).get("value") or r.get("value")
                    max_cap = vals.get("maximum", {}).get("value")
                    freq = r.get("frequency") or "claim-free year"

                    if max_cap:
                        desc = f"The cumulative bonus increases coverage by {inc}% for each {freq}, up to a maximum of {max_cap}% of the Sum Insured"
                    else:
                        desc = f"The cumulative bonus increases coverage by {inc}% for each {freq}"
                    parts.append(f"{desc} ({clause}, Page {page}).")

                # Handle Dual Limits / Capped rules
                elif r.get("limits") and len(r.get("limits")) > 0:
                    lim_strs = []
                    for lim in r.get("limits"):
                        val_str = f"{lim.get('value')}%" if lim.get("unit") == "percent" else f"₹{lim.get('value'):,}"
                        lim_strs.append(f"{val_str} ({lim.get('basis', 'limit')})")
                    desc = f"{r_name} is subject to limits: " + ", ".join(lim_strs)
                    parts.append(f"{desc} ({clause}, Page {page}).")

                # General Rule
                else:
                    val_str = r.get("formatted_value") or (f"₹{int(r['value']):,}" if isinstance(r.get("value"), (int, float)) else str(r.get("value")))
                    quals = f" ({r.get('qualifiers')})" if r.get("qualifiers") else ""
                    conds = f" [Condition: {r.get('conditions')}]" if r.get("conditions") else ""
                    parts.append(f"{r_name} is {val_str}{quals}{conds} ({clause}, Page {page}).")

                citations.append({
                    "page": page,
                    "clause": clause,
                    "rule": r_name,
                    "source_text": src,
                    "bbox": bbox
                })

            answer = " ".join(parts)

        # Handle matched metadata
        elif matched_metadata:
            parts = []
            for k, v in matched_metadata.items():
                k_clean = k.replace("_", " ").title()
                parts.append(f"According to your policy metadata, {k_clean} is {v}.")
                rules_used.append(k_clean)
            answer = " ".join(parts)
            citations.append({
                "page": 1,
                "clause": "Policy Schedule Metadata",
                "rule": "Policy Metadata",
                "source_text": f"Policy Metadata: {matched_metadata}"
            })

        # Handle matched text snippets
        elif matched_snippets:
            parts = []
            for snip in matched_snippets:
                parts.append(f"Page {snip['page']}: \"{snip['source_text']}\"")
                citations.append({
                    "page": snip["page"],
                    "clause": snip["clause"],
                    "rule": "Matched Text Snippet",
                    "source_text": snip["source_text"]
                })
            answer = f"Based on your policy document text: " + " ".join(parts)

        # NOT_FOUND Handling
        else:
            grounding_status = "NOT_FOUND"
            confidence = 0.30
            missing_information.append(query)
            clean_q = query.replace("Is ", "").replace("does ", "").replace("covered", "").replace("what is ", "").strip()
            answer = (
                f"I could not find a specific provision for '{query}' in the uploaded policy document. "
                f"Standard policy terms apply, but specific coverage for '{clean_q}' is not explicitly defined in the indexed clauses."
            )

        logger.debug("FINAL GROUNDING STATUS: %s", grounding_status)
        logger.debug("FINAL ANSWER: %s", answer)

        return {
            "policy_id": policy_id,
            "query": query,
            "answer": answer,
            "citations": citations,
            "confidence": confidence,
            "grounding_status": grounding_status,
            "rules_used": rules_used,
            "missing_information": missing_information
        }

    @classmethod
    def process_query(
        cls,
        policy_id: str,
        query: str,
        canonical_json: Dict[str, Any],
        history: Optional[List[Dict[str, Any]]] = None
    ) -> Dict[str, Any]:
        """
        Main entrypoint: Retrieves rules and generates grounded answer.
        """
        retrieval_data = cls.retrieve_relevant_rules(canonical_json, query, history)
        return cls.generate_grounded_answer(policy_id, query, retrieval_data)
