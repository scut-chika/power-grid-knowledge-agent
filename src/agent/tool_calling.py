from src.agent.tools import device_aggregation_tool, graph_tool, knowledge_tool, scenario_tool


def call_tool(tool: str, query: str, context: dict | None = None) -> dict:
    context = context or {}
    if tool == 'knowledge_retrieval':
        return knowledge_tool.run(query)
    if tool == 'graph_query':
        return graph_tool.run(query)
    if tool == 'device_aggregation':
        return device_aggregation_tool.run(query, context.get('retrieval', {}))
    if tool == 'scenario_template':
        return scenario_tool.run(query, context.get('retrieval', {}))
    return {'error': f'未知工具：{tool}'}
