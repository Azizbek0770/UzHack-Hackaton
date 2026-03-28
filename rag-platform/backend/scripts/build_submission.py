from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

import pandas as pd
import requests


def _pick_column(columns: list[str], candidates: list[str]) -> str | None:
    normalized = {column.lower(): column for column in columns}
    for candidate in candidates:
        if candidate.lower() in normalized:
            return normalized[candidate.lower()]
    return None


def _coerce_answer(value: str, answer_type: str | None) -> Any:
    if not answer_type:
        return value
    normalized_type = answer_type.strip().lower()
    if normalized_type == "int":
        cleaned = "".join(char for char in value if char.isdigit() or char == "-")
        if cleaned in {"", "-"}:
            return 0
        return int(cleaned)
    if normalized_type == "float":
        text = value.replace(" ", "").replace(",", ".")
        keep = "".join(char for char in text if char.isdigit() or char in {"-", "."})
        if keep in {"", "-", ".", "-."}:
            return 0.0
        return float(keep)
    return value


def run() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--questions", required=True, help="Path to questions_public.xlsx or private questions xlsx")
    parser.add_argument("--output", required=True, help="Output JSON file path")
    parser.add_argument("--api-url", default="http://127.0.0.1:8000/query", help="Backend query endpoint")
    args = parser.parse_args()

    questions_path = Path(args.questions)
    output_path = Path(args.output)
    dataframe = pd.read_excel(questions_path)
    columns = list(dataframe.columns)
    question_column = _pick_column(columns, ["question", "вопрос", "query"])
    answer_type_column = _pick_column(columns, ["answer_type", "type", "format"])
    id_column = _pick_column(columns, ["id", "question_id", "qid"])
    company_column = _pick_column(columns, ["company", "компания"])
    if question_column is None:
        raise ValueError("No question column found in question file.")

    output_items: list[dict[str, Any]] = []
    for index, row in dataframe.iterrows():
        question = str(row[question_column]).strip()
        if not question:
            continue
        payload = {"question": question}
        if company_column and str(row[company_column]).strip():
            payload["company"] = str(row[company_column]).strip()
        response = requests.post(args.api_url, json=payload, timeout=90)
        response.raise_for_status()
        data = response.json()
        answer_text = str(data.get("answer", "")).strip()
        answer_type = None
        if answer_type_column:
            answer_type = str(row[answer_type_column]).strip()
        final_answer = _coerce_answer(answer_text, answer_type)
        item = {
            "question": question,
            "answer": final_answer,
            "relevant_chunks": [
                {
                    "file": source.get("file"),
                    "page": int(source.get("page", 0)),
                }
                for source in data.get("relevant_chunks", [])
            ],
        }
        if id_column:
            item["id"] = row[id_column]
        output_items.append(item)

    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(output_items, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"Saved {len(output_items)} answers to {output_path}")


if __name__ == "__main__":
    run()
