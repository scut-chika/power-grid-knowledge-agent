from pydantic import BaseModel


class BuildRequest(BaseModel):
    build_type: str = 'incremental'
