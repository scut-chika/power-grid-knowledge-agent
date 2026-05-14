"""Sync UI-managed config keys to project root .env (Pydantic-compatible names)."""

from __future__ import annotations

import re
from pathlib import Path

from src.backend.core.logger import get_logger

logger = get_logger(__name__)

# Form / DB keys -> environment variable names (Pydantic Settings default)
CONFIG_KEY_TO_ENV_VAR: dict[str, str] = {
    'llm_api_base_url': 'LLM_API_BASE_URL',
    'llm_api_key': 'LLM_API_KEY',
    'llm_model_name': 'LLM_MODEL_NAME',
    'embedding_provider': 'EMBEDDING_PROVIDER',
    'embedding_api_base_url': 'EMBEDDING_API_BASE_URL',
    'embedding_api_key': 'EMBEDDING_API_KEY',
    'embedding_model_name': 'EMBEDDING_MODEL_NAME',
    'reranker_provider': 'RERANKER_PROVIDER',
    'reranker_api_base_url': 'RERANKER_API_BASE_URL',
    'reranker_api_key': 'RERANKER_API_KEY',
    'reranker_model_name': 'RERANKER_MODEL_NAME',
    'retrieve_top_n': 'RETRIEVE_TOP_N',
    'rerank_top_n': 'RERANK_TOP_N',
    'similarity_threshold': 'SIMILARITY_THRESHOLD',
}


def _project_root() -> Path:
    # src/backend/core/env_sync.py -> parents[3] = repository root
    return Path(__file__).resolve().parents[3]


def _env_path() -> Path:
    return _project_root() / '.env'


def _escape_env_value(val: str) -> str:
    if val == '':
        return '""'
    if re.search(r'[\s#"\'\\]', val):
        escaped = val.replace('\\', '\\\\').replace('"', '\\"')
        return f'"{escaped}"'
    return val


def sync_config_items_to_env_file(items: dict[str, str]) -> None:
    """Upsert known keys into .env; preserve other lines and comments."""
    path = _env_path()
    env_map: dict[str, str] = {}
    for k, v in items.items():
        env_key = CONFIG_KEY_TO_ENV_VAR.get(k)
        if env_key is not None:
            env_map[env_key] = v

    if not env_map:
        return

    if path.exists():
        raw = path.read_text(encoding='utf-8')
        lines = raw.splitlines(keepends=True)
        if not lines and raw:
            lines = [raw]
    else:
        lines = []

    seen: set[str] = set()
    new_lines: list[str] = []

    for line in lines:
        stripped = line.strip()
        if stripped and not stripped.startswith('#') and '=' in stripped:
            key = stripped.split('=', 1)[0].strip()
            if key in env_map:
                nl = '\n' if line.endswith('\n') else ''
                new_lines.append(f'{key}={_escape_env_value(env_map[key])}{nl}')
                seen.add(key)
                continue
        new_lines.append(line if line.endswith('\n') or line == '' else line + '\n')

    for env_key, val in env_map.items():
        if env_key not in seen:
            new_lines.append(f'{env_key}={_escape_env_value(val)}\n')

    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(''.join(new_lines), encoding='utf-8')
    logger.info('已同步 %s 项配置到 %s', len(env_map), path)
