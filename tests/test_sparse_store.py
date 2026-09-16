from src.backend.core.config import settings
from src.knowledge_base.sparse_store.bm25_store import (
    _load_runtime_index,
    build_sparse_index,
    query_sparse,
    tokenize,
)


def test_chinese_tokenizer_produces_bigrams():
    tokens = tokenize('线路保护装置 PCS-931')
    assert '线路' in tokens
    assert 'pcs-931' in tokens


def test_bm25_index_prefers_matching_document(tmp_path, monkeypatch):
    monkeypatch.setattr(settings, 'sparse_index_path', str(tmp_path / 'bm25.json'))
    build_sparse_index(
        [
            {
                'chunk_id': 'ck-protection',
                'text': 'PCS-931线路保护装置支持距离保护和零序保护。',
                'metadata': {'file_name': '保护说明书.pdf'},
            },
            {
                'chunk_id': 'ck-inspection',
                'text': '变电站日常巡检应检查环境温度。',
                'metadata': {'file_name': '巡检规程.pdf'},
            },
        ]
    )

    results = query_sparse('PCS-931距离保护', top_n=2)

    assert results[0]['metadata']['chunk_id'] == 'ck-protection'
    assert results[0]['retrieval_channel'] == 'sparse'
    assert _load_runtime_index() is _load_runtime_index()
