from src.rag_engine import engine
from src.rag_engine.fusion import reciprocal_rank_fusion


def _result(chunk_id: str, score: float, source: str = 'manual.pdf') -> dict:
    return {
        'content': f'content-{chunk_id}',
        'metadata': {'chunk_id': chunk_id, 'file_name': source},
        'source': source,
        'score': score,
    }


def test_rrf_merges_duplicate_chunks_and_records_channels():
    fused = reciprocal_rank_fusion(
        {
            'dense': [_result('a', 0.9), _result('b', 0.8)],
            'sparse': [_result('b', 1.0), _result('a', 0.7)],
            'graph': [],
        }
    )

    assert [item['metadata']['chunk_id'] for item in fused] == ['a', 'b']
    assert set(fused[0]['retrieval_channels']) == {'dense', 'sparse'}
    assert fused[0]['score'] == 1.0


def test_hybrid_engine_isolates_channel_failure_and_reports_latency(monkeypatch):
    def fail_dense(_: str) -> list[dict]:
        raise RuntimeError('dense unavailable')

    monkeypatch.setattr(engine, 'retrieve_by_vector', fail_dense)
    monkeypatch.setattr(
        engine,
        'retrieve_by_sparse',
        lambda _: [_result('sparse-hit', 1.0, source='规程.pdf')],
    )
    monkeypatch.setattr(engine, 'retrieve_by_graph', lambda _: [])
    monkeypatch.setattr(
        engine,
        'rerank',
        lambda query, results, top_n, threshold: results[:top_n],
    )

    output = engine.run_hybrid_retrieval('保护规程')

    assert output['results'][0]['source'] == '规程.pdf'
    assert 'dense' in output['retrieval']['errors']
    assert output['retrieval']['latency_ms']['total'] >= 0
    assert set(output['retrieval']['latency_ms']) == {
        'dense',
        'sparse',
        'graph',
        'fusion',
        'rerank',
        'context',
        'total',
    }
