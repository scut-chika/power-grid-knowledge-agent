def run(query: str, retrieval: dict) -> dict:
    return {
        'template': '运维场景标准化模板',
        'steps': [
            '确认设备与厂站信息',
            '核查规程与定值',
            '执行现场处置并复核',
        ],
        'references': retrieval.get('results', []),
        'query': query,
    }
