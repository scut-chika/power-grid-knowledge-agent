from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Protocol


@dataclass
class SkillMeta:
    name: str
    description: str
    tags: list[str] = field(default_factory=list)


class Skill(Protocol):
    meta: SkillMeta

    def run(self, query: str, context: dict[str, Any]) -> dict[str, Any]:
        ...
