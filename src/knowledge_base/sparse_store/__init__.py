"""Local sparse retrieval index."""

from src.knowledge_base.sparse_store.bm25_store import build_sparse_index, query_sparse

__all__ = ['build_sparse_index', 'query_sparse']
