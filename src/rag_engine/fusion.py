"""Rank fusion utilities for hybrid retrieval."""
from __future__ import annotations

import hashlib


def _result_key(item: dict) -> str:
    metadata = item.get('metadata') or {}
    chunk_id = metadata.get('chunk_id')
    if chunk_id:
        return f'chunk:{chunk_id}'
    raw = f"{item.get('source', '')}|{item.get('content', '')}"
    return f"content:{hashlib.sha1(raw.encode('utf-8')).hexdigest()}"


def reciprocal_rank_fusion(result_sets: dict[str, list[dict]], k: int = 60) -> list[dict]:
    """Fuse ranked result lists with Reciprocal Rank Fusion.

    Results representing the same chunk are merged and retain per-channel rank
    and score metadata for observability in the API and user interface.
    """
    if k < 1:
        raise ValueError('RRF k must be positive')

    merged: dict[str, dict] = {}
    for channel, results in result_sets.items():
        seen_in_channel: set[str] = set()
        for rank, item in enumerate(results, start=1):
            key = _result_key(item)
            if key in seen_in_channel:
                continue
            seen_in_channel.add(key)

            if key not in merged:
                merged[key] = {
                    **item,
                    'metadata': dict(item.get('metadata') or {}),
                    'fusion_score': 0.0,
                    'retrieval_channels': [],
                    'channel_ranks': {},
                    'channel_scores': {},
                }
            entry = merged[key]
            entry['fusion_score'] += 1.0 / (k + rank)
            entry['retrieval_channels'].append(channel)
            entry['channel_ranks'][channel] = rank
            entry['channel_scores'][channel] = float(item.get('score', 0.0))

    ranked = sorted(merged.values(), key=lambda item: item['fusion_score'], reverse=True)
    max_score = ranked[0]['fusion_score'] if ranked else 1.0
    for item in ranked:
        item['score'] = item['fusion_score'] / max_score
        item['metadata']['retrieval_channels'] = item['retrieval_channels']
    return ranked
