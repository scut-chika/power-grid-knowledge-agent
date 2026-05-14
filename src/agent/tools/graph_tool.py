def run(query: str) -> dict:
    return {
        'items': [
            {'content': f'图谱查询结果（示例）：{query}', 'source': 'knowledge_graph', 'score': 0.8}
        ]
    }
