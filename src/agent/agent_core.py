import os

from src.agent.answer_generator import generate_answer
from src.agent.cot_reasoning import reason
from src.agent.dialogue_manager import append_assistant_message, append_user_message, ensure_session
from src.agent.intent_recognition import recognize_intent
from src.agent.skills.adapters.legacy_tools_adapter import build_default_registry
from src.agent.skills.executor_react import ReActExecutor
from src.agent.task_planner import make_plan
from src.agent.tool_calling import call_tool
from src.rag_engine.query_processor import preprocess_query


def _execute_with_legacy(query: str, intent: dict) -> dict:
    plan = make_plan(intent)
    tool_results = []
    runtime_ctx = {}
    for task in plan:
        result = call_tool(task['tool'], query, runtime_ctx)
        tool_results.append(result)
        if task['tool'] == 'knowledge_retrieval':
            runtime_ctx['retrieval'] = result
    return {'plan': plan, 'tool_results': tool_results, 'runtime_ctx': runtime_ctx, 'trace': []}


def _execute_with_react(query: str, intent: dict) -> dict:
    registry = build_default_registry()
    executor = ReActExecutor(registry=registry, max_steps=4)
    return executor.run(query=query, intent=intent, initial_plan=make_plan(intent))


def execute_agent_pipeline(query: str) -> dict:
    parsed = preprocess_query(query)
    intent = recognize_intent(parsed)
    mode = os.getenv('AGENT_EXECUTION_MODE', 'legacy').strip().lower()

    if mode == 'react':
        execution = _execute_with_react(query, intent)
    else:
        mode = 'legacy'
        execution = _execute_with_legacy(query, intent)

    plan = execution.get('plan', [])
    tool_results = execution.get('tool_results', [])
    runtime_ctx = execution.get('runtime_ctx', {})
    reasoning = reason(plan, tool_results)

    final_data = tool_results[-1] if tool_results else {}
    if 'results' not in final_data and runtime_ctx.get('retrieval'):
        final_data = runtime_ctx['retrieval']

    return {
        'intent': intent,
        'reasoning': reasoning,
        'final_data': final_data,
        'execution_mode': mode,
        'trace': execution.get('trace', []),
    }


def run_agent(query: str, session_id: str, user_id: str) -> dict:
    ensure_session(session_id, user_id)
    append_user_message(session_id, query)
    pipeline = execute_agent_pipeline(query)
    answer, citations = generate_answer(query, pipeline['reasoning'], pipeline['final_data'])
    append_assistant_message(session_id, answer, citations)

    return {
        'answer': answer,
        'citations': citations,
        'reasoning': pipeline['reasoning'],
        'intent': pipeline['intent'],
        'execution_mode': pipeline['execution_mode'],
        'trace': pipeline['trace'],
    }
