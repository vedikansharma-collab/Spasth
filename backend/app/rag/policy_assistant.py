import re
import logging
import json
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
       "cost sharing", "out of pocket", "claim contribution") to canonical rule categories (co-payment, sum insured, etc.).
    4. Structured Rule Priority: Ranks canonical Policy JSON rules over raw text page snippets.
    5. Irrelevance Filtering & Thresholding: Rejects weak evidence, generic disclaimers, and ungrounded queries.
    6. Semantic Relationship Preservation (Cumulative Bonus, Dual Limits, Conditions).
    7. Zero Financial Payout Calculation (Math Engine handles calculation).
    """

    INTENT_MAP = {
        "copay": [
            "co-payment", "copay", "co pay", "co-pay", "copayment", "deductible", "cost sharing", 
            "cost-sharing", "mandatory co-payment", "claim contribution", "contribute to the claim",
            "contribute to claim", "policyholder contribute", "insured contribute", "pay percentage",
            "pay myself", "pay out of pocket", "percentage of my claim", "percentage of the claim",
            "percentage do i have to pay", "percentage i have to pay", "how much of the claim do i pay",
            "how much of the claim do i pay myself", "pay any percentage", "pay any percentage of my claim",
            "share claim", "my share", "patient share", "insured share", "contribution", "cost sharing in my policy",
            "is there any cost sharing", "claim cost sharing", "percentage paid by the insured", "user percentage"
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
            "cataract", "cataract surgery", "eye surgery", "lens replacement", "cataract limit", "cataract coverage"
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
            "prior to hospital", "days before hospitalization", "before hospitalization",
            "expenses are covered before hospitalization", "before admission expenses"
        ],
        "post_hospitalisation": [
            "post-hospitalisation", "post hospitalisation", "post-hospital", "after discharge",
            "expenses after hospitalization", "after hospitalization",
            "expenses are covered after hospitalization", "after discharge expenses"
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
        "conditions", "apply", "sample", "illustration", "expenses", "expense"
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

        # 2. Semantic & combination rules
        # Co-payment / Cost-sharing combinations:
        if any(w in q_lower for w in ["pay", "paid", "paying", "contribution", "contribute", "share", "cost sharing", "cost-sharing", "co-pay", "copay", "co-payment", "copayment", "co pay"]):
            if any(w in q_lower for w in ["percentage", "claim", "myself", "out of pocket", "how much", "amount", "cost", "portion", "policyholder", "insured", "share"]):
                matched_intents.add("copay")

        if any(w in q_lower for w in ["copay", "co-pay", "co pay", "copayment", "co-payment", "cost sharing", "cost-sharing", "deductible"]):
            matched_intents.add("copay")

        # Sum Insured combinations:
        if any(w in q_lower for w in ["coverage", "cover", "insured", "sum"]):
            if any(w in q_lower for w in ["how much", "total", "overall", "maximum", "amount", "sum", "insured"]):
                matched_intents.add("sum_insured")

        # Cataract combinations:
        if "cataract" in q_lower:
            matched_intents.add("cataract")
            if any(w in q_lower for w in ["waiting", "period", "months", "years", "time", "delay"]):
                matched_intents.add("waiting_period")

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

        # 1. Match Policy Metadata queries
        for meta_key, meta_val in metadata.items():
            if meta_val and meta_key.replace("_", " ") in q_lower:
                matched_metadata[meta_key] = meta_val

        # 2. Rule keyword & semantic matching over structured Canonical Policy JSON
        scored_rules = []
        for rule in rules:
            score = 0
            rule_id = (rule.get("rule_id") or rule.get("rule_key") or "").lower()
            name = (rule.get("name") or rule.get("label") or rule.get("rule_name") or "").lower()
            category = (rule.get("category") or rule.get("rule_type") or "").lower()
            source_text = (rule.get("source_text") or "").lower()
            qualifiers = str(rule.get("qualifiers") or "").lower()
            conditions = str(rule.get("conditions") or "").lower()

            # A. Intent-based Concept Matching (+70 to +80 points)
            for intent in query_intents:
                if intent == "copay":
                    if any(k in rule_id or k in category or k in name or k in source_text for k in ["copay", "co_payment", "co-payment", "copayment", "co pay", "cost_sharing", "cost sharing", "deductible", "claim_contribution"]):
                        score += 75
                elif intent == "sum_insured":
                    if any(k in rule_id or k in category or k in name or k in source_text for k in ["sum_insured", "sum insured", "coverage_limit", "maximum_benefit", "insured_amount"]):
                        score += 75
                elif intent == "cataract":
                    if "cataract" in rule_id or "cataract" in category or "cataract" in name or "cataract" in source_text or "cataract" in qualifiers:
                        score += 70
                elif intent == "waiting_period":
                    if any(k in rule_id or k in category or k in name or k in source_text for k in ["waiting", "ped", "pre-existing", "waiting_period"]):
                        score += 70
                elif intent in rule_id or intent in category or intent in name:
                    score += 65
                elif any(kw in source_text or kw in qualifiers for kw in cls.INTENT_MAP.get(intent, [])):
                    score += 45

            # Compound Intent Boost (e.g., Cataract + Waiting Period)
            if "waiting_period" in query_intents and "cataract" in query_intents:
                if ("waiting" in rule_id or "waiting" in category or "waiting" in name or "waiting" in source_text) and ("cataract" in source_text or "cataract" in qualifiers or "cataract" in name):
                    score += 35

            # B. Non-generic Specific Query Terms Matching (+15 to +25 points)
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

            if score >= 30:
                scored_rules.append((score, rule))
            else:
                rejected_rules.append((rule.get("name") or rule.get("rule_id"), f"Below relevance threshold 30 (score={score})"))

        # Sort rules by score descending
        scored_rules.sort(key=lambda x: x[0], reverse=True)
        matched_rules = [r for score, r in scored_rules[:5]]

        # 3. Fallback page snippet matching (Strict threshold + disclaimer filter)
        if not matched_rules and not matched_metadata and pages:
            search_words = [w for w in q_lower.split() if len(w) > 3 and w not in cls.GENERIC_STOP_WORDS]
            if search_words:
                for page in pages:
                    p_num = page.get("page_number", 1)
                    content = page.get("content", "")
                    for line in content.split("\n"):
                        line_clean = line.strip()
                        if len(line_clean) > 15:
                            # Reject disclaimers
                            if cls.is_disclaimer_snippet(line_clean) or (p_num == 1 and any(w in line_clean.lower() for w in ["disclaimer", "not a real insurance", "sample"])):
                                rejected_rules.append((line_clean[:50], "Filtered out as disclaimer pattern"))
                                continue
                            
                            # Score line snippet
                            snip_score = sum(30 for w in search_words if re.search(r'\b' + re.escape(w) + r'\b', line_clean.lower()))
                            if snip_score >= 60:
                                matched_snippets.append({
                                    "page": p_num,
                                    "clause": "Policy Document Text",
                                    "source_text": line_clean,
                                    "score": snip_score
                                })
                                if len(matched_snippets) >= 3:
                                    break
                    if len(matched_snippets) >= 3:
                        break

        # Log Debug output
        logger.debug("==================================================")
        logger.debug("SPASTH POLICY ASSISTANT RETRIEVAL DEBUG LOG")
        logger.debug("==================================================")
        logger.debug("QUESTION: %s", query)
        logger.debug("EFFECTIVE QUERY: %s", effective_query)
        logger.debug("INTERPRETED INTENT: %s", query_intents)
        logger.debug("--------------------------------------------------")
        logger.debug("TOP RETRIEVED RULES:")
        for idx, (sc, r) in enumerate(scored_rules[:5], start=1):
            logger.debug("  %d. rule_id: %s | rule_name: %s | category: %s | page: %s | score: %d",
                         idx, r.get("rule_id") or r.get("rule_key"), r.get("name"), r.get("category"), r.get("page"), sc)
        logger.debug("--------------------------------------------------")
        logger.debug("REJECTED RESULTS COUNT: %d", len(rejected_rules))
        for r_name, reason in rejected_rules[:5]:
            logger.debug("  - %s: %s", r_name, reason)
        logger.debug("--------------------------------------------------")
        logger.debug("FINAL SELECTED EVIDENCE: %d rules, %d snippets", len(matched_rules), len(matched_snippets))

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
        Validates evidence relevance strictly before passing to LLM or generating answer.
        """
        matched_rules = retrieval_data["matched_rules"]
        matched_metadata = retrieval_data["matched_metadata"]
        matched_snippets = retrieval_data["matched_snippets"]
        effective_query = retrieval_data["effective_query"]
        metadata = retrieval_data["metadata"]

        # Reject weak/empty evidence immediately (Grounding Validation)
        if not matched_rules and not matched_metadata and not matched_snippets:
            clean_q = query.replace("Is ", "").replace("does ", "").replace("covered", "").replace("what is ", "").strip()
            logger.debug("FINAL GROUNDING STATUS: NOT_FOUND")
            logger.debug("==================================================")
            return {
                "policy_id": policy_id,
                "query": query,
                "answer": (
                    f"I could not find a specific provision for '{query}' in the uploaded policy document. "
                    f"Standard policy terms apply, but specific coverage for '{clean_q}' is not explicitly defined in the indexed clauses."
                ),
                "citations": [],
                "confidence": 0.20,
                "grounding_status": "NOT_FOUND",
                "rules_used": [],
                "missing_information": [query]
            }

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
6. If evidence is missing or not found, explicitly state that information is NOT AVAILABLE in the uploaded policy and set grounding_status to "NOT_FOUND".
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

                r_id = (r.get("rule_id") or "").lower()
                r_key = (r.get("rule_key") or "").lower()
                r_cat = (r.get("category") or r.get("rule_type") or "").lower()

                # Handle Co-Payment Rule specifically
                if any(k in r_id or k in r_key or k in r_name.lower() or k in r_cat for k in ["copay", "co_payment", "co-payment", "copayment", "cost_sharing", "cost sharing"]):
                    val = r.get("value", 0.0)
                    fmt = r.get("formatted_value") or (f"{int(val)}%" if val > 0 else "0% (Nil)")
                    raw_quals = r.get('qualifiers')
                    quals_str = ", ".join(raw_quals) if isinstance(raw_quals, list) else str(raw_quals) if raw_quals else ""
                    quals = f" ({quals_str})" if quals_str else ""
                    if val == 0.0 or "nil" in fmt.lower() or "0%" in fmt or "zero" in fmt.lower():
                        parts.append(f"Under your policy ({clause}, Page {page}), the mandatory co-payment is {fmt}{quals}. There is no cost-sharing co-payment deduction required on admissible claims, and eligible hospitalisation expenses are payable up to the Sum Insured.")
                    else:
                        parts.append(f"Under your policy ({clause}, Page {page}), a mandatory co-payment of {fmt}{quals} applies to admissible claims. The policyholder is responsible for paying this percentage out of pocket.")

                # Handle Cataract Surgery
                elif "cataract" in r_name.lower() or "cataract" in r_key:
                    val_str = r.get("formatted_value") or (f"₹{int(r['value']):,}" if isinstance(r.get("value"), (int, float)) else str(r.get("value")))
                    quals = f" ({r.get('qualifiers')})" if r.get("qualifiers") else ""
                    parts.append(f"Under your policy ({clause}, Page {page}), cataract surgery coverage is capped at {val_str}{quals}.")

                # Handle Waiting Period rules
                elif "waiting" in r_cat or "waiting" in r_key or "waiting" in r_name.lower():
                    val_str = r.get("formatted_value") or str(r.get("value"))
                    quals = f" ({r.get('qualifiers')})" if r.get("qualifiers") else ""
                    parts.append(f"Under your policy ({clause}, Page {page}), {r_name} is {val_str}{quals}.")

                # Handle Pre-Hospitalisation
                elif "pre_hospital" in r_key or "pre-hospital" in r_name.lower() or "pre hospital" in r_name.lower():
                    val_str = r.get("formatted_value") or f"{int(r['value'])} days"
                    parts.append(f"Under your policy ({clause}, Page {page}), pre-hospitalisation expenses are covered for {val_str} prior to admission.")

                # Handle Post-Hospitalisation
                elif "post_hospital" in r_key or "post-hospital" in r_name.lower() or "post hospital" in r_name.lower():
                    val_str = r.get("formatted_value") or f"{int(r['value'])} days"
                    parts.append(f"Under your policy ({clause}, Page {page}), post-hospitalisation expenses are covered for {val_str} after discharge.")

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
        logger.debug("==================================================")

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
