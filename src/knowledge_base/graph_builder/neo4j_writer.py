"""Neo4j 图数据库读写封装。

驱动连不上时自动降级到模拟实现，保证主链路（知识入库 / 检索 / Web）不中断。
"""
from __future__ import annotations

import threading
from typing import Any

from src.backend.core.config import settings
from src.backend.core.logger import get_logger

logger = get_logger(__name__)


_driver = None
_driver_lock = threading.Lock()
_driver_unavailable = False


class Neo4jUnavailable(RuntimeError):
    """Neo4j 不可用（驱动未安装、连接失败、鉴权失败等）。"""


def _get_driver():
    """单例获取 GraphDatabase driver。失败抛 Neo4jUnavailable。"""
    global _driver, _driver_unavailable

    if _driver is not None:
        return _driver
    if _driver_unavailable:
        raise Neo4jUnavailable('Neo4j 此前已标记不可用')

    with _driver_lock:
        if _driver is not None:
            return _driver
        try:
            from neo4j import GraphDatabase
        except ImportError as exc:
            _driver_unavailable = True
            raise Neo4jUnavailable(f'neo4j 驱动未安装: {exc}') from exc

        try:
            drv = GraphDatabase.driver(
                settings.neo4j_uri,
                auth=(settings.neo4j_username, settings.neo4j_password),
                connection_timeout=2.0,
            )
            drv.verify_connectivity()
        except Exception as exc:  # noqa: BLE001
            _driver_unavailable = True
            raise Neo4jUnavailable(f'Neo4j 连接失败: {exc}') from exc

        _driver = drv
        logger.info('Neo4j driver 已建立: %s', settings.neo4j_uri)
        return _driver


def _session():
    drv = _get_driver()
    return drv.session(database=settings.neo4j_database) if settings.neo4j_database else drv.session()


def verify_connectivity(timeout: float = 1.0) -> bool:
    """供 /api/system/status 探活使用。"""
    try:
        _get_driver().verify_connectivity()
        return True
    except Exception:  # noqa: BLE001
        return False


# ---------------------- 写入 ----------------------

def build_graph(entities: list[dict], relations: list[dict], mode: str = 'incremental') -> dict:
    """把实体与关系写入 Neo4j。失败时返回 simulated 状态，不抛异常。"""
    if not entities and not relations:
        return {'entity_count': 0, 'relation_count': 0, 'status': 'empty'}

    try:
        with _session() as sess:
            if mode == 'full':
                sess.run('MATCH (n) DETACH DELETE n')

            if entities:
                rows = [{'id': e['id'], 'name': e.get('name', ''), 'type': e.get('type', '')} for e in entities]
                sess.run(
                    'UNWIND $rows AS row '
                    'MERGE (e:Entity {id: row.id}) '
                    'SET e.name = row.name, e.type = row.type',
                    rows=rows,
                )

            if relations:
                rrows = [
                    {'head': r['head'], 'tail': r['tail'], 'relation': r.get('relation', 'REL')}
                    for r in relations
                ]
                sess.run(
                    'UNWIND $rows AS r '
                    'MATCH (h:Entity {id: r.head}), (t:Entity {id: r.tail}) '
                    'MERGE (h)-[rel:REL {type: r.relation}]->(t)',
                    rows=rrows,
                )

        return {
            'entity_count': len(entities),
            'relation_count': len(relations),
            'status': 'neo4j',
            'mode': mode,
            'database': settings.neo4j_database,
        }
    except Neo4jUnavailable as exc:
        logger.warning('Neo4j 不可用，图谱写入回退到模拟模式: %s', exc)
        return {
            'entity_count': len(entities),
            'relation_count': len(relations),
            'status': 'simulated',
            'reason': str(exc),
        }
    except Exception as exc:  # noqa: BLE001
        logger.warning('Neo4j 写入异常，回退到模拟模式: %s', exc)
        return {
            'entity_count': len(entities),
            'relation_count': len(relations),
            'status': 'simulated',
            'reason': str(exc),
        }


# ---------------------- 检索：实体名匹配 ----------------------

def match_entities_by_name(terms: list[str], top_k: int = 5) -> list[dict[str, Any]]:
    """按实体名做包含匹配，供 RAG 图谱召回使用。失败返回空列表。"""
    if not terms:
        return []

    try:
        with _session() as sess:
            result = sess.run(
                'UNWIND $terms AS t '
                'MATCH (n:Entity) '
                'WHERE toLower(n.name) CONTAINS toLower(t) '
                'RETURN DISTINCT n.id AS id, n.name AS name, n.type AS type '
                'LIMIT $k',
                terms=list(terms),
                k=int(top_k),
            )
            return [dict(record) for record in result]
    except Neo4jUnavailable:
        return []
    except Exception as exc:  # noqa: BLE001
        logger.warning('Neo4j 实体匹配失败: %s', exc)
        return []


# ---------------------- 检索：子图查询（供前端可视化） ----------------------

def query_graph(entity_id: str | None = None, depth: int = 1, limit: int = 50) -> dict[str, Any]:
    """返回 ECharts 友好的 nodes/links 结构。失败时由调用方决定是否回退。"""
    depth = max(1, min(depth, 5))
    limit = max(1, min(limit, 500))

    try:
        with _session() as sess:
            if entity_id:
                cypher = (
                    f'MATCH path=(n:Entity {{id: $id}})-[r:REL*1..{depth}]-(m:Entity) '
                    'RETURN n, r, m LIMIT $limit'
                )
                result = sess.run(cypher, id=entity_id, limit=limit)
            else:
                cypher = (
                    'MATCH (n:Entity)-[r:REL]->(m:Entity) '
                    'RETURN n, r, m LIMIT $limit'
                )
                result = sess.run(cypher, limit=limit)

            nodes_map: dict[str, dict[str, Any]] = {}
            links: list[dict[str, Any]] = []

            for record in result:
                n_node = record.get('n')
                m_node = record.get('m')
                rels = record.get('r')
                for node in (n_node, m_node):
                    if node is None:
                        continue
                    nid = node.get('id')
                    if nid and nid not in nodes_map:
                        nodes_map[nid] = {
                            'id': nid,
                            'name': node.get('name', ''),
                            'type': node.get('type', ''),
                        }

                rel_iter = rels if isinstance(rels, list) else [rels] if rels is not None else []
                for rel in rel_iter:
                    try:
                        start_id = rel.start_node.get('id')
                        end_id = rel.end_node.get('id')
                        rel_type = rel.get('type') or rel.type
                    except AttributeError:
                        continue
                    if start_id and end_id:
                        links.append({'source': start_id, 'target': end_id, 'relation': rel_type})

            return {'nodes': list(nodes_map.values()), 'links': links, 'depth': depth, 'source': 'neo4j'}
    except Neo4jUnavailable as exc:
        return {'nodes': [], 'links': [], 'depth': depth, 'source': 'unavailable', 'reason': str(exc)}
    except Exception as exc:  # noqa: BLE001
        logger.warning('Neo4j 子图查询失败: %s', exc)
        return {'nodes': [], 'links': [], 'depth': depth, 'source': 'error', 'reason': str(exc)}
