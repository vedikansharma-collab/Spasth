import sys
import json
from pathlib import Path

backend_dir = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(backend_dir))

from app.services.policy_service import PolicyService
from app.rag.policy_assistant import PolicyAssistantEngine

def run_live_tests():
    policies = PolicyService.get_all_policies()
    if not policies:
        print("No policies found in database.")
        return

    pid = policies[0]["id"]
    print(f"Testing on Database Policy ID: {pid} ({policies[0].get('original_filename')})")

    canonical_json = PolicyService.get_canonical_json(pid)

    test_questions = [
        "What is my co-pay?",
        "Do I have to pay any percentage of my claim myself?",
        "What percentage of the claim do I have to pay?",
        "Is there any cost sharing in my policy?",
        "How much of the claim do I pay myself?",
        "What is my sum insured?",
        "What is my cataract coverage?"
    ]

    for idx, q in enumerate(test_questions, start=1):
        res = PolicyAssistantEngine.process_query(pid, q, canonical_json)
        print(f"\n==========================================")
        print(f"TEST #{idx}: {q}")
        print(f"GROUNDING STATUS: {res['grounding_status']}")
        print(f"RULES USED: {res['rules_used']}")
        print(f"ANSWER: {res['answer']}")
        if res.get("citations"):
            for c in res["citations"]:
                print(f"CITATION -> Page {c.get('page')}, Clause: {c.get('clause')}, Rule: {c.get('rule')}")
                print(f"  Source Text: \"{c.get('source_text')}\"")
        else:
            print("CITATION -> None")

if __name__ == "__main__":
    run_live_tests()
