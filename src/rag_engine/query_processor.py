import re

INTENT_MAP = {
    '定值': '定值查询',
    '规程': '运维规程查询',
    '故障': '故障处置查询',
    '图纸': '图纸文档查询',
    '设备': '设备信息查询',
}

DOMAIN_ENTITY_PATTERNS = [
    re.compile(r'[\u4e00-\u9fff]{2,12}变电站'),
    re.compile(r'[#0-9一二三四五六七八九十]{1,5}号?主变'),
    re.compile(r'\d+(?:kV|KV|千伏)?[\u4e00-\u9fffA-Za-z0-9#\-]{0,12}(?:线路|母线|间隔|断路器|开关)'),
]
MODEL_ENTITY_PATTERN = re.compile(
    r'[A-Za-z]{2,10}[\-#]?\d[A-Za-z0-9\-]{0,24}(?:线路保护装置|保护装置|装置)?'
)
ENTITY_PREFIX_PATTERN = re.compile(r'^(?:请查询|查询|请问|关于|帮我查|查一下|核对)')


def _clean_entity(entity: str) -> str:
    return ENTITY_PREFIX_PATTERN.sub('', entity).strip('，。；：:、 的')


def preprocess_query(query: str) -> dict:
    query = query.strip()
    q_norm = re.sub(r'\s+', ' ', query)
    intent = '通用知识咨询'
    for k, v in INTENT_MAP.items():
        if k in q_norm:
            intent = v
            break

    domain_entities = [
        _clean_entity(entity)
        for pattern in DOMAIN_ENTITY_PATTERNS
        for entity in pattern.findall(q_norm)
    ]
    model_entities = MODEL_ENTITY_PATTERN.findall(q_norm)
    quoted_entities = re.findall(r'[「“\"]([^」”\"]{2,30})[」”\"]', q_norm)
    entities = list(dict.fromkeys(entity for entity in domain_entities + model_entities + quoted_entities if entity))
    return {
        'normalized_query': q_norm,
        'intent': intent,
        'entities': entities,
        'sub_queries': [q_norm],
    }
