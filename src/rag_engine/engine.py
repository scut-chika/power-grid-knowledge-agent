from src.backend.core.config import settings
from src.rag_engine.context_assembler import assemble_context
from src.rag_engine.graph_retriever import retrieve_by_graph
from src.rag_engine.query_processor import preprocess_query
from src.rag_engine.reranker import rerank
from src.rag_engine.vector_retriever import retrieve_by_vector


def run_hybrid_retrieval(query: str) -> dict:
    parsed = preprocess_query(query)
    v_results = retrieve_by_vector(parsed['normalized_query'])
    g_results = retrieve_by_graph(parsed)
    final = rerank(query=parsed['normalized_query'], results=v_results + g_results, top_n=settings.rerank_top_n, threshold=0.1)
    context = assemble_context(query, final, max_tokens=settings.max_context_token)
    return {'parsed': parsed, 'results': final, 'context': context}
