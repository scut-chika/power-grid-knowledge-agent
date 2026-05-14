import json
import math
import re
from pathlib import Path

from src.backend.core.config import settings
from src.rag_engine.siliconflow_client import embed_texts

CACHE_PATH = Path('data/cache/vector_store.json')


def _cosine_similarity(a: list[float], b: list[float]) -> float:
    if not a or not b:
        return 0.0
    n = min(len(a), len(b))
    va = a[:n]
    vb = b[:n]
    dot = sum(x * y for x, y in zip(va, vb))
    na = math.sqrt(sum(x * x for x in va))
    nb = math.sqrt(sum(y * y for y in vb))
    if na == 0 or nb == 0:
        return 0.0
    return dot / (na * nb)


def build_vectors(chunks: list[dict]) -> dict:
    CACHE_PATH.parent.mkdir(parents=True, exist_ok=True)
    vectors = embed_texts([c['text'] for c in chunks])
    records = []
    for c, v in zip(chunks, vectors):
        records.append(
            {
                'id': c['chunk_id'],
                'text': c['text'],
                'metadata': c['metadata'],
                'vector': v,
            }
        )
    CACHE_PATH.write_text(json.dumps(records, ensure_ascii=False), encoding='utf-8')
    return {
        'vector_count': len(records),
        'status': 'api' if settings.embedding_provider == 'api' else 'simulated',
        'provider': settings.embedding_provider,
        'model': settings.embedding_model_name or 'fallback-local-hash',
    }


def query_vectors(query: str, top_n: int = 20) -> list[dict]:
    if not CACHE_PATH.exists():
        return []
    records = json.loads(CACHE_PATH.read_text(encoding='utf-8'))
    qvecs = embed_texts([query])
    qvec = qvecs[0] if qvecs else []

    scored = []
    for r in records:
        score = _cosine_similarity(qvec, r.get('vector', []))
        if score >= settings.similarity_threshold:
            scored.append(
                {
                    'content': r['text'],
                    'metadata': r['metadata'],
                    'score': float(score),
                    'source': r['metadata'].get('file_name', ''),
                }
            )

    scored.sort(key=lambda x: x['score'], reverse=True)
    if scored:
        return scored[:top_n]

    # 向量检索未命中时，执行关键词兜底，避免中文短句查询全部落空
    q_tokens = [t for t in re.findall(r'[\u4e00-\u9fffA-Za-z0-9]{2,}', query.lower()) if t]
    expanded_tokens: list[str] = []
    for token in q_tokens:
        expanded_tokens.append(token)
        # 对中文长词增加双字片段，提升“巡检要点/故障处置流程”类问题召回率
        if re.search(r'[\u4e00-\u9fff]', token) and len(token) >= 4:
            expanded_tokens.extend(token[i:i + 2] for i in range(len(token) - 1))
    q_tokens = list(dict.fromkeys(expanded_tokens))
    lexical = []
    for r in records:
        text = (r.get('text') or '').lower()
        hit = sum(1 for t in q_tokens if t in text)
        if hit > 0:
            score = hit / max(1, len(q_tokens))
            lexical.append(
                {
                    'content': r['text'],
                    'metadata': r['metadata'],
                    'score': float(score),
                    'source': r['metadata'].get('file_name', ''),
                }
            )
    lexical.sort(key=lambda x: x['score'], reverse=True)
    return lexical[:top_n]
