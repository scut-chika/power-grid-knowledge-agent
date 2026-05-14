from src.rag_engine.engine import run_hybrid_retrieval


def run(query: str) -> dict:
    return run_hybrid_retrieval(query)
