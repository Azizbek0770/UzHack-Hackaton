# Challenge Alignment (UzHack 2026 NBU RAG)

## Scope

This document maps the current implementation against the challenge requirements and defines next-step hardening items.

## Current Alignment

- Backend stack matches requirement:
  - FastAPI service
  - modular ingestion/parsing/chunking/retrieval/QA architecture
- Supported data formats:
  - PDF
  - XLSX
  - JSON
- Multilingual handling:
  - RU/UZ content normalization and OCR language policy
- Retrieval and answering:
  - Dense FAISS + BM25 hybrid retrieval
  - table-aware QA for numeric questions
  - source references included in API output
- Operational robustness:
  - ingestion manifest
  - per-stage ingestion report
  - audit run logging
  - debug endpoints

## Critical Challenge Rules Coverage

- Answer only from provided docs:
  - implemented through retrieval-grounded QA pipeline
- Source citations:
  - returned via `relevant_chunks` with `file` and `page`
- Public/private question workflow:
  - supported by submission builder script:
    - `backend/scripts/build_submission.py`
- XLSX sheet numbering:
  - aligned to challenge rule (sheet index starts from 1)
- PDF page numbering:
  - aligned to technical page order with 1-based output

## Remaining High-Impact Enhancements

- Add stronger answer-type coercion per official `submission_format.json` when available.
- Add strict post-answer verifier to reject answers without at least one valid source.
- Add benchmark script to compute exact/public score proxies against `answers_public.json`.
- Add chunk-level deduplication for duplicated PDF/XLSX disclosures from same report period.
- Add optional OCR quality score logging per page for low-confidence scan pages.

## Practical Runbook for Submission

1. Build indexes from full dataset with ingestion script.
2. Start backend API.
3. Run submission script:
   - `python backend/scripts/build_submission.py --questions <questions.xlsx> --output <submission.json>`
4. Validate output schema against expected competition format.
5. Spot-check numeric/table questions and source pages.

## Quality Gates Before Final Submission

- Backend tests pass
- Frontend lint/build pass
- `/health`, `/metrics`, `/ingestion/report`, `/audit/runs` all operational
- No failed files in latest ingestion report
- Benchmark hit-rate acceptable on public set
