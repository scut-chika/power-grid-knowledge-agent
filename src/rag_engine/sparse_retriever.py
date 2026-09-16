from src.backend.core.config import settings
from src.knowledge_base.sparse_store.bm25_store import query_sparse


def retrieve_by_sparse(query: str, top_n: int | None = None) -> list[dict]:
    return query_sparse(query, top_n=top_n or settings.sparse_retrieve_top_n)
