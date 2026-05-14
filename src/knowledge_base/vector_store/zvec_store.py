import json
import logging
import re
import shutil
from pathlib import Path

import zvec

from src.backend.core.config import settings
from src.rag_engine.siliconflow_client import embed_texts

logger = logging.getLogger(__name__)

_zvec_initialized = False
_collection_handle = None
_collection_generation = 0


def _ensure_init():
    global _zvec_initialized
    if not _zvec_initialized:
        zvec.init()
        _zvec_initialized = True


def _get_data_dir() -> Path:
    return Path(settings.zvec_data_dir)


def _open_collection():
    global _collection_handle
    if _collection_handle is not None:
        return _collection_handle
    _ensure_init()
    data_dir = _get_data_dir()
    if not data_dir.exists():
        raise FileNotFoundError(f"Vector store not found: {data_dir}")
    _collection_handle = zvec.open(str(data_dir))
    return _collection_handle


def _create_collection(dimension: int):
    global _collection_handle, _collection_generation
    _ensure_init()
    data_dir = _get_data_dir()

    if data_dir.exists():
        if _collection_handle is not None:
            try:
                _collection_handle.destroy()
            except Exception:
                _collection_handle = None
                shutil.rmtree(data_dir, ignore_errors=True)
        else:
            try:
                old = zvec.open(str(data_dir))
                old.destroy()
            except Exception:
                shutil.rmtree(data_dir, ignore_errors=True)
    _collection_handle = None

    schema = zvec.CollectionSchema(
        name=settings.zvec_collection_name,
        fields=[
            zvec.FieldSchema('text', zvec.DataType.STRING, nullable=True),
            zvec.FieldSchema('metadata', zvec.DataType.STRING, nullable=True),
        ],
        vectors=[
            zvec.VectorSchema(
                'embedding',
                zvec.DataType.VECTOR_FP32,
                dimension=dimension,
                index_param=zvec.HnswIndexParam(metric_type=zvec.MetricType.COSINE),
            ),
        ],
    )

    data_dir.parent.mkdir(parents=True, exist_ok=True)
    coll = zvec.create_and_open(str(data_dir), schema)
    _collection_handle = coll
    _collection_generation += 1
    return coll


def build_vectors(chunks: list[dict]) -> dict:
    """Embed text chunks and store them in zvec. Replaces any existing collection."""
    if not chunks:
        return {'vector_count': 0, 'status': 'empty', 'provider': settings.embedding_provider}

    vectors = embed_texts([c['text'] for c in chunks])
    dimension = len(vectors[0]) if vectors else settings.embedding_dimension

    coll = _create_collection(dimension)

    docs = []
    for c, v in zip(chunks, vectors):
        docs.append(
            zvec.Doc(
                id=c['chunk_id'],
                fields={
                    'text': c['text'],
                    'metadata': json.dumps(c['metadata'], ensure_ascii=False),
                },
                vectors={'embedding': v},
            )
        )

    batch_size = 200
    for i in range(0, len(docs), batch_size):
        coll.insert(docs[i:i + batch_size])

    return {
        'vector_count': len(docs),
        'status': 'api' if settings.embedding_provider == 'api' else 'simulated',
        'provider': settings.embedding_provider,
        'model': settings.embedding_model_name or 'fallback-local-hash',
    }


def query_vectors(query: str, top_n: int = 20) -> list[dict]:
    """Search vectors by semantic similarity, with keyword fallback."""
    if not _get_data_dir().exists():
        return []

    try:
        coll = _open_collection()
    except Exception as e:
        logger.warning('Failed to open zvec collection: %s', e)
        return []

    qvecs = embed_texts([query])
    qvec = qvecs[0] if qvecs else []
    if not qvec:
        return []

    try:
        results = coll.query(
            zvec.VectorQuery('embedding', vector=qvec),
            topk=top_n,
            output_fields=['text', 'metadata'],
            include_vector=False,
        )
    except Exception as e:
        logger.warning('zvec query failed: %s', e)
        return []

    scored = []
    for hit in results:
        if hit.score >= settings.similarity_threshold:
            meta = _parse_metadata(hit.fields.get('metadata'))
            scored.append({
                'content': hit.fields.get('text', ''),
                'metadata': meta,
                'score': float(hit.score),
                'source': meta.get('file_name', ''),
            })

    if scored:
        return scored

    return _keyword_fallback(coll, query, qvec, top_n)


def _keyword_fallback(coll, query: str, qvec: list[float], top_n: int) -> list[dict]:
    """Fall back to keyword matching when no vector results exceed the threshold."""
    try:
        doc_count = coll.stats.doc_count
    except Exception:
        doc_count = 500

    if doc_count == 0:
        return []

    try:
        all_results = coll.query(
            zvec.VectorQuery('embedding', vector=qvec),
            topk=min(doc_count, 1000),
            output_fields=['text', 'metadata'],
            include_vector=False,
        )
    except Exception:
        return []

    q_tokens = [t for t in re.findall(r'[\u4e00-\u9fffA-Za-z0-9]{2,}', query.lower()) if t]
    expanded: list[str] = []
    for token in q_tokens:
        expanded.append(token)
        if re.search(r'[\u4e00-\u9fff]', token) and len(token) >= 4:
            expanded.extend(token[i:i + 2] for i in range(len(token) - 1))
    q_tokens = list(dict.fromkeys(expanded))

    if not q_tokens:
        return []

    lexical = []
    for hit in all_results:
        text = (hit.fields.get('text') or '').lower()
        hit_count = sum(1 for t in q_tokens if t in text)
        if hit_count > 0:
            meta = _parse_metadata(hit.fields.get('metadata'))
            lexical.append({
                'content': hit.fields.get('text', ''),
                'metadata': meta,
                'score': hit_count / max(1, len(q_tokens)),
                'source': meta.get('file_name', ''),
            })

    lexical.sort(key=lambda x: x['score'], reverse=True)
    return lexical[:top_n]


def _parse_metadata(raw: str | None) -> dict:
    if not raw:
        return {}
    try:
        return json.loads(raw)
    except (json.JSONDecodeError, TypeError):
        return {}
