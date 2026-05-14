from src.rag_engine.siliconflow_client import rerank_documents


def rerank(query: str, results: list[dict], top_n: int = 10, threshold: float = 0.2) -> list[dict]:
    if not results:
        return []

    docs = [item.get('content', '') for item in results]
    api_ranked = rerank_documents(query=query, documents=docs, top_n=max(top_n, len(results)))

    api_score_map: dict[int, float] = {int(item['index']): float(item['relevance_score']) for item in api_ranked}
    for idx, item in enumerate(results):
        if idx in api_score_map:
            item['score'] = api_score_map[idx]

    merged = []
    seen = set()
    for item in sorted(results, key=lambda x: x.get('score', 0), reverse=True):
        key = (item.get('content'), item.get('source'))
        if key in seen:
            continue
        seen.add(key)
        if item.get('score', 0) >= threshold:
            merged.append(item)
    return merged[:top_n]
