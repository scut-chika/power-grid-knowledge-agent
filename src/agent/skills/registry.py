from __future__ import annotations

from typing import Any

from src.agent.skills.base import Skill


class SkillRegistry:
    def __init__(self) -> None:
        self._skills: dict[str, Skill] = {}

    def register(self, skill: Skill) -> None:
        self._skills[skill.meta.name] = skill

    def get(self, name: str) -> Skill | None:
        return self._skills.get(name)

    def run(self, name: str, query: str, context: dict[str, Any]) -> dict[str, Any]:
        skill = self.get(name)
        if skill is None:
            return {'error': f'未知技能：{name}'}
        return skill.run(query, context)

    def has(self, name: str) -> bool:
        return name in self._skills

    def names(self) -> list[str]:
        return list(self._skills.keys())
