# Power Grid Knowledge Agent

An end-to-end **RAG + Agent + knowledge-base management** prototype for power-grid secondary operation and maintenance documents.

The system turns heterogeneous materials such as manuals, setting sheets, drawings, and inspection records into searchable knowledge chunks, then answers domain questions with retrieval evidence and source references.

## Highlights

- **Heterogeneous document ingestion**: PDF / DOC / DOCX / table / drawing-style materials can be registered and chunked into a local knowledge base.
- **Traceable RAG pipeline**: vector retrieval, keyword fallback, reranking, context assembly, streaming generation, and source citation.
- **Agent orchestration**: intent recognition, task planning, tool invocation, and domain-specific skills for complex maintenance queries.
- **Web management console**: React + TypeScript + Ant Design frontend with document upload, build scheduling, chat, history, and runtime configuration.
- **Evaluation-oriented design**: retrieval tests were designed around setting lookup, protection logic, device aggregation, drawing search, and comparison tasks.

## Tech Stack

- Backend: Python, FastAPI, SQLite, Pydantic
- Frontend: React, TypeScript, Vite, Ant Design, ECharts
- AI/RAG: embedding API, reranker API, LLM chat-completion API, prompt engineering
- Agent: intent routing, tool registry, ReAct-style execution

## Project Structure

```text
.
├── main.py
├── build_knowledge_base.py
├── src/
│   ├── backend/          # FastAPI routes, auth, config and persistence
│   ├── knowledge_base/   # parsing, chunking, vectorization and graph hooks
│   ├── rag_engine/       # retrieval, reranking and LLM client
│   ├── agent/            # intent, tools and answer generation
│   └── frontend/         # React + TypeScript admin console
├── tests/
├── docs/
└── .env.example
```

## Quick Start

### Backend

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
copy .env.example .env
python main.py
```

API docs: `http://127.0.0.1:8000/docs`

### Frontend

```powershell
cd src/frontend
npm install
npm run dev
```

Frontend dev server: `http://localhost:3000`

## Configuration

This public version intentionally contains **no API keys, private documents, vector-cache files, or local databases**.

Create `.env` from `.env.example`, then fill in your own model endpoints and keys:

```env
LLM_API_KEY=your-llm-api-key
EMBEDDING_API_KEY=your-embedding-api-key
RERANKER_API_KEY=your-reranker-api-key
```

## Notes

- Real power-grid source documents and generated vector indices are excluded from this repository.
- The default account in the prototype is intended for local demo only. Change the credentials and `SECRET_KEY` before deployment.
- This repository is a portfolio-ready public packaging of a graduation-design prototype.

