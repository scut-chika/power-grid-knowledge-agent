from pathlib import Path
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException

from src.backend.core.config import settings
from src.backend.core.db import update_config
from src.backend.core.env_sync import sync_config_items_to_env_file
from src.backend.core.runtime_config import get_merged_config_for_api, get_runtime_config
from src.backend.core.security import get_current_user, require_admin
from src.backend.schemas.system import ConfigUpdateRequest
from src.knowledge_base.graph_builder.neo4j_writer import verify_connectivity as neo4j_verify

router = APIRouter()


@router.get('/config/smoke')
def config_smoke() -> dict:
    """
    仅 DEBUG=true 时可匿名访问：确认进程已合并读取 .env + 数据库（不返回任何密钥明文）。
    正式环境关闭 DEBUG 后此接口返回 404。
    """
    if not settings.debug:
        raise HTTPException(status_code=404, detail='Not found')
    cfg = get_merged_config_for_api()
    return {
        'code': 0,
        'message': 'ok',
        'data': {
            'llm_api_base_url': cfg.get('llm_api_base_url', ''),
            'llm_model_name': cfg.get('llm_model_name', ''),
            'llm_key_configured': bool((cfg.get('llm_api_key') or '').strip()),
            'embedding_model_name': cfg.get('embedding_model_name', ''),
            'embedding_key_configured': bool((cfg.get('embedding_api_key') or '').strip()),
            'reranker_model_name': cfg.get('reranker_model_name', ''),
            'retrieve_top_n': cfg.get('retrieve_top_n', ''),
            'rerank_top_n': cfg.get('rerank_top_n', ''),
        },
    }


@router.get('/config')
def get_config(_: Annotated[dict, Depends(require_admin)]) -> dict:
    data = get_merged_config_for_api()
    return {'code': 0, 'message': 'ok', 'data': data}


@router.post('/config')
def update_system_config(req: ConfigUpdateRequest, _: Annotated[dict, Depends(require_admin)]) -> dict:
    normalized: dict[str, str] = {str(k): '' if v is None else str(v) for k, v in req.items.items()}
    update_config(normalized)
    merged = get_merged_config_for_api()
    try:
        sync_config_items_to_env_file(normalized)
    except OSError as e:
        return {'code': 0, 'message': f'已写入数据库，但更新 .env 失败：{e}', 'data': merged}
    return {'code': 0, 'message': 'ok', 'data': merged}


@router.get('/status')
def system_status(_: Annotated[dict, Depends(get_current_user)]) -> dict:
    sqlite_ok = Path(settings.sqlite_db_path).exists()
    cfg = get_runtime_config()
    llm_ok = bool(cfg.get('llm_api_key') and cfg.get('llm_model_name'))
    emb_ok = bool(cfg.get('embedding_api_key') and cfg.get('embedding_model_name'))
    rerank_ok = bool(cfg.get('reranker_api_key') and cfg.get('reranker_model_name'))
    return {
        'code': 0,
        'message': 'ok',
        'data': {
            'sqlite': 'connected' if sqlite_ok else 'not_found',
            'neo4j': 'connected' if neo4j_verify() else 'unavailable',
            'zvec': 'ready',
            'llm': 'configured' if llm_ok else 'pending',
            'embedding': 'configured' if emb_ok else 'pending',
            'reranker': 'configured' if rerank_ok else 'pending',
            'knowledge_base': 'ready',
        },
    }
