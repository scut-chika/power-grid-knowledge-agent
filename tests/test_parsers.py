from src.knowledge_base.preprocess.parsers import chunk_document_units, split_chunks


def test_chunking_preserves_provenance():
    units = [{'text': '保护动作逻辑。' * 120, 'metadata': {'page_number': 7, 'section': '动作逻辑'}}]

    chunks = chunk_document_units(units, chunk_size=200, overlap=20)

    assert len(chunks) > 1
    assert all(chunk['metadata']['page_number'] == 7 for chunk in chunks)
    assert all(chunk['metadata']['section'] == '动作逻辑' for chunk in chunks)


def test_split_chunks_rejects_too_small_window():
    try:
        split_chunks('text', chunk_size=20)
    except ValueError as exc:
        assert 'chunk_size' in str(exc)
    else:
        raise AssertionError('expected ValueError')
