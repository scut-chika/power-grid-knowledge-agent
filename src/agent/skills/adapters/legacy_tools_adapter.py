from __future__ import annotations

import importlib
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Callable

import yaml

from src.agent.skills.base import SkillMeta
from src.agent.skills.registry import SkillRegistry
from src.agent.tools import device_aggregation_tool, graph_tool, knowledge_tool, scenario_tool


Runner = Callable[[str, dict[str, Any]], dict[str, Any]]

SKILLS_DIR = Path(__file__).resolve().parent.parent


@dataclass
class LegacyToolSkill:
    meta: SkillMeta
    runner: Runner

    def run(self, query: str, context: dict[str, Any]) -> dict[str, Any]:
        return self.runner(query, context)


@dataclass
class ScriptBackedSkill:
    """Skill backed by a standard SKILL.md + scripts/ directory."""

    meta: SkillMeta
    run_func: Callable[[str, dict[str, Any]], dict[str, Any]]

    def run(self, query: str, context: dict[str, Any]) -> dict[str, Any]:
        return self.run_func(query, context)


def _run_knowledge(query: str, _: dict[str, Any]) -> dict[str, Any]:
    return knowledge_tool.run(query)


def _run_graph(query: str, _: dict[str, Any]) -> dict[str, Any]:
    return graph_tool.run(query)


def _run_device_aggregation(query: str, context: dict[str, Any]) -> dict[str, Any]:
    retrieval = context.get('retrieval', {})
    return device_aggregation_tool.run(query, retrieval)


def _run_scenario(query: str, context: dict[str, Any]) -> dict[str, Any]:
    retrieval = context.get('retrieval', {})
    return scenario_tool.run(query, retrieval)


def _parse_skill_md(skill_md_path: Path) -> SkillMeta | None:
    """Parse YAML frontmatter from a SKILL.md file."""
    text = skill_md_path.read_text(encoding='utf-8')
    match = re.match(r'^---\s*\n(.*?)\n---', text, re.DOTALL)
    if not match:
        return None
    front = yaml.safe_load(match.group(1))
    if not front or 'name' not in front:
        return None
    return SkillMeta(
        name=front['name'],
        description=front.get('description', ''),
        tags=front.get('tags', []),
    )


_SKILL_SCRIPT_MAP: dict[str, str] = {
    'power_grid_document_parse': 'src.agent.skills.power_grid_document_parse.scripts.parse',
    'power_grid_standard_compare': 'src.agent.skills.power_grid_standard_compare.scripts.compare',
    'power_grid_risk_check': 'src.agent.skills.power_grid_risk_check.scripts.check',
    'power_grid_report_generate': 'src.agent.skills.power_grid_report_generate.scripts.generate',
}

_SKILL_NAME_REMAP: dict[str, str] = {
    'power_grid_document_parse': 'document_parse',
    'power_grid_standard_compare': 'standard_compare',
    'power_grid_risk_check': 'risk_check',
    'power_grid_report_generate': 'report_generate',
}


def _discover_and_register_standard_skills(registry: SkillRegistry) -> None:
    """Scan SKILLS_DIR for subdirectories containing SKILL.md and register them."""
    for skill_dir in sorted(SKILLS_DIR.iterdir()):
        skill_md = skill_dir / 'SKILL.md'
        if not skill_md.is_file():
            continue

        meta = _parse_skill_md(skill_md)
        if meta is None:
            continue

        dir_name = skill_dir.name
        module_path = _SKILL_SCRIPT_MAP.get(dir_name)
        if module_path is None:
            continue

        try:
            mod = importlib.import_module(module_path)
            run_func = getattr(mod, 'run')
        except (ImportError, AttributeError):
            continue

        short_name = _SKILL_NAME_REMAP.get(dir_name, meta.name)
        meta = SkillMeta(name=short_name, description=meta.description, tags=meta.tags)
        registry.register(ScriptBackedSkill(meta=meta, run_func=run_func))


def register_legacy_skills(registry: SkillRegistry) -> SkillRegistry:
    registry.register(
        LegacyToolSkill(
            meta=SkillMeta(
                name='knowledge_retrieval',
                description='执行混合检索并返回知识片段',
                tags=['rag', 'retrieval'],
            ),
            runner=_run_knowledge,
        )
    )
    registry.register(
        LegacyToolSkill(
            meta=SkillMeta(
                name='graph_query',
                description='执行图谱关系查询',
                tags=['graph'],
            ),
            runner=_run_graph,
        )
    )
    registry.register(
        LegacyToolSkill(
            meta=SkillMeta(
                name='device_aggregation',
                description='聚合设备台账、定值与文档信息',
                tags=['aggregation'],
            ),
            runner=_run_device_aggregation,
        )
    )
    registry.register(
        LegacyToolSkill(
            meta=SkillMeta(
                name='scenario_template',
                description='生成故障处置场景模板',
                tags=['scenario'],
            ),
            runner=_run_scenario,
        )
    )
    return registry


def build_default_registry() -> SkillRegistry:
    registry = SkillRegistry()
    register_legacy_skills(registry)
    _discover_and_register_standard_skills(registry)
    return registry
