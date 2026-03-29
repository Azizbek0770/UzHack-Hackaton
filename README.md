# 🚀 FinRAG Platform | NBU RAG Challenge - UzHack 2026

![UzHack 2026](https://img.shields.io/badge/UzHack-2026-blue.svg)
![Python](https://img.shields.io/badge/Python-3.11+-yellow.svg)
![FastAPI](https://img.shields.io/badge/FastAPI-009688?style=flat&logo=FastAPI&logoColor=white)
![React](https://img.shields.io/badge/React-20232A?style=flat&logo=react&logoColor=61DAFB)

**FinRAG** is an advanced Retrieval-Augmented Generation (RAG) platform designed specifically for the **NBU RAG Challenge** at the international **UzHack 2026** hackathon (Latvia). 

This system processes complex financial documents (PDFs, XLSX, JSON profiles) of Uzbekistan companies and provides highly accurate, source-backed answers to both textual and numerical queries in Russian and Uzbek.

---

## ✨ Features

- **📄 Multi-Format Document Parsing:** Seamlessly processes scanned PDFs, text-heavy PDFs, and complex Excel (XLSX) financial reports.
- **🔍 Hybrid Retrieval System:** Combines Dense Retrieval (FAISS/BGE-M3) with BM25 keyword search for robust and accurate context extraction.
- **📊 Table QA Engine:** Programmatically extracts financial metrics from tables without relying solely on LLM hallucinations.
- **⚡ Modern Fintech UI:** A sleek, responsive frontend built with React, Vite, and TailwindCSS (featuring dark mode and Framer Motion animations).
- **🌍 Multilingual Support:** Optimized for understanding and generating answers in both **Uzbek** and **Russian**.
- **📍 Source Citations:** Every answer includes exact references (file name and page/sheet number) to ensure trust and transparency.

---

## 🏗️ Architecture

### Backend (Python / FastAPI)
- **Ingestion Pipeline:** Reads company documents, identifies file types, and triggers specific parsers (PyMuPDF for PDFs, pandas for XLSX).
- **Chunking:** Semantic chunking preserving logical structures and document boundaries.
- **Embeddings & Indexing:** `bge-m3` multilingual embeddings stored in FAISS.
- **LLM Engine:** Strict prompting strategy to eliminate hallucinations and enforce context-only answers.

### Frontend (React / Vite)
- **UI Framework:** TailwindCSS for styling and Framer Motion for premium micro-animations.
- **User Flow:** Centralized search interface equipped with loading states, error handling, and answer streaming.
- **Components:** Modular structure (`QueryInput`, `StatusBar`, `States`) built for the best UX.

---

## 💻 Tech Stack

| Category | Technologies |
| --- | --- |
| **Frontend** | React, Vite, TypeScript, TailwindCSS, Framer Motion, Axios |
| **Backend** | Python 3.11+, FastAPI, Uvicorn, Pydantic |
| **AI / RAG** | Langchain, FAISS, BGE-M3, OpenAI/Local LLM |
| **Data Processing** | PyMuPDF, pdfplumber, PaddleOCR, Pandas |

---

## 📂 Project Structure

```text
rag-platform/
├── backend/
│   ├── app/
│   │   ├── api/          # API Routers & Endpoints
│   │   ├── core/         # Config & Settings
│   │   ├── parsing/      # PDF & XLSX parsers
│   │   ├── retrieval/    # FAISS & Hybrid search limits
│   │   └── main.py       # FastAPI Application Entry Point
│   ├── dataset/          # Financial documents & company profiles
│   └── requirements.txt  # Python Dependencies
├── frontend/
│   ├── src/
│   │   ├── components/   # React UI Components
│   │   ├── services/     # API Integration
│   │   └── App.tsx       # Main React Component
│   ├── package.json      # Node Dependencies
│   └── tailwind.config.js
└── README.md
```

---

## 🚀 Getting Started

### Prerequisites
- Node.js (v18+)
- Python (3.11+)

### 1. Backend Setup
```bash
cd rag-platform/backend
# Create a virtual environment
python -m venv venv
source venv/Scripts/activate  # On Windows

# Install dependencies
pip install -r requirements.txt

# Run the backend server
uvicorn app.main:app --reload
```
*The backend API will be available at `http://localhost:8000`*

### 2. Frontend Setup
```bash
cd rag-platform/frontend

# Install dependencies
npm install

# Run the development server
npm run dev
```
*The frontend will be available at `http://localhost:5173`*

---

## 📖 API Documentation

Once the backend is running, you can access the interactive API documentation at:
- **Swagger UI:** `http://localhost:8000/docs`
- **ReDoc:** `http://localhost:8000/redoc`

### Main Endpoint: `POST /query`
```json
// Request
{
  "question": "Mirobod tumanidagi korxona foydasi qancha?"
}

// Response
{
  "answer": "Korxona foydasi 12.55 mln so'mni tashkil etadi.",
  "relevant_chunks": [
    {
      "file": "NSBU_annual_2023.pdf",
      "page": 5
    }
  ]
}
```

---

## 🛡️ License & Acknowledgements
Built for the **NBU RAG Challenge** | **UzHack 2026** (Latvia).  
Dataset and challenge structure provided by NBU Bank.

*Designed and developed specifically for robust financial document reasoning and retrieval.*
