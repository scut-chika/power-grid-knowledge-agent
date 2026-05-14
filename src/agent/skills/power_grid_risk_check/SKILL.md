---
name: power-grid-risk-check
description: >-
  Identify safety risks in power grid documents and operation tickets based on
  upstream parse and compare results. Outputs risk items with severity levels
  and actionable suggestions. Use when the user mentions risk, safety, hazard,
  inspection, or checking operation tickets.
---

# Power Grid Risk Check

Analyze parsed document sections and clause comparison results to identify
operational safety risks, output structured risk items with severity and
recommended actions.

> **All paths are relative to the directory containing this SKILL.md file.**

## Prerequisites

- Python 3.10+
- Upstream skills should have run first:
  - `power-grid-document-parse` → `document_parse_result`
  - `power-grid-standard-compare` → `standard_compare_result`

## Quick Start

```bash
# Pipeline mode
python scripts/check.py --query "风险核查" \
  --context-json '{"standard_compare_result": {"differences": [...]}}'

# Show help
python scripts/check.py --help
```

## Workflow

1. **Read upstream differences** from `standard_compare_result.differences`
2. **For each difference**, evaluate risk level:
   - `critical`: may cause injury or widespread outage
   - `high`: serious regulation violation
   - `medium`: procedure order issue, record irregularity
   - `low`: informational note
3. **Output risk items**

```json
{
  "risk_items": [
    {
      "id": "RISK-001",
      "title": "描述：缺少验电步骤",
      "level": "critical|high|medium|low",
      "suggestion": "建议由值班员与专责联合复核"
    }
  ],
  "references": []
}
```

## Risk Level Guide

| Level | Trigger Examples |
|-------|-----------------|
| `critical` | 缺少验电、接地线遗漏、带电误操作 |
| `high` | 操作顺序颠倒、越级跳闸处置不当 |
| `medium` | 记录不规范、定值未校验 |
| `low` | 格式问题、通用性提示 |

## Error Handling

- **No upstream data**: returns a single `low` risk item suggesting manual review
- **Malformed context**: exits with code 1
