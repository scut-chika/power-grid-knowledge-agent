from pathlib import Path

from pydantic import Field
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    system_name: str = '基于AI的电网运行知识图谱智能体系统'
    system_version: str = 'v1.0'
    secret_key: str = 'replace-with-random-secret'
    debug: bool = False

    llm_type: str = 'openai'
    llm_api_key: str = ''
    llm_api_base_url: str = 'https://api.siliconflow.cn'
    llm_model_name: str = ''
    local_model_path: str = './models/your-local-model'

    embedding_provider: str = 'api'
    embedding_api_base_url: str = 'https://api.siliconflow.cn'
    embedding_api_key: str = ''
    embedding_model_name: str = ''
    embedding_model_path: str = './models/bge-large-zh-v1.5'
    embedding_dimension: int = 1024

    reranker_provider: str = 'api'
    reranker_api_base_url: str = 'https://api.siliconflow.cn'
    reranker_api_key: str = ''
    reranker_model_name: str = ''
    reranker_model_path: str = './models/bge-reranker-large'

    neo4j_uri: str = 'bolt://localhost:7687'
    neo4j_username: str = 'neo4j'
    neo4j_password: str = 'your-neo4j-password'
    neo4j_database: str = 'power_grid_knowledge'

    zvec_data_dir: str = './data/cache/zvec_store'
    zvec_collection_name: str = 'power_grid_knowledge'

    sqlite_db_path: str = './data/meta.db'

    retrieve_top_n: int = 20
    rerank_top_n: int = 10
    similarity_threshold: float = 0.7
    max_context_token: int = 4096

    cors_origins_raw: str = Field(
        default=(
            'http://localhost:3000,http://127.0.0.1:3000,'
            'http://localhost:5173,http://127.0.0.1:5173'
        ),
        alias='CORS_ORIGINS',
    )

    class Config:
        env_file = '.env'
        extra = 'ignore'

    @property
    def cors_origins(self) -> list[str]:
        return [x.strip() for x in self.cors_origins_raw.split(',') if x.strip()]

    @property
    def sqlite_path(self) -> Path:
        return Path(self.sqlite_db_path)


settings = Settings()
