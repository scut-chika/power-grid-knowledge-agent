from pydantic import BaseModel


class ConfigUpdateRequest(BaseModel):
    items: dict[str, str]
