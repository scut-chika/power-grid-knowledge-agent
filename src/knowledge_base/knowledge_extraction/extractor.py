"""Deterministic baseline entity and relation extraction.

This module intentionally identifies itself as a rule-based baseline. It creates
stable, auditable graph data without claiming LLM extraction capabilities.
"""
from __future__ import annotations

import hashlib
import re

ENTITY_TYPES = ['厂站', '间隔', '二次设备', '装置', '定值项', '技术文档', '运维规程', '图纸', '厂家']

_DOMAIN_SUFFIX_TYPES = {
    '变电站': '厂站',
    '线路': '间隔',
    '母线': '间隔',
    '主变': '二次设备',
    '保护装置': '装置',
    '装置': '装置',
    '断路器': '二次设备',
    '开关': '二次设备',
    '间隔': '间隔',
}
_ENTITY_PATTERN = re.compile(
    r'(?:[A-Za-z0-9#\-]{2,30}|[\u4e00-\u9fff]{2,12})'
    r'(?:变电站|线路|母线|主变|保护装置|装置|断路器|开关|间隔)'
)
_SETTING_PATTERN = re.compile(
    r'(?:[A-Za-z0-9#\-]{2,30}|[\u4e00-\u9fff]{2,12})'
    r'(?:定值|整定值)'
)


def _entity_id(name: str, entity_type: str) -> str:
    normalized = re.sub(r'\s+', '', name).lower()
    digest = hashlib.sha256(f'{entity_type}:{normalized}'.encode('utf-8')).hexdigest()[:16]
    return f'ent-{digest}'


def _make_entity(name: str, entity_type: str, source_file: str = '') -> dict:
    clean_name = re.sub(r'\s+', ' ', name).strip('，。；：:、 ')
    return {
        'id': _entity_id(clean_name, entity_type),
        'name': clean_name,
        'type': entity_type,
        'source_file': source_file,
    }


def extract_entities(text: str, metadata: dict) -> list[dict]:
    """Extract a conservative set of domain entities with traceable sources."""
    source_file = str(metadata.get('file_name') or '')
    entities: list[dict] = []

    station = str(metadata.get('station_name') or '').strip()
    if station:
        station_name = station if station.endswith('变电站') else f'{station}变电站'
        entities.append(_make_entity(station_name, '厂站', source_file))

    if source_file:
        category = str(metadata.get('category') or '')
        document_type = '运维规程' if '规程' in category or '规程' in source_file else '技术文档'
        if any(keyword in source_file for keyword in ('图纸', '接线图', '原理图')):
            document_type = '图纸'
        entities.append(_make_entity(source_file, document_type, source_file))

    for name in _ENTITY_PATTERN.findall(text):
        entity_type = next(
            (value for suffix, value in _DOMAIN_SUFFIX_TYPES.items() if name.endswith(suffix)),
            '二次设备',
        )
        entities.append(_make_entity(name, entity_type, source_file))

    for name in _SETTING_PATTERN.findall(text):
        entities.append(_make_entity(name, '定值项', source_file))

    unique = {(entity['id'], entity['type']): entity for entity in entities if entity['name']}
    return list(unique.values())


def extract_relations(entities: list[dict]) -> list[dict]:
    """Build deterministic document and station relationships."""
    relations: list[dict] = []
    stations = [entity for entity in entities if entity['type'] == '厂站']
    documents = [entity for entity in entities if entity['type'] in {'技术文档', '运维规程', '图纸'}]
    domain_entities = [entity for entity in entities if entity not in stations and entity not in documents]

    for station in stations:
        for entity in domain_entities:
            relations.append({'head': station['id'], 'relation': 'CONTAINS', 'tail': entity['id']})
    for document in documents:
        for entity in stations + domain_entities:
            relations.append({'head': document['id'], 'relation': 'MENTIONS', 'tail': entity['id']})

    unique = {(relation['head'], relation['relation'], relation['tail']): relation for relation in relations}
    return list(unique.values())


# Backward-compatible aliases for older imports. New code uses the explicit names.
fake_extract_entities = extract_entities
fake_extract_relations = extract_relations
