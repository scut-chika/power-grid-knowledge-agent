"""Deterministic retrieval metrics for an annotated JSONL dataset."""
from __future__ import annotations

from statistics import fmean
from typing import Callable


def _identity(result: dict, use_chunk_ids: bool) -> str:
    metadata = result.get('metadata') or {}
    if use_chunk_ids:
        return str(metadata.get('chunk_id') or '')
    return str(result.get('source') or metadata.get('file_name') or '')


def evaluate_retrieval_cases(
    cases: list[dict],
    search: Callable[[str], list[dict]],
    k: int = 10,
) -> dict:
    """Compute Recall@k, HitRate@k and MRR for labelled retrieval cases."""
    if k < 1:
        raise ValueError('k must be positive')

    per_case = []
    for case in cases:
        gold_chunk_ids = {str(value) for value in case.get('gold_chunk_ids') or []}
        gold_sources = {str(value) for value in case.get('gold_sources') or []}
        use_chunk_ids = bool(gold_chunk_ids)
        gold = gold_chunk_ids or gold_sources
        if not gold:
            raise ValueError(f"case {case.get('id', '<unknown>')} has no gold labels")

        results = search(str(case['query']))[:k]
        predicted = [_identity(result, use_chunk_ids) for result in results]
        hits = [rank for rank, identity in enumerate(predicted, start=1) if identity in gold]
        matched = set(predicted) & gold
        recall = len(matched) / len(gold)
        reciprocal_rank = 1 / hits[0] if hits else 0.0
        per_case.append(
            {
                'id': case.get('id'),
                'query': case['query'],
                f'recall@{k}': recall,
                f'hit_rate@{k}': 1.0 if hits else 0.0,
                'reciprocal_rank': reciprocal_rank,
                'matched': sorted(matched),
                'predicted': predicted,
            }
        )

    recall_key = f'recall@{k}'
    hit_rate_key = f'hit_rate@{k}'
    summary = {
        'case_count': len(per_case),
        recall_key: fmean(item[recall_key] for item in per_case) if per_case else 0.0,
        hit_rate_key: fmean(item[hit_rate_key] for item in per_case) if per_case else 0.0,
        'mrr': fmean(item['reciprocal_rank'] for item in per_case) if per_case else 0.0,
    }
    return {'summary': summary, 'cases': per_case}
