"""Power grid standard compare skill — CLI + importable module.

Usage (CLI):
    python scripts/compare.py --help
    python scripts/compare.py --query "核对" --context-json '{"document_parse_result": {...}}'

Usage (Python, called by ReAct executor):
    from src.agent.skills.power_grid_standard_compare.scripts.compare import run
    result = run(query, context)
"""
from __future__ import annotations

import argparse
import json
import sys
from typing import Any


def run(query: str, context: dict[str, Any]) -> dict[str, Any]:
    """Compare document sections against operational standards."""
    parsed = context.get('document_parse_result', {})
    sections = parsed.get('sections', [])

    if not sections:
        print('Warning: no sections from upstream document_parse', file=sys.stderr)

    diffs: list[dict[str, str]] = []
    for idx, section in enumerate(sections[:10], start=1):
        status = _check_section(section)
        diffs.append({
            'clause': f'条款片段-{idx}',
            'observed': section[:200],
            'expected': '需与当前电网规程条款逐条核对',
            'status': status,
        })

    return {
        'query': query,
        'compare_target': 'power_grid_operational_standards',
        'differences': diffs,
        'references': parsed.get('references', []),
    }


def _check_section(section: str) -> str:
    """Rule-based quick check — placeholder for real regulation matching."""
    danger_keywords = ('严禁', '禁止', '不得', '必须')
    missing_keywords = ('验电', '接地线', '安全距离')

    text = section.lower()
    if any(kw in text for kw in danger_keywords):
        return 'conflict'
    if any(kw in text for kw in missing_keywords):
        return 'pending_review'
    return 'pending_review'


def main() -> None:
    parser = argparse.ArgumentParser(
        description='Compare document sections against power grid standards.',
        epilog='Examples:\n'
               '  python compare.py --query "核对操作票" --context-json \'{"document_parse_result":{...}}\'',
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument('--query', default='', help='User query text')
    parser.add_argument('--context-json', default='{}', help='JSON string of runtime context')
    args = parser.parse_args()

    context = json.loads(args.context_json)
    result = run(args.query, context)
    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == '__main__':
    main()
