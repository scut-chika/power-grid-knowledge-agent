from src.knowledge_base.pipeline import KnowledgeBuildPipeline


def test_build_pipeline_runs():
    report = KnowledgeBuildPipeline().run(mode='incremental')
    assert 'processed_files' in report
