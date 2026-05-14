import threading
import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query

from src.backend.core.db import get_build_task, upsert_build_task
from src.backend.core.security import get_current_user
from src.backend.schemas.knowledge import BuildRequest
from src.knowledge_base.graph_builder.neo4j_writer import query_graph
from src.knowledge_base.pipeline import KnowledgeBuildPipeline

router = APIRouter()


def _run_build_task(task_id: str, mode: str) -> None:
    upsert_build_task(task_id, mode, 'running', 10, '开始执行知识库构建...', None)
    try:
        pipeline = KnowledgeBuildPipeline()
        upsert_build_task(task_id, mode, 'running', 50, '处理中...', None)
        report = pipeline.run(mode=mode)
        upsert_build_task(task_id, mode, 'finished', 100, '构建完成', report)
    except Exception as exc:  # noqa: BLE001
        upsert_build_task(task_id, mode, 'failed', 100, f'构建失败: {exc}', None)


@router.post('/build')
def build_knowledge(
    req: BuildRequest,
    user: Annotated[dict, Depends(get_current_user)] = None,
) -> dict:
    if req.build_type == 'full' and user.get('role') != 'admin':
        raise HTTPException(status_code=403, detail='全量构建需要管理员权限')
    mode = 'full' if req.build_type == 'full' else 'incremental'
    task_id = str(uuid.uuid4())
    upsert_build_task(task_id, mode, 'queued', 0, '任务已创建', None)

    thread = threading.Thread(target=_run_build_task, args=(task_id, mode), daemon=True)
    thread.start()

    return {'code': 0, 'message': 'ok', 'data': {'task_id': task_id, 'status': 'queued'}}


@router.get('/status')
def build_status(
    task_id: str = Query(...),
    _: Annotated[dict, Depends(get_current_user)] = None,
) -> dict:
    task = get_build_task(task_id)
    if not task:
        raise HTTPException(status_code=404, detail='任务不存在')
    return {'code': 0, 'message': 'ok', 'data': task}


_DEMO_GRAPH = {
    'nodes': [
        {'id': 'station-1', 'name': '南山变电站', 'type': '厂站'},
        {'id': 'device-1', 'name': 'PCS-931线路保护装置', 'type': '二次设备'},
    ],
    'links': [{'source': 'station-1', 'target': 'device-1', 'relation': '包含'}],
}


@router.get('/graph')
def graph_data(
    entity_id: str | None = Query(default=None),
    depth: int = Query(default=1, ge=1, le=5),
    _: Annotated[dict, Depends(get_current_user)] = None,
) -> dict:
    result = query_graph(entity_id=entity_id, depth=depth)
    if result.get('source') == 'neo4j' and result.get('nodes'):
        return {
            'code': 0,
            'message': 'ok',
            'data': {
                'nodes': result['nodes'],
                'links': result['links'],
                'depth': result['depth'],
                'source': 'neo4j',
            },
        }

    nodes = _DEMO_GRAPH['nodes']
    links = _DEMO_GRAPH['links']
    if entity_id:
        nodes = [n for n in nodes if n['id'] == entity_id] or nodes
    return {
        'code': 0,
        'message': 'ok',
        'data': {
            'nodes': nodes,
            'links': links,
            'depth': depth,
            'source': result.get('source', 'fallback'),
            'fallback': True,
            'reason': result.get('reason'),
        },
    }
