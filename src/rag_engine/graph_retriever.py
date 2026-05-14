"""图谱召回：基于实体名在 Neo4j 中匹配实体并返回参考片段。

Neo4j 不可用时回退到本地占位结果，使主链路始终可用。
"""
from __future__ import annotations

from src.knowledge_base.graph_builder.neo4j_writer import match_entities_by_name


def _fallback(entities: list[str]) -> list[dict]:
    return [
        {
            'content': f"图谱命中实体：{e}",
            'metadata': {'entity': e, 'source': 'knowledge_graph'},
            'score': 0.6,
            'source': 'knowledge_graph_fallback',
        }
        for e in entities[:5]
    ]


def retrieve_by_graph(parsed_query: dict) -> list[dict]:
    entities: list[str] = parsed_query.get('entities', []) or []
    if not entities:
        return []

    matched = match_entities_by_name(entities, top_k=5)
    if not matched:
        return _fallback(entities)

    results: list[dict] = []
    for ent in matched:
        name = ent.get('name', '')
        etype = ent.get('type', '')
        results.append(
            {
                'content': f"图谱命中实体：{name}（类型：{etype}）",
                'metadata': {
                    'entity_id': ent.get('id', ''),
                    'entity': name,
                    'type': etype,
                    'source': 'knowledge_graph',
                },
                'score': 0.75,
                'source': 'knowledge_graph',
            }
        )
    return results
