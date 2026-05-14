import hashlib
import re

ENTITY_TYPES = ['厂站', '间隔', '二次设备', '装置', '定值项', '技术文档', '运维规程', '图纸', '厂家']


def fake_extract_entities(text: str, metadata: dict) -> list[dict]:
    entities = []
    station = metadata.get('station_name')
    if station:
        entities.append({'id': f'ent-{hashlib.md5(station.encode()).hexdigest()[:12]}', 'name': station, 'type': '厂站'})

    for keyword, etype in [('保护', '装置'), ('定值', '定值项'), ('规程', '运维规程'), ('图', '图纸')]:
        if keyword in text:
            val = f'{etype}-{keyword}'
            entities.append({'id': f'ent-{hashlib.md5(val.encode()).hexdigest()[:12]}', 'name': val, 'type': etype})

    # 简单设备名提取示例：XXX装置
    for m in re.findall(r'[A-Za-z0-9\\-]{2,20}装置', text):
        entities.append({'id': f'ent-{hashlib.md5(m.encode()).hexdigest()[:12]}', 'name': m, 'type': '二次设备'})

    unique = {(e['id'], e['type']): e for e in entities}
    return list(unique.values())


def fake_extract_relations(entities: list[dict]) -> list[dict]:
    rels = []
    stations = [e for e in entities if e['type'] == '厂站']
    others = [e for e in entities if e['type'] != '厂站']
    for s in stations:
        for o in others:
            rels.append({'head': s['id'], 'relation': '包含', 'tail': o['id']})
    return rels
