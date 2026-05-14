from src.rag_engine.engine import run_hybrid_retrieval


def test_rag_engine_runs():
    out = run_hybrid_retrieval('??????')
    assert 'context' in out
