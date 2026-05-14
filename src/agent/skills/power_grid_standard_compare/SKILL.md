---
name: power-grid-standard-compare
description: >-
  Compare document sections against power grid operational standards and
  regulations, outputting clause-level differences. Use when the user mentions
  comparing, verifying, checking compliance, or validating operation tickets
  against standards.
---

# Power Grid Standard Compare

Compare extracted document sections (from `power-grid-document-parse`) against
the knowledge base of grid operational standards to find conflicts, omissions,
and deviations.

> **All paths are relative to the directory containing this SKILL.md file.**

## Prerequisites

- Python 3.10+
- Upstream skill `power-grid-document-parse` should have run first (its output
  is read from context key `document_parse_result`)

## Quick Start

```bash
# Pipeline mode (receives upstream context)
python scripts/compare.py --query "核对操作票" \
  --context-json '{"document_parse_result": {"sections": [...], "references": [...]}}'

# Show help
python scripts/compare.py --help
```

## Workflow

1. **Read upstream sections** from `document_parse_result.sections`
2. **For each section**, compare against known standards:
   - Look for missing safety steps (验电、接地线、操作顺序)
   - Check parameter ranges against retrieval context
3. **Output clause-level diff list**

```json
{
  "compare_target": "power_grid_operational_standards",
  "differences": [
    {
      "clause": "条款编号或片段标识",
      "observed": "文档中实际内容",
      "expected": "规程要求的标准内容",
      "status": "conflict|missing|ok|pending_review"
    }
  ],
  "references": []
}
```

## Status Values

| Status | Meaning |
|--------|---------|
| `ok` | Section matches standard |
| `conflict` | Content contradicts the standard |
| `missing` | Required step/clause absent from document |
| `pending_review` | Cannot auto-determine, needs human review |

## Error Handling

- **No upstream data**: returns empty `differences` with a warning in stderr
- **Malformed context**: exits with code 1
