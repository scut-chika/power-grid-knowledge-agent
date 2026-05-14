import hashlib
import json
from typing import Any

import httpx

from src.backend.core.config import settings
from src.backend.core.runtime_config import get_runtime_config


def _normalize_base_url(base_url: str) -> str:
    return base_url.rstrip('/')


def _mock_embedding(text: str, dim: int) -> list[float]:
    digest = hashlib.sha256(text.encode('utf-8')).digest()
    seed = [b / 255 for b in digest]
    return (seed * ((dim // len(seed)) + 1))[:dim]


def embed_texts(texts: list[str]) -> list[list[float]]:
    if not texts:
        return []

    cfg = get_runtime_config()
    api_key = cfg.get('embedding_api_key', '')
    model_name = cfg.get('embedding_model_name', '')
    base_url = cfg.get('embedding_api_base_url', settings.embedding_api_base_url)

    if not (api_key and model_name):
        return [_mock_embedding(t, settings.embedding_dimension) for t in texts]

    url = f"{_normalize_base_url(base_url)}/v1/embeddings"
    headers = {
        'Authorization': f"Bearer {api_key}",
        'Content-Type': 'application/json',
    }
    payload: dict[str, Any] = {
        'model': model_name,
        'input': texts,
    }

    try:
        with httpx.Client(timeout=20) as client:
            response = client.post(url, json=payload, headers=headers)
            response.raise_for_status()
            data = response.json()
    except Exception:
        return [_mock_embedding(t, settings.embedding_dimension) for t in texts]

    vectors = []
    for item in data.get('data', []):
        emb = item.get('embedding') or []
        vectors.append([float(x) for x in emb])

    if len(vectors) != len(texts):
        return [_mock_embedding(t, settings.embedding_dimension) for t in texts]
    return vectors


def rerank_documents(query: str, documents: list[str], top_n: int) -> list[dict]:
    if not documents:
        return []

    cfg = get_runtime_config()
    api_key = cfg.get('reranker_api_key', '')
    model_name = cfg.get('reranker_model_name', '')
    base_url = cfg.get('reranker_api_base_url', settings.reranker_api_base_url)

    if not (api_key and model_name):
        return [
            {'index': idx, 'relevance_score': 0.5, 'document': doc}
            for idx, doc in enumerate(documents[:top_n])
        ]

    url = f"{_normalize_base_url(base_url)}/v1/rerank"
    headers = {
        'Authorization': f"Bearer {api_key}",
        'Content-Type': 'application/json',
    }
    payload: dict[str, Any] = {
        'model': model_name,
        'query': query,
        'documents': documents,
        'top_n': top_n,
    }

    try:
        with httpx.Client(timeout=20) as client:
            response = client.post(url, json=payload, headers=headers)
            response.raise_for_status()
            data = response.json()
    except Exception:
        return [
            {'index': idx, 'relevance_score': 0.5, 'document': doc}
            for idx, doc in enumerate(documents[:top_n])
        ]

    results = data.get('results') or data.get('data') or []
    normalized = []
    for item in results:
        idx = int(item.get('index', 0))
        score = float(item.get('relevance_score', item.get('score', 0)))
        if 0 <= idx < len(documents):
            normalized.append({'index': idx, 'relevance_score': score, 'document': documents[idx]})

    if not normalized:
        return [
            {'index': idx, 'relevance_score': 0.5, 'document': doc}
            for idx, doc in enumerate(documents[:top_n])
        ]
    return normalized


def chat_completion(messages: list[dict], temperature: float = 0.2, max_tokens: int = 1024) -> str | None:
    cfg = get_runtime_config()
    api_key = cfg.get('llm_api_key', '')
    model_name = cfg.get('llm_model_name', '')
    base_url = cfg.get('llm_api_base_url', settings.llm_api_base_url)

    if not (api_key and model_name):
        return None

    url = f"{_normalize_base_url(base_url)}/v1/chat/completions"
    headers = {
        'Authorization': f"Bearer {api_key}",
        'Content-Type': 'application/json',
    }
    payload: dict[str, Any] = {
        'model': model_name,
        'messages': messages,
        'temperature': temperature,
        'max_tokens': max_tokens,
    }

    try:
        with httpx.Client(timeout=90) as client:
            response = client.post(url, json=payload, headers=headers)
            response.raise_for_status()
            data = response.json()
    except Exception:
        return None

    choices = data.get('choices') or []
    if not choices:
        return None
    message = choices[0].get('message') or {}
    content = message.get('content')
    if not content:
        return None
    return str(content).strip()


def chat_completion_stream(messages: list[dict], temperature: float = 0.2, max_tokens: int = 1024):
    cfg = get_runtime_config()
    api_key = cfg.get('llm_api_key', '')
    model_name = cfg.get('llm_model_name', '')
    base_url = cfg.get('llm_api_base_url', settings.llm_api_base_url)

    if not (api_key and model_name):
        return

    url = f"{_normalize_base_url(base_url)}/v1/chat/completions"
    headers = {
        'Authorization': f"Bearer {api_key}",
        'Content-Type': 'application/json',
    }
    payload: dict[str, Any] = {
        'model': model_name,
        'messages': messages,
        'temperature': temperature,
        'max_tokens': max_tokens,
        'stream': True,
    }

    try:
        with httpx.stream('POST', url, json=payload, headers=headers, timeout=120) as response:
            response.raise_for_status()
            for line in response.iter_lines():
                if not line:
                    continue
                if isinstance(line, bytes):
                    line = line.decode('utf-8', errors='ignore')
                line = str(line).strip()
                if not line.startswith('data:'):
                    continue
                data = line[5:].strip()
                if data == '[DONE]':
                    break
                try:
                    obj = json.loads(data)
                except json.JSONDecodeError:
                    continue

                choices = obj.get('choices') or []
                if not choices:
                    continue
                delta = choices[0].get('delta') or {}
                reasoning = delta.get('reasoning_content') or delta.get('reasoning')
                if reasoning:
                    yield {'type': 'reasoning', 'content': str(reasoning)}
                content = delta.get('content')
                if content:
                    yield {'type': 'content', 'content': str(content)}
    except Exception:
        return
