from src.backend.core.config import settings
from src.knowledge_base.vector_store.zvec_store import query_vectors


def retrieve_by_vector(query: str, top_n: int | None = None) -> list[dict]:
    n = top_n or settings.retrieve_top_n
    return query_vectors(query, top_n=n)
