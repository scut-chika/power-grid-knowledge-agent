from src.rag_engine.siliconflow_client import rerank_documents


def rerank(query: str, results: list[dict], top_n: int = 10, threshold: float = 0.2) -> list[dict]:
    if not results:
        return []

    docs = [item.get('content', '') for item in results]
    api_ranked = rerank_documents(query=query, documents=docs, top_n=max(top_n, len(results)))

    ranked_results = [{**item, 'metadata': dict(item.get('metadata') or {})} for item in results]
    api_score_map: dict[int, float] = {
        int(item['index']): float(item['relevance_score'])
        for item in api_ranked
        if item.get('provider') == 'api'
    }
    for idx, item in enumerate(ranked_results):
        if idx in api_score_map:
            reranker_score = api_score_map[idx]
            fusion_score = float(item.get('score', 0.0))
            item['rerank_score'] = reranker_score
            item['score'] = 0.75 * reranker_score + 0.25 * fusion_score
            item['metadata']['reranker'] = 'api'
        else:
            item['metadata']['reranker'] = 'not_configured'

    merged = []
    seen = set()
    for item in sorted(ranked_results, key=lambda x: x.get('score', 0), reverse=True):
        metadata = item.get('metadata') or {}
        key = metadata.get('chunk_id') or (item.get('content'), item.get('source'))
        if key in seen:
            continue
        seen.add(key)
        if item.get('score', 0) >= threshold:
            merged.append(item)
    return merged[:top_n]
