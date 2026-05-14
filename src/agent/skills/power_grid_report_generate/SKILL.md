---
name: power-grid-report-generate
description: >-
  Aggregate results from document parse, standard compare, and risk check into
  a final structured review report. Use when the user asks for a summary,
  report, output, or final review of document processing results.
---

# Power Grid Report Generate

Collect all upstream skill outputs (parse → compare → risk-check) and produce
a human-readable review report with action items.

> **All paths are relative to the directory containing this SKILL.md file.**

## Prerequisites

- Python 3.10+
- Upstream skills should have run first (outputs read from context):
  - `document_parse_result`
  - `standard_compare_result`
  - `risk_check_result`

## Quick Start

```bash
# Pipeline mode
python scripts/generate.py --query "生成报告" \
  --context-json '{"document_parse_result":{...}, "standard_compare_result":{...}, "risk_check_result":{...}}'

# Show help
python scripts/generate.py --help
```

## Workflow

1. **Collect upstream data** from three context keys
2. **Aggregate statistics**: section count, diff count, risk count by level
3. **Compose report structure** with title, summary, stats, and next actions
4. **Output JSON to stdout**

```json
{
  "report": {
    "title": "电力文档处理报告",
    "query": "原始查询",
    "summary": "综述结论",
    "document_sections_count": 5,
    "difference_count": 2,
    "risk_count": 1,
    "risk_by_level": {"critical": 0, "high": 0, "medium": 1, "low": 0},
    "next_actions": [
      "人工复核关键条款一致性",
      "确认安措票与现场操作条件",
      "形成最终签发版本并归档"
    ]
  },
  "references": []
}
```

## Integration

This skill is typically the **last step** in the document processing pipeline.
Its output is returned directly to the user as the final answer context.

## Error Handling

- **Partial upstream data**: report still generated with available fields;
  missing counts shown as 0
- **No upstream data at all**: returns a minimal report advising manual review
