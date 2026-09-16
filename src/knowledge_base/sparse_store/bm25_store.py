"""Small persistent BM25 index used for lexical retrieval.

The implementation deliberately has no extra runtime dependency. It is suitable
for the document volume of this portfolio project and keeps the retrieval path
available when external embedding services are not configured.
"""
from __future__ import annotations

import json
import math
import re
import threading
from collections import Counter
from pathlib import Path
from typing import Any

from src.backend.core.config import settings

_TOKEN_PATTERN = re.compile(r'[A-Za-z0-9][A-Za-z0-9_.#/\-]*|[\u4e00-\u9fff]+')
_INDEX_VERSION = 1
_CACHE_LOCK = threading.Lock()
_RUNTIME_CACHE_KEY: tuple[str, int, int] | None = None
_RUNTIME_CACHE: dict[str, Any] | None = None


def tokenize(text: str) -> list[str]:
    """Tokenize mixed Chinese/English power-grid text.

    Chinese sequences keep the complete term and overlapping bigrams so device
    names such as ``线路保护装置`` can match both full and partial queries.
    """
    tokens: list[str] = []
    for match in _TOKEN_PATTERN.finditer(text.lower()):
        term = match.group(0)
        if re.fullmatch(r'[\u4e00-\u9fff]+', term):
            tokens.append(term)
            if len(term) > 1:
                tokens.extend(term[i:i + 2] for i in range(len(term) - 1))
        else:
            tokens.append(term)
    return tokens


def _index_path() -> Path:
    return Path(settings.sparse_index_path)


def _prepare_runtime_index(documents: list[dict[str, Any]]) -> dict[str, Any]:
    tokenized = [document.get('tokens') or tokenize(document.get('text', '')) for document in documents]
    frequencies = [Counter(tokens) for tokens in tokenized]
    document_frequency: Counter[str] = Counter()
    for tokens in tokenized:
        document_frequency.update(set(tokens))
    return {
        'documents': documents,
        'tokenized': tokenized,
        'frequencies': frequencies,
        'document_frequency': document_frequency,
        'average_length': sum(len(tokens) for tokens in tokenized) / max(1, len(tokenized)),
    }


def _cache_key(path: Path) -> tuple[str, int, int]:
    stat = path.stat()
    return str(path.resolve()), stat.st_mtime_ns, stat.st_size


def _set_runtime_cache(path: Path, documents: list[dict[str, Any]]) -> dict[str, Any]:
    global _RUNTIME_CACHE_KEY, _RUNTIME_CACHE
    runtime_index = _prepare_runtime_index(documents)
    with _CACHE_LOCK:
        _RUNTIME_CACHE_KEY = _cache_key(path)
        _RUNTIME_CACHE = runtime_index
    return runtime_index


def build_sparse_index(chunks: list[dict]) -> dict:
    """Replace the local sparse index with the supplied complete chunk set."""
    path = _index_path()
    path.parent.mkdir(parents=True, exist_ok=True)

    documents = []
    for chunk in chunks:
        metadata = {'chunk_id': chunk['chunk_id'], **chunk.get('metadata', {})}
        documents.append(
            {
                'chunk_id': chunk['chunk_id'],
                'text': chunk['text'],
                'metadata': metadata,
                'tokens': tokenize(chunk['text']),
            }
        )

    payload = {'version': _INDEX_VERSION, 'documents': documents}
    temp_path = path.with_suffix(f'{path.suffix}.tmp')
    temp_path.write_text(json.dumps(payload, ensure_ascii=False), encoding='utf-8')
    temp_path.replace(path)
    _set_runtime_cache(path, documents)
    return {'document_count': len(documents), 'status': 'built', 'path': str(path)}


def _load_runtime_index() -> dict[str, Any]:
    path = _index_path()
    if not path.exists():
        return _prepare_runtime_index([])
    key = _cache_key(path)
    with _CACHE_LOCK:
        if _RUNTIME_CACHE_KEY == key and _RUNTIME_CACHE is not None:
            return _RUNTIME_CACHE
    try:
        payload = json.loads(path.read_text(encoding='utf-8'))
    except (OSError, json.JSONDecodeError):
        return _prepare_runtime_index([])
    if payload.get('version') != _INDEX_VERSION:
        return _prepare_runtime_index([])
    return _set_runtime_cache(path, payload.get('documents') or [])


def query_sparse(query: str, top_n: int = 20, k1: float = 1.5, b: float = 0.75) -> list[dict]:
    """Rank indexed chunks with Okapi BM25."""
    query_tokens = list(dict.fromkeys(tokenize(query)))
    runtime_index = _load_runtime_index()
    documents = runtime_index['documents']
    if not query_tokens or not documents:
        return []

    tokenized = runtime_index['tokenized']
    frequencies_by_document = runtime_index['frequencies']
    document_frequency = runtime_index['document_frequency']
    document_count = len(documents)
    avg_length = runtime_index['average_length']

    scored: list[tuple[float, dict]] = []
    for document, tokens, frequencies in zip(documents, tokenized, frequencies_by_document):
        length = len(tokens)
        score = 0.0
        for term in query_tokens:
            frequency = frequencies.get(term, 0)
            if frequency == 0:
                continue
            df = document_frequency[term]
            inverse_document_frequency = math.log(1 + (document_count - df + 0.5) / (df + 0.5))
            denominator = frequency + k1 * (1 - b + b * length / max(avg_length, 1.0))
            score += inverse_document_frequency * (frequency * (k1 + 1)) / denominator
        if score > 0:
            scored.append((score, document))

    scored.sort(key=lambda item: item[0], reverse=True)
    max_score = scored[0][0] if scored else 1.0
    results = []
    for raw_score, document in scored[:top_n]:
        metadata = dict(document.get('metadata') or {})
        results.append(
            {
                'content': document.get('text', ''),
                'metadata': metadata,
                'score': raw_score / max_score,
                'raw_score': raw_score,
                'source': metadata.get('file_name', ''),
                'retrieval_channel': 'sparse',
            }
        )
    return results
