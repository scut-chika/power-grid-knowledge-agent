"""Graph retrieval backed by real Neo4j entity neighborhoods."""
from __future__ import annotations

from src.knowledge_base.graph_builder.neo4j_writer import match_entity_neighborhood


def retrieve_by_graph(parsed_query: dict) -> list[dict]:
    entities: list[str] = parsed_query.get('entities', []) or []
    if not entities:
        return []

    matched = match_entity_neighborhood(entities, top_k=5)

    results: list[dict] = []
    for ent in matched:
        name = ent.get('name', '')
        etype = ent.get('type', '')
        neighbors = [n for n in (ent.get('neighbors') or []) if n.get('name')]
        relation_text = '；'.join(
            f"{n.get('relation') or '关联'} → {n.get('name')}（{n.get('type') or '实体'}）"
            for n in neighbors
        )
        content = f"图谱实体：{name}（{etype}）"
        if relation_text:
            content = f'{content}；一跳关系：{relation_text}'
        source_file = ent.get('source_file') or 'knowledge_graph'
        results.append(
            {
                'content': content,
                'metadata': {
                    'entity_id': ent.get('id', ''),
                    'entity': name,
                    'type': etype,
                    'source': 'knowledge_graph',
                    'source_file': ent.get('source_file', ''),
                    'neighbors': neighbors,
                },
                'score': 0.75,
                'source': source_file,
                'retrieval_channel': 'graph',
            }
        )
    return results
