from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from src.backend.api.auth_api import router as auth_router
from src.backend.api.chat_api import router as chat_router
from src.backend.api.data_api import router as data_router
from src.backend.api.knowledge_api import router as knowledge_router
from src.backend.api.system_api import router as system_router
from src.backend.core.config import settings
from src.backend.core.db import init_db
from src.backend.core.logger import get_logger
from src.backend.core.runtime_config import get_merged_config_for_api

logger = get_logger(__name__)

app = FastAPI(title=settings.system_name, version=settings.system_version)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=['*'],
    allow_headers=['*'],
)


@app.on_event('startup')
def startup_event() -> None:
    init_db()
    try:
        cfg = get_merged_config_for_api()
        logger.info(
            '运行时模型配置（不含密钥）: llm_model=%s, embedding=%s, reranker=%s',
            cfg.get('llm_model_name', '') or '(空)',
            cfg.get('embedding_model_name', '') or '(空)',
            cfg.get('reranker_model_name', '') or '(空)',
        )
    except Exception as exc:  # noqa: BLE001
        logger.warning('启动时读取合并配置失败: %s', exc)


@app.get('/health')
def health() -> dict:
    return {'status': 'ok'}


app.include_router(auth_router, prefix='/api/auth', tags=['auth'])
app.include_router(data_router, prefix='/api/data', tags=['data'])
app.include_router(knowledge_router, prefix='/api/knowledge', tags=['knowledge'])
app.include_router(chat_router, prefix='/api/chat', tags=['chat'])
app.include_router(system_router, prefix='/api/system', tags=['system'])
