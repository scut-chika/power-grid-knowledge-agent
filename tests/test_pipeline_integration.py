from src.knowledge_base.pipeline import KnowledgeBuildPipeline
from src.rag_engine.engine import run_hybrid_retrieval


def test_full_pipeline_builds_hybrid_indexes_and_skips_unchanged_rebuild(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    document_dir = tmp_path / 'data' / 'raw' / 'documents'
    document_dir.mkdir(parents=True)
    (document_dir / '华南站-保护规程-PCS931.txt').write_text(
        '# PCS-931线路保护装置\nPCS-931线路保护装置支持距离保护和零序保护。\n'
        '发生保护动作后，应先核对告警信息与故障录波。',
        encoding='utf-8',
    )

    first_report = KnowledgeBuildPipeline().run(mode='full')
    retrieval = run_hybrid_retrieval('PCS-931距离保护')
    second_report = KnowledgeBuildPipeline().run(mode='incremental')

    assert first_report['chunk_count'] >= 1
    assert first_report['sparse']['document_count'] >= 1
    assert retrieval['retrieval']['sparse_count'] >= 1
    assert retrieval['results'][0]['source'] == '华南站-保护规程-PCS931.txt'
    assert 'sparse' in retrieval['results'][0]['retrieval_channels']
    assert second_report['rebuild_performed'] is False
