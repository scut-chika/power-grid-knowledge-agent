from pydantic import BaseModel, Field


class ChatQueryRequest(BaseModel):
    query: str
    session_id: str


class ChatStreamRequest(BaseModel):
    query: str
    session_id: str
    show_thinking: bool = False
    """对话时附带的纯文本节选（如用户选择的 txt/csv/md），参与回答但不写入向量库。"""
    attachment_text: str | None = Field(default=None, max_length=50000)
