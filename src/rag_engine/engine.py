from concurrent.futures import ThreadPoolExecutor
from time import perf_counter
from typing import Callable

from src.backend.core.config import settings
from src.backend.core.logger import get_logger
from src.rag_engine.context_assembler import assemble_context
from src.rag_engine.fusion import reciprocal_rank_fusion
from src.rag_engine.graph_retriever import retrieve_by_graph
from src.rag_engine.query_processor import preprocess_query
from src.rag_engine.reranker import rerank
from src.rag_engine.sparse_retriever import retrieve_by_sparse
from src.rag_engine.vector_retriever import retrieve_by_vector

logger = get_logger(__name__)


def _timed_retrieval(channel: str, retrieve: Callable[[], list[dict]]) -> tuple[list[dict], float, str | None]:
    """Run one retrieval channel without allowing it to fail the whole query."""
    started_at = perf_counter()
    try:
        return retrieve(), (perf_counter() - started_at) * 1000, None
    except Exception as exc:  # noqa: BLE001
        logger.warning('%s retrieval failed: %s', channel, exc)
        return [], (perf_counter() - started_at) * 1000, type(exc).__name__


def run_hybrid_retrieval(query: str) -> dict:
    total_started_at = perf_counter()
    parsed = preprocess_query(query)
    normalized_query = parsed['normalized_query']

    with ThreadPoolExecutor(max_workers=3, thread_name_prefix='rag-retrieval') as executor:
        futures = {
            'dense': executor.submit(
                _timed_retrieval,
                'dense',
                lambda: retrieve_by_vector(normalized_query),
            ),
            'sparse': executor.submit(
                _timed_retrieval,
                'sparse',
                lambda: retrieve_by_sparse(normalized_query),
            ),
            'graph': executor.submit(
                _timed_retrieval,
                'graph',
                lambda: retrieve_by_graph(parsed),
            ),
        }
        channel_outputs = {channel: future.result() for channel, future in futures.items()}

    dense_results, dense_latency, dense_error = channel_outputs['dense']
    sparse_results, sparse_latency, sparse_error = channel_outputs['sparse']
    graph_results, graph_latency, graph_error = channel_outputs['graph']

    fusion_started_at = perf_counter()
    fused = reciprocal_rank_fusion(
        {
            'dense': dense_results,
            'sparse': sparse_results,
            'graph': graph_results,
        },
        k=settings.hybrid_rrf_k,
    )
    fusion_latency = (perf_counter() - fusion_started_at) * 1000

    rerank_started_at = perf_counter()
    final = rerank(
        query=normalized_query,
        results=fused,
        top_n=settings.rerank_top_n,
        threshold=0.1,
    )
    rerank_latency = (perf_counter() - rerank_started_at) * 1000

    context_started_at = perf_counter()
    context = assemble_context(query, final, max_tokens=settings.max_context_token)
    context_latency = (perf_counter() - context_started_at) * 1000
    errors = {
        channel: error
        for channel, error in {
            'dense': dense_error,
            'sparse': sparse_error,
            'graph': graph_error,
        }.items()
        if error
    }
    return {
        'parsed': parsed,
        'results': final,
        'context': context,
        'retrieval': {
            'dense_count': len(dense_results),
            'sparse_count': len(sparse_results),
            'graph_count': len(graph_results),
            'fused_count': len(fused),
            'strategies': ['dense', 'sparse', 'graph', 'rrf', 'rerank'],
            'latency_ms': {
                'dense': round(dense_latency, 2),
                'sparse': round(sparse_latency, 2),
                'graph': round(graph_latency, 2),
                'fusion': round(fusion_latency, 2),
                'rerank': round(rerank_latency, 2),
                'context': round(context_latency, 2),
                'total': round((perf_counter() - total_started_at) * 1000, 2),
            },
            'errors': errors,
        },
    }
