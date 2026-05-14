"""Power grid report generate skill — CLI + importable module.

Usage (CLI):
    python scripts/generate.py --help
    python scripts/generate.py --query "生成报告" --context-json '{"document_parse_result":...}'

Usage (Python, called by ReAct executor):
    from src.agent.skills.power_grid_report_generate.scripts.generate import run
    result = run(query, context)
"""
from __future__ import annotations

import argparse
import json
from typing import Any


def run(query: str, context: dict[str, Any]) -> dict[str, Any]:
    """Aggregate upstream skill results into a final report."""
    parsed = context.get('document_parse_result', {})
    compared = context.get('standard_compare_result', {})
    checked = context.get('risk_check_result', {})

    risk_items = checked.get('risk_items', [])
    risk_by_level: dict[str, int] = {'critical': 0, 'high': 0, 'medium': 0, 'low': 0}
    for item in risk_items:
        lvl = item.get('level', 'low')
        risk_by_level[lvl] = risk_by_level.get(lvl, 0) + 1

    has_critical = risk_by_level.get('critical', 0) > 0
    summary = (
        '发现高危风险项，建议立即终止流转并组织专项复核。'
        if has_critical
        else '已完成文档解析、条款比对与风险核查，请进行人工确认后落地执行。'
    )

    report = {
        'title': '电力文档处理报告',
        'query': query,
        'summary': summary,
        'document_sections_count': len(parsed.get('sections', [])),
        'difference_count': len(compared.get('differences', [])),
        'risk_count': len(risk_items),
        'risk_by_level': risk_by_level,
        'next_actions': [
            '人工复核关键条款一致性',
            '确认安措票与现场操作条件',
            '形成最终签发版本并归档',
        ],
    }

    references = (
        checked.get('references')
        or compared.get('references')
        or parsed.get('references')
        or context.get('retrieval', {}).get('results', [])
    )
    return {'report': report, 'references': references[:8]}


def main() -> None:
    parser = argparse.ArgumentParser(
        description='Generate a structured review report from upstream skill results.',
        epilog='Examples:\n'
               '  python generate.py --query "生成报告" --context-json \'{"document_parse_result":{...}}\'',
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
