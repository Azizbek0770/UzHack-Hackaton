"""
Evaluation Script — RAG Platform Benchmarking
Runs a set of test questions and measures accuracy + latency.
Saves results to a JSON report.

Usage:
    python scripts/evaluate.py --questions questions.json --output results.json
"""

from __future__ import annotations

import argparse
import asyncio
import json
import time
from pathlib import Path
from typing import Any, Dict, List, Optional


SAMPLE_QUESTIONS = [
    {
        "id": "q1",
        "question": "Какова выручка компании за 2023 год?",
        "expected_type": "numeric",
        "company": None,
    },
    {
        "id": "q2",
        "question": "Каковы суммарные активы на конец отчётного периода?",
        "expected_type": "numeric",
        "company": None,
    },
    {
        "id": "q3",
        "question": "Каким является основной вид деятельности компании?",
        "expected_type": "textual",
        "company": None,
    },
    {
        "id": "q4",
        "question": "Какова чистая прибыль за 2022 год?",
        "expected_type": "numeric",
        "company": None,
    },
    {
        "id": "q5",
        "question": "Сколько сотрудников работает в компании?",
        "expected_type": "numeric",
        "company": None,
    },
]


async def evaluate(
    questions: List[Dict[str, Any]],
    base_url: str = "http://localhost:8000/api/v1",
) -> Dict[str, Any]:
    """
    Run all evaluation questions and collect metrics.

    Args:
        questions: List of question dicts with id, question, expected_type.
        base_url: Backend API base URL.

    Returns:
        Evaluation results dict.
    """
    try:
        import httpx
    except ImportError:
        raise RuntimeError("httpx not installed. Run: pip install httpx")

    results = []
    total_latency = 0.0
    answered = 0

    async with httpx.AsyncClient(base_url=base_url, timeout=60.0) as client:
        for q in questions:
            start = time.perf_counter()
            try:
                resp = await client.post(
                    "/query",
                    json={
                        "question": q["question"],
                        "company_filter": q.get("company"),
                        "debug": False,
                    },
                )
                elapsed = (time.perf_counter() - start) * 1000
                total_latency += elapsed

                if resp.status_code == 200:
                    data = resp.json()
                    answered += 1
                    results.append({
                        "id": q["id"],
                        "question": q["question"],
                        "answer": data["answer"],
                        "confidence": data["confidence"],
                        "confidence_level": data["confidence_level"],
                        "query_type": data["query_type"],
                        "latency_ms": elapsed,
                        "sources": len(data.get("relevant_chunks", [])),
                        "status": "ok",
                    })
                else:
                    results.append({
                        "id": q["id"],
                        "question": q["question"],
                        "status": "error",
                        "http_status": resp.status_code,
                        "latency_ms": elapsed,
                    })

            except Exception as e:
                elapsed = (time.perf_counter() - start) * 1000
                results.append({
                    "id": q["id"],
                    "question": q["question"],
                    "status": "exception",
                    "error": str(e),
                    "latency_ms": elapsed,
                })

    n = len(questions)
    avg_latency = total_latency / n if n > 0 else 0
    success_rate = answered / n if n > 0 else 0

    avg_confidence = (
        sum(r.get("confidence", 0) for r in results if r.get("status") == "ok")
        / max(answered, 1)
    )

    return {
        "summary": {
            "total_questions": n,
            "answered": answered,
            "failed": n - answered,
            "success_rate": round(success_rate, 3),
            "avg_latency_ms": round(avg_latency, 1),
            "avg_confidence": round(avg_confidence, 3),
        },
        "results": results,
    }


def main():
    parser = argparse.ArgumentParser(description="Evaluate RAG pipeline")
    parser.add_argument(
        "--questions",
        type=Path,
        default=None,
        help="Path to JSON file with questions (uses built-in samples if not provided)",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=Path("evaluation_results.json"),
        help="Output file for results",
    )
    parser.add_argument(
        "--url",
        default="http://localhost:8000/api/v1",
        help="Backend API base URL",
    )
    args = parser.parse_args()

    if args.questions and args.questions.exists():
        with open(args.questions, encoding="utf-8") as f:
            questions = json.load(f)
    else:
        print("Using built-in sample questions")
        questions = SAMPLE_QUESTIONS

    print(f"Running evaluation on {len(questions)} questions...")
    print(f"Backend: {args.url}")
    print("-" * 60)

    results = asyncio.run(evaluate(questions, base_url=args.url))

    # Print summary
    summary = results["summary"]
    print(f"\n{'=' * 60}")
    print("EVALUATION RESULTS")
    print(f"{'=' * 60}")
    print(f"Total questions:  {summary['total_questions']}")
    print(f"Answered:         {summary['answered']}")
    print(f"Failed:           {summary['failed']}")
    print(f"Success rate:     {summary['success_rate']:.1%}")
    print(f"Avg latency:      {summary['avg_latency_ms']:.0f} ms")
    print(f"Avg confidence:   {summary['avg_confidence']:.3f}")

    print(f"\nIndividual results:")
    for r in results["results"]:
        status = "✓" if r["status"] == "ok" else "✗"
        latency = f"{r['latency_ms']:.0f}ms"
        conf = f"{r.get('confidence', 0):.2f}" if r.get("confidence") else "N/A"
        print(f"  {status} [{r['id']}] {r['question'][:50]:<50} {latency:>8} conf={conf}")

    # Save results
    with open(args.output, "w", encoding="utf-8") as f:
        json.dump(results, f, ensure_ascii=False, indent=2)
    print(f"\nResults saved to: {args.output}")


if __name__ == "__main__":
    main()
