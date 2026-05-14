from __future__ import annotations

from typing import Any

from src.agent.skills.registry import SkillRegistry


class ReActExecutor:
    """
    轻量 ReAct 执行器：
    - 保留现有 task plan 作为初始计划；
    - 每一步根据上下文决定下一个技能；
    - 支持最大步数限制，避免循环调用。
    """

    def __init__(self, registry: SkillRegistry, max_steps: int = 4) -> None:
        self.registry = registry
        self.max_steps = max_steps

    def run(
        self,
        query: str,
        intent: dict[str, Any],
        initial_plan: list[dict[str, Any]] | None = None,
    ) -> dict[str, Any]:
        runtime_ctx: dict[str, Any] = {}
        tool_results: list[dict[str, Any]] = []
        plan_steps: list[dict[str, Any]] = []
        trace: list[dict[str, Any]] = []

        queued_tools = [item.get('tool') for item in (initial_plan or []) if item.get('tool')]
        queued_tools.extend(self._infer_document_workflow(query))
        used_tools: list[str] = []

        for step_idx in range(1, self.max_steps + 1):
            next_tool = self._choose_next_tool(intent, runtime_ctx, queued_tools, used_tools)
            if not next_tool:
                break

            result = self.registry.run(next_tool, query, runtime_ctx)
            used_tools.append(next_tool)

            plan_steps.append({'tool': next_tool, 'desc': self._build_desc(next_tool)})
            tool_results.append(result)
            self._update_runtime_context(next_tool, result, runtime_ctx)

            trace.append(
                {
                    'step': step_idx,
                    'thought': self._build_thought(next_tool, intent, runtime_ctx),
                    'action': next_tool,
                    'observation': 'error' if 'error' in result else 'ok',
                }
            )

            if self._should_stop(intent, next_tool, result, runtime_ctx, queued_tools):
                break

        return {
            'plan': plan_steps,
            'tool_results': tool_results,
            'runtime_ctx': runtime_ctx,
            'trace': trace,
        }

    def _choose_next_tool(
        self,
        intent: dict[str, Any],
        runtime_ctx: dict[str, Any],
        queued_tools: list[str],
        used_tools: list[str],
    ) -> str | None:
        while queued_tools:
            candidate = queued_tools.pop(0)
            if candidate and self.registry.has(candidate) and candidate not in used_tools:
                return candidate

        group = intent.get('intent_group', 'qa')
        if group in ('qa', 'aggregation', 'scenario') and 'knowledge_retrieval' not in used_tools and self.registry.has(
            'knowledge_retrieval'
        ):
            return 'knowledge_retrieval'
        if group == 'aggregation' and 'device_aggregation' not in used_tools and self.registry.has('device_aggregation'):
            return 'device_aggregation'
        if group == 'scenario' and 'scenario_template' not in used_tools and self.registry.has('scenario_template'):
            return 'scenario_template'
        if group == 'graph' and 'graph_query' not in used_tools and self.registry.has('graph_query'):
            return 'graph_query'
        return None

    def _update_runtime_context(self, tool_name: str, result: dict[str, Any], runtime_ctx: dict[str, Any]) -> None:
        runtime_ctx[f'{tool_name}_result'] = result
        if tool_name == 'knowledge_retrieval':
            runtime_ctx['retrieval'] = result
        if tool_name == 'document_parse':
            runtime_ctx['document_parse_result'] = result
        if tool_name == 'standard_compare':
            runtime_ctx['standard_compare_result'] = result
        if tool_name == 'risk_check':
            runtime_ctx['risk_check_result'] = result

    def _should_stop(
        self,
        intent: dict[str, Any],
        tool_name: str,
        result: dict[str, Any],
        runtime_ctx: dict[str, Any],
        queued_tools: list[str],
    ) -> bool:
        if 'error' in result:
            return True
        if tool_name == 'graph_query':
            return True
        if tool_name in ('device_aggregation', 'scenario_template'):
            return True
        if tool_name == 'report_generate':
            return True
        # QA 场景：只检索一次后结束
        group = intent.get('intent_group', 'qa')
        has_pending_workflow = any(step in ('document_parse', 'standard_compare', 'risk_check', 'report_generate') for step in queued_tools)
        if group == 'qa' and tool_name == 'knowledge_retrieval' and 'retrieval' in runtime_ctx and not has_pending_workflow:
            return True
        return False

    def _build_desc(self, tool_name: str) -> str:
        if tool_name == 'knowledge_retrieval':
            return '执行知识检索技能'
        if tool_name == 'device_aggregation':
            return '执行设备聚合技能'
        if tool_name == 'scenario_template':
            return '执行场景模板技能'
        if tool_name == 'graph_query':
            return '执行图谱查询技能'
        if tool_name == 'document_parse':
            return '执行文档解析技能'
        if tool_name == 'standard_compare':
            return '执行条款比对技能'
        if tool_name == 'risk_check':
            return '执行风险核查技能'
        if tool_name == 'report_generate':
            return '执行报告生成技能'
        return f'执行技能：{tool_name}'

    def _build_thought(self, tool_name: str, intent: dict[str, Any], runtime_ctx: dict[str, Any]) -> str:
        group = intent.get('intent_group', 'qa')
        has_retrieval = 'retrieval' in runtime_ctx
        return f'意图组={group}，已检索={has_retrieval}，选择技能={tool_name}'

    def _infer_document_workflow(self, query: str) -> list[str]:
        q = query.strip().lower()
        doc_terms = ('文档', '规程', '条款', '操作票', '安措', 'pdf', 'word', 'excel')
        compare_terms = ('比对', '核对', '一致性')
        risk_terms = ('风险', '隐患', '安全')
        report_terms = ('报告', '总结', '输出')

        if not any(term in q for term in doc_terms):
            return []

        workflow: list[str] = []
        workflow.append('document_parse')
        if any(term in q for term in compare_terms):
            workflow.append('standard_compare')
        if any(term in q for term in risk_terms):
            if 'standard_compare' not in workflow:
                workflow.append('standard_compare')
            workflow.append('risk_check')
        if any(term in q for term in report_terms):
            if 'standard_compare' not in workflow:
                workflow.append('standard_compare')
            if 'risk_check' not in workflow:
                workflow.append('risk_check')
            workflow.append('report_generate')

        if len(workflow) == 1:
            workflow.extend(['standard_compare', 'risk_check', 'report_generate'])
        return workflow
