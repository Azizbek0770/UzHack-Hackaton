# FinRAG — Financial Intelligence Platform

> **Production-grade RAG system for financial document QA in Russian & Uzbek**
> Built for: PDF · XLSX · Corporate Disclosures · Multi-language

---

## Architecture Overview

```
rag-platform/
├── backend/                    # Python 3.11 + FastAPI
│   ├── app/
│   │   ├── api/
│   │   │   └── routes.py           # POST /query, GET /status, etc.
│   │   ├── core/
│   │   │   ├── config.py           # Pydantic settings (env-driven)
│   │   │   ├── ingestion.py        # Document traversal & routing
│   │   │   ├── logging.py          # structlog setup + TimingLogger
│   │   │   └── pipeline.py         # RAG orchestrator (main brain)
│   │   ├── models/
│   │   │   └── schemas.py          # All Pydantic domain models
│   │   ├── parsers/
│   │   │   ├── base.py             # BaseParser ABC + JSONParser
│   │   │   ├── pdf_parser.py       # PyMuPDF + PaddleOCR fallback
│   │   │   └── xlsx_parser.py      # pandas multi-sheet extraction
│   │   ├── retrieval/
│   │   │   ├── embeddings.py       # BAAI/bge-m3 multilingual encoder
│   │   │   ├── faiss_index.py      # FAISS (text + table, separate)
│   │   │   ├── bm25.py             # BM25Okapi sparse retrieval
│   │   │   └── hybrid.py           # RRF fusion + query rewriting
│   │   ├── qa/
│   │   │   ├── classifier.py       # Rule-based query type classifier
│   │   │   ├── table_qa.py         # Programmatic numeric extraction
│   │   │   └── llm_qa.py           # LLM reasoning (OpenAI/Anthropic/Ollama)
│   │   └── utils/
│   │       ├── cache.py            # Thread-safe LRU query cache
│   │       ├── confidence.py       # Multi-signal confidence scoring
│   │       ├── text.py             # Text cleaning & validation
│   │       └── language.py         # Language detection (RU/UZ/EN)
│   ├── tests/
│   │   └── test_core.py            # pytest test suite
│   ├── scripts/
│   │   └── evaluate.py             # Benchmark evaluation script
│   ├── requirements.txt
│   ├── Dockerfile
│   └── .env.example
│
├── frontend/                   # React 18 + Vite + TailwindCSS
│   ├── src/
│   │   ├── components/
│   │   │   ├── query/
│   │   │   │   └── QueryInput.tsx      # Main query bar with filters
│   │   │   ├── answer/
│   │   │   │   └── AnswerCard.tsx      # Answer + confidence + keyword HL
│   │   │   ├── sources/
│   │   │   │   └── SourcesPanel.tsx    # Source tags with excerpts
│   │   │   └── ui/
│   │   │       ├── States.tsx          # Loading, error, empty states
│   │   │       ├── DebugPanel.tsx      # Debug info accordion
│   │   │       ├── QueryHistory.tsx    # Sidebar query history
│   │   │       └── StatusBar.tsx       # Pipeline health indicator
│   │   ├── hooks/
│   │   │   └── useQuery.ts             # Query state + history hooks
│   │   ├── pages/
│   │   │   └── MainPage.tsx            # Full layout assembly
│   │   ├── services/
│   │   │   ├── api.ts                  # Axios API service layer
│   │   │   └── types.ts                # TypeScript domain types
│   │   └── styles/
│   │       └── globals.css             # Design tokens + Tailwind base
│   ├── Dockerfile
│   ├── nginx.conf
│   └── package.json
│
├── dataset/                    # Your documents go here
│   └── {company_name}/
│       ├── report_2023.pdf
│       ├── financials_2022.xlsx
│       └── metadata.json
│
├── docker-compose.yml
└── README.md
```

---

## Pipeline Flow

```
User Question
     │
     ▼
┌─────────────────────────────────────┐
│  1. Query Classifier                │
│     numeric / textual / table       │
│     extract: metric, year, company  │
└─────────────────┬───────────────────┘
                  │
     ┌────────────▼────────────┐
     │  2. Query Rewriting     │
     │     expand synonyms     │
     │     add financial ctx   │
     └────────────┬────────────┘
                  │
     ┌────────────▼────────────────────┐
     │  3. Hybrid Retrieval (RRF)      │
     │  ┌──────────┐  ┌─────────────┐ │
     │  │  FAISS   │  │    BM25     │ │
     │  │  Dense   │  │   Sparse    │ │
     │  │ Text idx │  │   Keyword   │ │
     │  │ Table idx│  │   Search    │ │
     │  └────┬─────┘  └──────┬──────┘ │
     │       └───────┬────────┘        │
     │         RRF Fusion              │
     └───────────────┬─────────────────┘
                     │
     ┌───────────────▼───────────────┐
     │  4. Table QA Engine           │
     │     Programmatic extraction   │
     │     metric column → year row  │
     │     Returns if confident      │
     └───────────────┬───────────────┘
                     │ (if no table match)
     ┌───────────────▼───────────────┐
     │  5. LLM QA Module             │
     │     Context → GPT/Claude/Llama│
     │     Strict anti-hallucination │
     │     JSON structured output    │
     └───────────────┬───────────────┘
                     │
     ┌───────────────▼───────────────┐
     │  6. Confidence Calibration    │
     │     LLM conf + retrieval score│
     │     + chunk count + source    │
     └───────────────┬───────────────┘
                     │
     ┌───────────────▼───────────────┐
     │  7. Response + Cache          │
     │     answer, confidence,       │
     │     sources, debug info       │
     └───────────────────────────────┘
```

