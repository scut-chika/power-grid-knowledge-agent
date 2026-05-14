import re

INTENT_MAP = {
    '定值': '定值查询',
    '规程': '运维规程查询',
    '故障': '故障处置查询',
    '图纸': '图纸文档查询',
    '设备': '设备信息查询',
}


def preprocess_query(query: str) -> dict:
    query = query.strip()
    q_norm = re.sub(r'\s+', ' ', query)
    intent = '通用知识咨询'
    for k, v in INTENT_MAP.items():
        if k in q_norm:
            intent = v
            break

    entities = re.findall(r'[A-Za-z0-9\-]{2,30}', q_norm)
    return {
        'normalized_query': q_norm,
        'intent': intent,
        'entities': entities,
        'sub_queries': [q_norm],
    }
