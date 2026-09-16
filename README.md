# Power Grid Knowledge Agent

[![CI](https://github.com/scut-chika/power-grid-knowledge-agent/actions/workflows/ci.yml/badge.svg)](https://github.com/scut-chika/power-grid-knowledge-agent/actions/workflows/ci.yml)

An end-to-end **Hybrid RAG + Knowledge Graph + Agent** prototype for power-grid secondary operation and maintenance documents.

The project converts manuals, setting sheets, inspection records and drawing PDFs into traceable knowledge chunks, retrieves evidence through multiple independent channels, and returns answers with source locations.

## Implemented capabilities

- **Structure-aware ingestion**: PDF pages, DOCX headings/tables, Markdown/text sections and Excel/CSV row ranges are parsed into overlapping chunks with page, section, row, document and chunk identifiers.
- **Hybrid retrieval**: dense retrieval from zvec, local BM25 sparse retrieval and Neo4j one-hop graph retrieval run concurrently with channel-level failure isolation; Reciprocal Rank Fusion (RRF) deduplicates and combines their rankings.
- **Optional reranking**: an OpenAI-compatible reranker endpoint can rescore fused candidates. Without an API key, the system keeps deterministic RRF scores instead of fabricating model scores.
- **Traceable answers**: context and citations retain source file, page/section and retrieval-channel metadata. The React interface exposes these details in the citation panel.
- **Knowledge graph baseline**: conservative, rule-based entity extraction creates document/entity relationships and supports parameterized Neo4j neighborhood queries. It is intentionally documented as a baseline, not as LLM-based extraction.
- **Agent workflow**: intent routing, task planning, tool registry and an optional ReAct-style executor coordinate retrieval and document-oriented skills.
- **Offline evaluation**: a JSONL-based evaluator reports Recall@K, HitRate@K and MRR without requiring an external evaluation service.
- **Observability and CI**: retrieval responses expose per-channel/stage latency, while GitHub Actions runs backend tests and the frontend production build on every change.

## Retrieval flow

```text
PDF / DOCX / Markdown / TXT / Excel / CSV
                    │
          parsing + provenance-aware chunks
                    │
      ┌─────────────┼─────────────┐
      │             │             │
 zvec dense      BM25 sparse   Neo4j graph
      │             │             │
      └─────────────┼─────────────┘
                    │
              RRF rank fusion
                    │
          optional API reranker
                    │
          answer + source citation
```

## Tech stack

- Backend: Python, FastAPI, Pydantic, SQLite
- Retrieval: zvec (HNSW), BM25, RRF, embedding/reranker APIs
- Graph: Neo4j, Cypher
- Agent: intent routing, tool registry, ReAct-style execution
- Frontend: React, TypeScript, Vite, Ant Design, ECharts, Framer Motion
- Engineering: pytest, Docker Compose

## Project structure

```text
.
├── main.py
├── build_knowledge_base.py
├── scripts/evaluate_retrieval.py
├── evals/
├── src/
│   ├── backend/          # FastAPI routes, auth, config and persistence
│   ├── knowledge_base/   # parsers, dense/sparse indexes and graph writer
│   ├── rag_engine/       # multi-channel retrieval, RRF and reranking
│   ├── evaluation/       # retrieval metrics
│   ├── agent/            # intent, planning, tools and skills
│   └── frontend/         # React + TypeScript console
├── tests/
└── deploy/
```

## Quick start

Use Python 3.11 or 3.12. The current zvec release does not provide wheels for every newer Python version.

### Backend

```powershell
py -3.12 -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
Copy-Item .env.example .env
python main.py
```

API documentation: `http://127.0.0.1:8000/docs`

For scanned JPG/PNG/TIFF documents, install the optional OCR dependencies:

```powershell
pip install -r requirements-ocr.txt
```

### Frontend

```powershell
Set-Location src/frontend
npm ci
npm run dev
```

Frontend: `http://localhost:3000`

### Docker Compose

After creating `.env`, start the API, frontend and Neo4j together:

```powershell
docker compose -f deploy/docker-compose.yml up --build
```

The frontend is exposed on `http://localhost`, the API on `http://localhost:8000`, and Neo4j Browser on `http://localhost:7474`.

## Build the knowledge base

Place authorized files in the corresponding directory:

```text
data/raw/documents/   PDF, DOCX, MD, TXT
data/raw/tables/      XLSX, XLS, CSV
data/raw/drawings/    PDF
data/raw/scans/       JPG, JPEG, PNG, TIFF (optional OCR dependency)
```

Then run:

```powershell
python build_knowledge_base.py --mode full
```

Incremental mode fingerprints the corpus and skips rebuilding when nothing changed. When files are added, modified or removed, all retrieval indexes are rebuilt together so vector, sparse and graph data cannot drift apart.

## Retrieval evaluation

Create a labelled JSONL dataset following [evals/README.md](evals/README.md), then run:

```powershell
python scripts/evaluate_retrieval.py `
  --dataset evals/retrieval_cases.jsonl `
  --strategy hybrid `
  --k 10 `
  --output data/eval/latest.json
```

No benchmark score is bundled with the repository. Add labels from documents you are authorized to use before reporting retrieval improvements.

## Configuration

This public repository contains no model keys, source documents, vector caches or local databases. Configure `.env` with your own endpoints:

```env
LLM_API_KEY=your-llm-api-key
LLM_MODEL_NAME=your-chat-model
EMBEDDING_API_KEY=your-embedding-api-key
EMBEDDING_MODEL_NAME=your-embedding-model
RERANKER_API_KEY=your-reranker-api-key
RERANKER_MODEL_NAME=your-reranker-model
```

The local hash embedding is a deterministic development fallback only; it is not a semantic model and must not be used to report production retrieval quality.

## Current boundaries

- Legacy `.doc` and native `.dwg` parsing are not implemented.
- OCR is optional and is skipped cleanly when PaddleOCR is unavailable.
- Entity extraction is currently rule-based. LLM structured extraction and entity-review workflows are future work.
- The Agent is a local tool-orchestration implementation, not a LangGraph workflow.
