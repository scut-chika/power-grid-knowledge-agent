from src.rag_engine.query_processor import preprocess_query


def test_query_processor_extracts_model_without_swallowing_question():
    parsed = preprocess_query('请查询PCS-931线路保护装置的距离保护定值')

    assert parsed['intent'] == '定值查询'
    assert 'PCS-931线路保护装置' in parsed['entities']
    assert all(not entity.startswith('请查询') for entity in parsed['entities'])


def test_query_processor_extracts_station_name():
    parsed = preprocess_query('请查询南山变电站的运维规程')

    assert '南山变电站' in parsed['entities']
