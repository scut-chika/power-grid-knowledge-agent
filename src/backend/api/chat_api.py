import json
import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, Query
from fastapi.responses import StreamingResponse

from src.agent.agent_core import execute_agent_pipeline, run_agent
from src.agent.answer_generator import SAFETY_NOTE, build_llm_messages, fallback_answer, is_general_chat
from src.agent.dialogue_manager import append_assistant_message, append_user_message, ensure_session, get_history, get_sessions
from src.backend.core.security import get_current_user
from src.backend.schemas.chat import ChatQueryRequest, ChatStreamRequest
from src.rag_engine.siliconflow_client import chat_completion_stream

router = APIRouter()


@router.post('/query')
def chat_query(req: ChatQueryRequest, user: Annotated[dict, Depends(get_current_user)]) -> dict:
    session_id = req.session_id or str(uuid.uuid4())
    result = run_agent(req.query, session_id=session_id, user_id=user['username'])
    return {'code': 0, 'message': 'ok', 'data': {'session_id': session_id, **result}}


@router.get('/history')
def chat_history(
    session_id: str = Query(...),
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=50, ge=1, le=500),
    _: Annotated[dict, Depends(get_current_user)] = None,
) -> dict:
    items = get_history(session_id, page, page_size)
    return {'code': 0, 'message': 'ok', 'data': {'items': items, 'session_id': session_id}}


@router.get('/session')
def chat_sessions(user: Annotated[dict, Depends(get_current_user)]) -> dict:
    sessions = get_sessions(user['username'])
    return {'code': 0, 'message': 'ok', 'data': {'items': sessions}}


@router.post('/session')
def create_chat_session(user: Annotated[dict, Depends(get_current_user)]) -> dict:
    """新建空会话，写入 chat_sessions，便于侧栏立即展示。"""
    session_id = f'sess-{uuid.uuid4().hex[:16]}'
    ensure_session(session_id, user['username'])
    return {'code': 0, 'message': 'ok', 'data': {'session_id': session_id}}


@router.post('/stream')
def chat_stream(req: ChatStreamRequest, user: Annotated[dict, Depends(get_current_user)]):
    session_id = req.session_id or str(uuid.uuid4())

    def _sse(event: dict) -> str:
        return f"data: {json.dumps(event, ensure_ascii=False)}\n\n"

    def event_stream():
        ensure_session(session_id, user['username'])
        append_user_message(session_id, req.query)
        yield _sse({'type': 'session', 'session_id': session_id})

        pipeline = execute_agent_pipeline(req.query)
        reasoning = pipeline['reasoning']
        if req.show_thinking:
            steps = reasoning.get('steps', [])
            thinking_text = '\n'.join([f"{s['step']}. {s['task']}（{s['observation']}）" for s in steps])
            if thinking_text:
                yield _sse({'type': 'thinking', 'content': thinking_text})

        final_data = pipeline['final_data']
        citations = (final_data.get('results') or final_data.get('references') or [])[:5]

        full_answer = ''
        if citations or is_general_chat(req.query) or (req.attachment_text and str(req.attachment_text).strip()):
            messages = build_llm_messages(req.query, citations, attachment_excerpt=req.attachment_text)
            for chunk in chat_completion_stream(messages=messages, temperature=0.2, max_tokens=800) or []:
                if chunk.get('type') == 'reasoning' and req.show_thinking:
                    yield _sse({'type': 'thinking_delta', 'content': chunk.get('content', '')})
                if chunk.get('type') == 'content':
                    delta = chunk.get('content', '')
                    full_answer += delta
                    yield _sse({'type': 'delta', 'content': delta})

        if not full_answer.strip():
            full_answer = fallback_answer(req.query, citations)
            yield _sse({'type': 'delta', 'content': full_answer})
        else:
            full_answer = f"{full_answer}\n\n{SAFETY_NOTE}"
            yield _sse({'type': 'delta', 'content': f"\n\n{SAFETY_NOTE}"})

        append_assistant_message(session_id, full_answer, citations)
        yield _sse({'type': 'done', 'session_id': session_id, 'citations': citations})

    return StreamingResponse(event_stream(), media_type='text/event-stream')