---

## Quick Start

### Prerequisites

- Python 3.11+
- Node.js 20+
- An LLM API key (OpenAI, Anthropic, or local Ollama)

### 1. Prepare dataset

Place your documents in:

```
rag-platform/dataset/
└── CompanyName/
    ├── annual_report_2023.pdf
    ├── financials_2022.xlsx
    └── metadata.json
```

The company name is inferred from the top-level folder name.

### 2. Backend setup

```bash
cd backend

# Create virtual environment
python -m venv .venv
source .venv/bin/activate   # Windows: .venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Configure environment
cp .env.example .env
# Edit .env with your LLM API key

# Run the server
uvicorn app.main:app --reload --port 8000
```

The first startup will automatically:
1. Traverse `dataset/` and parse all documents
2. Embed all chunks with `bge-m3`
3. Build FAISS + BM25 indexes
4. Save indexes to `indexes/` for fast future restarts

### 3. Frontend setup

```bash
cd frontend

# Install dependencies
npm install

# Start dev server (proxies /api → localhost:8000)
npm run dev
```

Open **http://localhost:5173**

### 4. Docker (production)

```bash
# Set your API key
export LLM_API_KEY=sk-your-key

# Build and run
docker-compose up --build
```

Frontend: **http://localhost:3000**

---

## Configuration Reference

| Variable | Default | Description |
|---|---|---|
| `LLM_PROVIDER` | `openai` | `openai` / `anthropic` / `ollama` |
| `LLM_MODEL` | `gpt-4o-mini` | Model name for the provider |
| `LLM_API_KEY` | — | API key |
| `EMBEDDING_MODEL` | `BAAI/bge-m3` | HuggingFace model ID |
| `EMBEDDING_DEVICE` | `cpu` | `cpu` or `cuda` |
| `OCR_ENABLED` | `false` | Enable PaddleOCR for scanned PDFs |
| `RETRIEVAL_TOP_K` | `10` | Candidates per retriever |
| `RETRIEVAL_FINAL_K` | `5` | Final chunks after RRF |
| `CACHE_ENABLED` | `true` | In-memory query cache |
| `CACHE_TTL_SECONDS` | `3600` | Cache entry lifetime |
| `INGEST_ON_STARTUP` | `true` | Auto-ingest if no index found |

---

## API Reference

### `POST /api/v1/query`

```json
{
  "question": "Какова выручка компании в 2023 году?",
  "company_filter": "Uzpromstroybank",
  "doc_type_filter": "financial_report",
  "debug": true,
  "top_k": 5
}
```

**Response:**

```json
{
  "answer": "Выручка компании за 2023 год составила 1 234 567 тыс. руб. [Лист: Отчёт о прибылях]",
  "confidence": 0.87,
  "confidence_level": "high",
  "query_type": "table",
  "processing_time_ms": 1243.5,
  "relevant_chunks": [
    {
      "file": "financials_2023.xlsx",
      "page": null,
      "sheet": "Отчёт о прибылях",
      "company": "Uzpromstroybank",
      "doc_type": "financial_report",
      "chunk_type": "table",
      "excerpt": "Выручка: 1 234 567 | Год: 2023 | ..."
    }
  ],
  "debug": {
    "query_type": "table",
    "retrieved_text_chunks": 3,
    "retrieved_table_chunks": 2,
    "stage_timings": {
      "classify_ms": 1.2,
      "retrieve_ms": 45.8,
      "table_qa_ms": 3.1,
      "llm_qa_ms": 1192.4
    }
  }
}
```

### `GET /api/v1/status`

Returns pipeline health, index sizes, and configuration.

### `POST /api/v1/ingest`

Triggers a full re-ingestion of the dataset directory.

### `DELETE /api/v1/cache`

Clears the in-memory query cache.

---

## Running Tests

```bash
cd backend
pytest tests/ -v

# With coverage
pytest tests/ -v --cov=app --cov-report=term-missing
```

---

## Evaluation

```bash
cd backend
python scripts/evaluate.py --url http://localhost:8000/api/v1

# Custom questions file
python scripts/evaluate.py --questions my_questions.json --output results.json
```

---

## OCR for Scanned PDFs

Enable OCR support for scanned documents:

```bash
# Install PaddleOCR (heavyweight — ~2GB)
pip install paddlepaddle paddleocr

# In .env:
OCR_ENABLED=true
OCR_LANG=ru   # or uz for Uzbek
```

OCR activates automatically per-page when fewer than 50 characters are extracted by PyMuPDF.

---

## Adding a Custom LLM Provider

Implement the `_call_llm()` method in `app/qa/llm_qa.py` for any OpenAI-compatible API:

```python
elif self._provider == "custom":
    # Your implementation here
    ...
```

---

## Design Decisions

| Decision | Rationale |
|---|---|
| Separate FAISS indexes for text vs tables | Tables need different retrieval behavior; mixing degrades precision |
| RRF over score normalization | RRF is more robust when scores from FAISS and BM25 have different distributions |
| Table QA before LLM | Programmatic extraction is faster, cheaper, and more reliable for numeric queries |
| BGE-M3 for embeddings | Best multilingual model supporting Russian + Uzbek with single encoder |
| LRU cache with TTL | Prevents redundant LLM calls for repeated queries; TTL ensures freshness |
| Structured logging (structlog) | JSON logs in production enable log aggregation (Datadog, GCP, etc.) |

---

## License

MIT — Built for hackathon. Use freely.
