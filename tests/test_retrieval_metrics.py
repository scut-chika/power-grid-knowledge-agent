from src.evaluation.retrieval_metrics import evaluate_retrieval_cases


def test_retrieval_metrics_compute_recall_and_mrr():
    cases = [{'id': 'q1', 'query': 'query', 'gold_chunk_ids': ['gold-a', 'gold-b']}]

    def search(_: str) -> list[dict]:
        return [
            {'metadata': {'chunk_id': 'noise'}},
            {'metadata': {'chunk_id': 'gold-a'}},
        ]

    report = evaluate_retrieval_cases(cases, search=search, k=2)

    assert report['summary']['recall@2'] == 0.5
    assert report['summary']['hit_rate@2'] == 1.0
    assert report['summary']['mrr'] == 0.5
