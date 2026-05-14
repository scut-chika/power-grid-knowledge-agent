---
name: power-grid-document-parse
description: >-
  Parse power grid documents (PDF/Word/Excel/scanned images) into structured
  sections, equipment entities, and operating steps. Use when the user uploads
  a document, mentions parsing, extracting, or structuring power grid files.
---

# Power Grid Document Parse

Parse power grid operational documents and extract structured data for
downstream skills (compare, risk-check, report).

> **All paths are relative to the directory containing this SKILL.md file.**

## Prerequisites

- Python 3.10+
- Project dependencies installed (`pip install -r requirements.txt`)
- For scanned documents: PaddleOCR (`paddleocr` package, already in project deps)

## Quick Start

```bash
# Parse from retrieval context (pipeline mode, called by ReAct executor)
python scripts/parse.py --query "某某规程文档解析" --context-json '{"retrieval": ...}'

# Parse a local file directly
python scripts/parse.py --file path/to/document.pdf

# Show help
python scripts/parse.py --help
```

## Workflow

1. **Determine document source**
   - If `--file` is given: read the file with pdfplumber / python-docx / openpyxl
   - If `--context-json` is given: extract sections from retrieval results

2. **Extract structured fields**
   - Equipment names and IDs (e.g. `220kV线路A`, `#1主变`)
   - Setting parameters (e.g. `过流保护Ⅰ段定值`)
   - Ordered operating steps

3. **Output JSON to stdout**

```json
{
  "document_profile": {
    "query": "原始查询",
    "doc_type": "power_grid_doc",
    "source": "file|retrieval"
  },
  "sections": ["片段1: ...", "片段2: ..."],
  "entities": ["220kV线路A"],
  "references": []
}
```

## Integration

This skill is called automatically by the ReAct executor when the user query
contains document-related keywords (`文档`, `规程`, `操作票`, `PDF`, etc.).
Downstream skills (`standard_compare`, `risk_check`, `report_generate`) read
its output from the runtime context key `document_parse_result`.

## Error Handling

- **File not found**: exits with code 1 and prints path to stderr
- **Unsupported format**: exits with code 2 and lists supported extensions
- **Empty extraction**: returns valid JSON with empty `sections` list
