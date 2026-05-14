"""Power grid risk check skill — CLI + importable module.

Usage (CLI):
    python scripts/check.py --help
    python scripts/check.py --query "风险核查" --context-json '{"standard_compare_result": {...}}'

Usage (Python, called by ReAct executor):
    from src.agent.skills.power_grid_risk_check.scripts.check import run
    result = run(query, context)
"""
from __future__ import annotations

import argparse
import json
import sys
from typing import Any


CRITICAL_KEYWORDS = ('验电', '接地线', '带电', '误操作', '人身')
HIGH_KEYWORDS = ('顺序', '越级', '跳闸', '误合', '误拉')
MEDIUM_KEYWORDS = ('定值', '校验', '记录', '签名')


def run(query: str, context: dict[str, Any]) -> dict[str, Any]:
    """Identify risk items from upstream compare results."""
    compared = context.get('standard_compare_result', {})
    diffs = compared.get('differences', [])

    risk_items: list[dict[str, str]] = []
    for idx, item in enumerate(diffs[:10], start=1):
        level = _assess_level(item)
        risk_items.append({
            'id': f'RISK-{idx:03d}',
            'title': f"条款核查风险：{item.get('clause', '未知条款')}",
            'level': level,
            'suggestion': _suggestion_for(level),
        })

    if not risk_items:
        risk_items.append({
            'id': 'RISK-000',
            'title': '未发现可自动判定风险项',
            'level': 'low',
            'suggestion': '建议人工复核操作票、安措票、现场安全措施',
        })

    return {
        'query': query,
        'risk_items': risk_items,
        'references': compared.get('references', []),
    }


def _assess_level(diff: dict[str, str]) -> str:
    text = (diff.get('observed', '') + diff.get('expected', '')).lower()
    if any(kw in text for kw in CRITICAL_KEYWORDS):
        return 'critical'
    if any(kw in text for kw in HIGH_KEYWORDS):
        return 'high'
    if any(kw in text for kw in MEDIUM_KEYWORDS):
        return 'medium'
    return 'medium'


def _suggestion_for(level: str) -> str:
    if level == 'critical':
        return '立即停止操作，通知值班负责人与安全专责到场确认'
    if level == 'high':
        return '暂停操作，由值班员与专责联合复核后方可继续'
    if level == 'medium':
        return '建议核查后补充记录或签字确认'
    return '建议人工复核操作票、安措票、现场安全措施'


def main() -> None:
    parser = argparse.ArgumentParser(
        description='Check safety risks in power grid documents.',
        epilog='Examples:\n'
               '  python check.py --query "风险核查" --context-json \'{"standard_compare_result":{...}}\'',
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
