# RAG Financial Platform

Production-grade retrieval-augmented generation system for financial documents with a FastAPI backend and a React fintech UI.

## Architecture Overview

- Backend: Modular RAG pipeline with ingestion, parsing, chunking, embeddings, hybrid retrieval, and QA orchestration.
- Frontend: Fintech dashboard UI with dark mode, source citations, and response timing.

## Project Structure

```
rag-platform/
├── backend/
│   ├── app/
│   │   ├── api/
│   │   ├── core/
│   │   ├── ingestion/
│   │   ├── parsing/
│   │   ├── chunking/
│   │   ├── embeddings/
│   │   ├── retrieval/
│   │   ├── tables/
│   │   ├── qa/
│   │   ├── models/
│   │   └── main.py
│   ├── scripts/
│   └── requirements.txt
├── frontend/
│   ├── src/
│   │   ├── components/
│   │   ├── pages/
│   │   ├── services/
│   │   └── App.jsx
│   └── package.json
└── README.md
```

## Backend Usage

1. Install dependencies:

```
pip install -r backend/requirements.txt
```

2. Ingest documents:

```
python backend/scripts/ingest.py
```

3. Run API:

```
uvicorn app.main:app --reload --app-dir backend
```

### Example Query

```
curl -X POST http://localhost:8000/query \
  -H "Content-Type: application/json" \
  -d '{"question": "What is the revenue in 2023?"}'
```

## Frontend Usage

1. Install dependencies:

```
cd frontend
npm install
```

2. Run UI:

```
npm run dev
```

## Configuration

- `RAG_DATASET_PATH`: Dataset root directory.
- `RAG_LLM_ENDPOINT`: Optional LLM inference endpoint.
- `RAG_LLM_API_KEY`: Optional API key for the LLM endpoint.
