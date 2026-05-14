"""Power grid document parse skill — CLI + importable module.

Usage (CLI):
    python scripts/parse.py --help
    python scripts/parse.py --query "解析某规程" --context-json '{"retrieval": {...}}'
    python scripts/parse.py --file path/to/document.pdf

Usage (Python, called by ReAct executor):
    from src.agent.skills.power_grid_document_parse.scripts.parse import run
    result = run(query, context)
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any


def run(query: str, context: dict[str, Any]) -> dict[str, Any]:
    """Core logic — parse document from retrieval context or file path."""
    retrieval = context.get('retrieval', {})
    refs = retrieval.get('results') or []
    file_path = context.get('file_path')

    sections: list[str] = []
    entities: list[str] = retrieval.get('parsed', {}).get('entities', [])
    source = 'retrieval'

    if file_path:
        source = 'file'
        sections, entities = _parse_file(Path(file_path))
    else:
        for item in refs[:5]:
            content = str(item.get('content', '')).strip()
            if content:
                sections.append(content[:200])

    return {
        'document_profile': {
            'query': query,
            'doc_type': 'power_grid_doc',
            'source': source,
            'has_retrieval_context': bool(refs),
        },
        'sections': sections,
        'entities': entities,
        'references': refs[:8],
    }


def _parse_file(path: Path) -> tuple[list[str], list[str]]:
    """Extract text sections and entities from a local file."""
    suffix = path.suffix.lower()
    sections: list[str] = []
    entities: list[str] = []

    if not path.exists():
        print(f'Error: file not found: {path}', file=sys.stderr)
        sys.exit(1)

    if suffix == '.pdf':
        try:
            import pdfplumber
            with pdfplumber.open(str(path)) as pdf:
                for page in pdf.pages[:20]:
                    text = page.extract_text()
                    if text:
                        sections.append(text[:500])
        except ImportError:
            print('pdfplumber not installed', file=sys.stderr)
            sys.exit(2)

    elif suffix in ('.docx', '.doc'):
        try:
            from docx import Document
            doc = Document(str(path))
            for para in doc.paragraphs[:50]:
                if para.text.strip():
                    sections.append(para.text.strip()[:500])
        except ImportError:
            print('python-docx not installed', file=sys.stderr)
            sys.exit(2)

    elif suffix in ('.xlsx', '.xls'):
        try:
            import openpyxl
            wb = openpyxl.load_workbook(str(path), read_only=True)
            ws = wb.active
            for row in ws.iter_rows(max_row=50, values_only=True):
                line = ' | '.join(str(c) for c in row if c is not None)
                if line.strip():
                    sections.append(line[:500])
        except ImportError:
            print('openpyxl not installed', file=sys.stderr)
            sys.exit(2)

    else:
        print(f'Unsupported format: {suffix}. Supported: .pdf .docx .xlsx', file=sys.stderr)
        sys.exit(2)

    return sections, entities


def main() -> None:
    parser = argparse.ArgumentParser(
        description='Parse power grid documents into structured JSON.',
        epilog='Examples:\n'
               '  python parse.py --file report.pdf\n'
               '  python parse.py --query "解析" --context-json \'{"retrieval":{}}\'',
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument('--query', default='', help='User query text')
    parser.add_argument('--file', default=None, help='Path to a local document file')
    parser.add_argument('--context-json', default='{}', help='JSON string of runtime context')
    args = parser.parse_args()

    context = json.loads(args.context_json)
    if args.file:
        context['file_path'] = args.file

    result = run(args.query, context)
    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == '__main__':
    main()
