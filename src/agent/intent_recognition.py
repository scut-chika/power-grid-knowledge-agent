def recognize_intent(parsed_query: dict) -> dict:
    mapping = {
        '设备信息查询': 'aggregation',
        '定值查询': 'qa',
        '运维规程查询': 'qa',
        '故障处置查询': 'scenario',
        '图纸文档查询': 'graph',
        '通用知识咨询': 'qa',
    }
    query_intent = parsed_query.get('intent', '通用知识咨询')
    return {
        'intent': query_intent,
        'intent_group': mapping.get(query_intent, 'qa'),
        'priority': 1,
    }
