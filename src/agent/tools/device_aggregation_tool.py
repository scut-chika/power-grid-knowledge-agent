def run(query: str, retrieval: dict) -> dict:
    names = retrieval.get('parsed', {}).get('entities', [])
    return {
        'device': names[0] if names else '未识别设备',
        'summary': '已聚合设备的台账、定值、文档、图纸信息（基于当前检索结果）。',
        'references': retrieval.get('results', []),
    }
