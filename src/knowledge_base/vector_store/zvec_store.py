import json
import logging
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
        global _collection_handle
        data_dir = _get_data_dir()
        if data_dir.exists():
            if _collection_handle is not None:
                try:
                    _collection_handle.destroy()
                except Exception:
                    shutil.rmtree(data_dir, ignore_errors=True)
            else:
                shutil.rmtree(data_dir, ignore_errors=True)
        _collection_handle = None
        return {'vector_count': 0, 'status': 'empty', 'provider': settings.embedding_provider}

    vectors = embed_texts([c['text'] for c in chunks])
    dimension = len(vectors[0]) if vectors else settings.embedding_dimension

    coll = _create_collection(dimension)

    docs = []
    for c, v in zip(chunks, vectors):
        metadata = {'chunk_id': c['chunk_id'], **c.get('metadata', {})}
        docs.append(
            zvec.Doc(
                id=c['chunk_id'],
                fields={
                    'text': c['text'],
                    'metadata': json.dumps(metadata, ensure_ascii=False),
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
    """Search vectors by semantic similarity."""
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
            zvec.Query('embedding', vector=qvec),
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
                'retrieval_channel': 'dense',
            })

    return scored


def _parse_metadata(raw: str | None) -> dict:
    if not raw:
        return {}
    try:
        return json.loads(raw)
    except (json.JSONDecodeError, TypeError):
        return {}
