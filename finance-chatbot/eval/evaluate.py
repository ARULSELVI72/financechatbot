"""
Evaluation harness for FinanceBot.

Runs each question in eval_dataset.json through the live backend API and
scores the responses on three axes:

1. Keyword coverage  — how many expected keywords appear in the answer
                        (simple proxy for "accuracy" / relevant content).
2. Retrieval hit rate — whether the RAG pipeline retrieved the expected
                         source document for questions that should hit the
                         knowledge base.
3. LLM-judged coherence — the LLM itself scores each answer 1-5 for
                           coherence and helpfulness (a lightweight
                           "LLM-as-judge" pattern). This step is optional
                           and skipped automatically if GROQ_API_KEY isn't
                           set — see the printed note if so.

Usage:
    1. Start the backend:  python backend/app.py
    2. In another terminal, from the project root: python eval/evaluate.py
"""

import json
import os
import sys
from pathlib import Path

import requests

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.append(str(PROJECT_ROOT))

BACKEND_URL = os.environ.get("BACKEND_URL", "http://localhost:5000/api/chat")
DATASET_PATH = Path(__file__).resolve().parent / "eval_dataset.json"

JUDGE_PROMPT_TEMPLATE = """You are grading a finance chatbot's answer for coherence and helpfulness.

Question: {question}
Answer: {answer}

Rate the answer from 1 to 5, where:
1 = incoherent, off-topic, or unhelpful
3 = understandable but has notable gaps
5 = clear, well-organized, and directly helpful

Respond with ONLY the number."""


def load_dataset():
    with open(DATASET_PATH, "r", encoding="utf-8") as f:
        return json.load(f)


def call_backend(question: str):
    resp = requests.post(BACKEND_URL, json={"message": question, "history": []}, timeout=60)
    resp.raise_for_status()
    return resp.json()


def keyword_coverage(answer: str, expected_keywords) -> float:
    if not expected_keywords:
        return 1.0
    lowered = answer.lower()
    hits = sum(1 for kw in expected_keywords if kw.lower() in lowered)
    return hits / len(expected_keywords)


def judge_coherence(question: str, answer: str):
    """Returns an int 1-5, or None if judging isn't available."""
    try:
        from llm.llm_client import get_response
    except ImportError:
        return None
    prompt = JUDGE_PROMPT_TEMPLATE.format(question=question, answer=answer)
    try:
        raw = get_response(prompt, history=[], system_prompt="You are a strict, concise grader.")
        digits = "".join(ch for ch in raw if ch.isdigit())
        return int(digits[0]) if digits else None
    except Exception:
        return None


def run_eval():
    dataset = load_dataset()
    results = []

    print(f"Running {len(dataset)} eval questions against {BACKEND_URL}\n")

    for i, item in enumerate(dataset, start=1):
        question = item["question"]
        expected_keywords = item.get("expected_keywords", [])
        expected_source = item.get("expected_source")

        try:
            data = call_backend(question)
        except requests.exceptions.RequestException as exc:
            print(f"[{i}] FAILED to reach backend: {exc}")
            continue

        answer = data.get("reply", "")
        sources = data.get("sources", [])

        kw_score = keyword_coverage(answer, expected_keywords)
        retrieval_hit = (expected_source is None) or (expected_source in sources)
        coherence = judge_coherence(question, answer)

        results.append({
            "question": question,
            "keyword_coverage": kw_score,
            "retrieval_hit": retrieval_hit,
            "coherence": coherence,
        })

        print(f"[{i}] {question}")
        print(f"    keyword_coverage : {kw_score:.2f}")
        print(f"    retrieval_hit    : {retrieval_hit}  (sources: {sources})")
        print(f"    coherence (1-5)  : {coherence if coherence is not None else 'skipped'}")
        print()

    if not results:
        print("No results collected — is the backend running?")
        return

    avg_kw = sum(r["keyword_coverage"] for r in results) / len(results)
    hit_rate = sum(1 for r in results if r["retrieval_hit"]) / len(results)
    coherence_scores = [r["coherence"] for r in results if r["coherence"] is not None]
    avg_coherence = sum(coherence_scores) / len(coherence_scores) if coherence_scores else None

    print("=" * 50)
    print("SUMMARY")
    print("=" * 50)
    print(f"Avg keyword coverage : {avg_kw:.2%}")
    print(f"Retrieval hit rate   : {hit_rate:.2%}")
    print(f"Avg coherence (1-5)  : {avg_coherence:.2f}" if avg_coherence else "Avg coherence (1-5)  : skipped (no GROQ_API_KEY)")


if __name__ == "__main__":
    run_eval()
