def make_plan(intent_info: dict) -> list[dict]:
    group = intent_info.get('intent_group', 'qa')
    if group == 'aggregation':
        return [
            {'tool': 'knowledge_retrieval', 'desc': '检索设备相关知识'},
            {'tool': 'device_aggregation', 'desc': '聚合设备全量信息'},
        ]
    if group == 'graph':
        return [
            {'tool': 'graph_query', 'desc': '查询实体关系'},
        ]
    if group == 'scenario':
        return [
            {'tool': 'knowledge_retrieval', 'desc': '检索场景相关知识'},
            {'tool': 'scenario_template', 'desc': '生成场景化输出'},
        ]
    return [{'tool': 'knowledge_retrieval', 'desc': '执行混合检索'}]
