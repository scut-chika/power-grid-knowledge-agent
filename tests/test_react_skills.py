import os

from src.agent import agent_core
from src.agent.skills.adapters.legacy_tools_adapter import build_default_registry
from src.agent.skills.executor_react import ReActExecutor
from src.agent.tools import knowledge_tool


def test_registry_contains_document_skills():
    registry = build_default_registry()
    names = registry.names()
    assert 'document_parse' in names
    assert 'standard_compare' in names
    assert 'risk_check' in names
    assert 'report_generate' in names


def test_react_document_workflow_with_legacy_retrieval(monkeypatch):
    monkeypatch.setattr(
        knowledge_tool,
        'run',
        lambda query: {
            'results': [{'content': f'规程片段:{query}', 'source': 'kb', 'score': 0.9}],
            'parsed': {'entities': ['220kV线路A']},
        },
    )

    registry = build_default_registry()
    executor = ReActExecutor(registry=registry, max_steps=6)
    out = executor.run(
        query='请对这份文档做条款比对、风险核查并输出报告',
        intent={'intent_group': 'qa'},
        initial_plan=[{'tool': 'knowledge_retrieval', 'desc': '执行混合检索'}],
    )

    plan_tools = [step['tool'] for step in out['plan']]
    assert plan_tools[:5] == [
        'knowledge_retrieval',
        'document_parse',
        'standard_compare',
        'risk_check',
        'report_generate',
    ]
    assert 'report' in out['tool_results'][-1]
    assert 'document_parse_result' in out['runtime_ctx']
    assert 'risk_check_result' in out['runtime_ctx']


def test_execute_agent_pipeline_mode_switch(monkeypatch):
    monkeypatch.setattr(agent_core, 'preprocess_query', lambda query: {'intent': '通用知识咨询'})
    monkeypatch.setattr(agent_core, 'recognize_intent', lambda parsed: {'intent_group': 'qa'})
    monkeypatch.setattr(
        agent_core,
        '_execute_with_legacy',
        lambda query, intent: {
            'plan': [{'tool': 'knowledge_retrieval', 'desc': 'legacy'}],
            'tool_results': [{'results': [{'content': 'legacy'}]}],
            'runtime_ctx': {'retrieval': {'results': [{'content': 'legacy'}]}},
            'trace': [],
        },
    )
    monkeypatch.setattr(
        agent_core,
        '_execute_with_react',
        lambda query, intent: {
            'plan': [{'tool': 'report_generate', 'desc': 'react'}],
            'tool_results': [{'report': {'title': 'r'}, 'references': []}],
            'runtime_ctx': {},
            'trace': [{'step': 1, 'action': 'report_generate', 'observation': 'ok'}],
        },
    )

    monkeypatch.setenv('AGENT_EXECUTION_MODE', 'legacy')
    out_legacy = agent_core.execute_agent_pipeline('x')
    assert out_legacy['execution_mode'] == 'legacy'

    monkeypatch.setenv('AGENT_EXECUTION_MODE', 'react')
    out_react = agent_core.execute_agent_pipeline('x')
    assert out_react['execution_mode'] == 'react'
    assert out_react['trace']

    os.environ.pop('AGENT_EXECUTION_MODE', None)
