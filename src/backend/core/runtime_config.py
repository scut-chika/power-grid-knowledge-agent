from src.backend.core.config import settings


def _env_defaults() -> dict[str, str]:
    return {
        'llm_api_base_url': settings.llm_api_base_url or '',
        'llm_api_key': settings.llm_api_key or '',
        'llm_model_name': settings.llm_model_name or '',
        'embedding_provider': settings.embedding_provider or '',
        'embedding_api_base_url': settings.embedding_api_base_url or '',
        'embedding_api_key': settings.embedding_api_key or '',
        'embedding_model_name': settings.embedding_model_name or '',
        'reranker_provider': settings.reranker_provider or '',
        'reranker_api_base_url': settings.reranker_api_base_url or '',
        'reranker_api_key': settings.reranker_api_key or '',
        'reranker_model_name': settings.reranker_model_name or '',
        'retrieve_top_n': str(settings.retrieve_top_n),
        'rerank_top_n': str(settings.rerank_top_n),
        'similarity_threshold': str(settings.similarity_threshold),
    }


def _merge_db_over_defaults(db_cfg: dict[str, str], defaults: dict[str, str]) -> dict[str, str]:
    """
    非空的数据库值覆盖默认（环境变量）；空字符串视为“未填写”，继续用环境变量。
    这样首次初始化写入的空占位不会挡住后续 .env。
    """
    merged = dict(defaults)
    for k, v in db_cfg.items():
        if k not in merged:
            merged[k] = str(v) if v is not None else ''
            continue
        if v is None:
            continue
        s = str(v).strip()
        if s != '':
            merged[k] = str(v)
    return merged


def get_runtime_config() -> dict[str, str]:
    """
    运行时配置：环境变量/Settings 为底，数据库中的非空项覆盖。
    """
    defaults = _env_defaults()
    try:
        from src.backend.core.db import get_all_config

        db_cfg = get_all_config()
        return _merge_db_over_defaults(db_cfg, defaults)
    except Exception:
        return defaults


def get_merged_config_for_api() -> dict[str, str]:
    """
    供 GET /config 与前端表单使用，与 get_runtime_config 一致。
    """
    return get_runtime_config()
