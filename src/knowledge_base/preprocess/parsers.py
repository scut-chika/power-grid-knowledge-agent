"""Document parsing and structure-aware chunking helpers."""
from __future__ import annotations

import re
from pathlib import Path

import pandas as pd
from docx import Document
from pypdf import PdfReader

_OCR_ENGINE = None


def parse_pdf_units(path: str) -> list[dict]:
    units = []
    reader = PdfReader(path)
    for page_number, page in enumerate(reader.pages, start=1):
        text = (page.extract_text() or '').strip()
        if text:
            units.append(
                {
                    'text': text,
                    'metadata': {'page_number': page_number, 'parser': 'pypdf2'},
                }
            )
    return units


def parse_pdf(path: str) -> str:
    return '\n'.join(unit['text'] for unit in parse_pdf_units(path))


def parse_docx_units(path: str) -> list[dict]:
    doc = Document(path)
    units: list[dict] = []
    section = Path(path).stem
    buffer: list[str] = []

    def flush() -> None:
        if not buffer:
            return
        units.append(
            {
                'text': '\n'.join(buffer),
                'metadata': {'section': section, 'parser': 'python-docx'},
            }
        )
        buffer.clear()

    for paragraph in doc.paragraphs:
        text = paragraph.text.strip()
        if not text:
            continue
        style_name = str(getattr(paragraph.style, 'name', '') or '').lower()
        if style_name.startswith('heading'):
            flush()
            section = text
        else:
            buffer.append(text)
    flush()

    for table_index, table in enumerate(doc.tables, start=1):
        rows = []
        for row in table.rows:
            values = [cell.text.strip().replace('\n', ' ') for cell in row.cells]
            rows.append(' | '.join(values))
        content = '\n'.join(row for row in rows if row.strip(' |'))
        if content:
            units.append(
                {
                    'text': content,
                    'metadata': {
                        'section': f'表格 {table_index}',
                        'table_index': table_index,
                        'parser': 'python-docx',
                    },
                }
            )
    return units


def parse_docx(path: str) -> str:
    return '\n'.join(unit['text'] for unit in parse_docx_units(path))


def parse_table_units(path: str, rows_per_unit: int = 50) -> list[dict]:
    ext = Path(path).suffix.lower()
    if ext == '.csv':
        frame = pd.read_csv(path)
    else:
        frame = pd.read_excel(path)
    frame = frame.fillna('')

    units = []
    for start in range(0, len(frame), rows_per_unit):
        part = frame.iloc[start:start + rows_per_unit]
        units.append(
            {
                'text': part.to_csv(index=False),
                'metadata': {
                    'row_start': start + 1,
                    'row_end': start + len(part),
                    'parser': 'pandas',
                },
            }
        )
    if not units and len(frame.columns):
        units.append({'text': frame.to_csv(index=False), 'metadata': {'parser': 'pandas'}})
    return units


def parse_table(path: str) -> str:
    return '\n'.join(unit['text'] for unit in parse_table_units(path))


def parse_text_units(path: str) -> list[dict]:
    raw = Path(path).read_text(encoding='utf-8', errors='ignore')
    lines = raw.splitlines()
    units: list[dict] = []
    section = Path(path).stem
    buffer: list[str] = []
    heading_pattern = re.compile(r'^(?:#{1,6}\s+|[一二三四五六七八九十]+[、.]|\d+(?:\.\d+)*[、.\s])(.+)$')

    def flush() -> None:
        if not buffer:
            return
        content = '\n'.join(buffer).strip()
        if content:
            units.append(
                {
                    'text': content,
                    'metadata': {'section': section, 'parser': 'structured-text'},
                }
            )
        buffer.clear()

    for line in lines:
        match = heading_pattern.match(line.strip())
        if match:
            flush()
            section = match.group(1).strip() or line.strip('# ').strip()
            continue
        buffer.append(line)
    flush()
    return units


def parse_markdown_or_text(path: str) -> str:
    return '\n'.join(unit['text'] for unit in parse_text_units(path))


def parse_image_ocr(path: str) -> list[dict]:
    """Run PaddleOCR lazily when the optional OCR runtime is available."""
    global _OCR_ENGINE
    try:
        from paddleocr import PaddleOCR
    except ImportError:
        return []

    try:
        if _OCR_ENGINE is None:
            _OCR_ENGINE = PaddleOCR(use_angle_cls=True, lang='ch', show_log=False)
        raw_result = _OCR_ENGINE.ocr(path, cls=True)
    except Exception:
        return []

    lines: list[str] = []
    for page in raw_result or []:
        for item in page or []:
            if len(item) >= 2 and item[1]:
                lines.append(str(item[1][0]))
    text = '\n'.join(lines).strip()
    if not text:
        return []
    return [{'text': text, 'metadata': {'page_number': 1, 'parser': 'paddleocr'}}]


def parse_document(path: str, file_type: str) -> list[dict]:
    p = Path(path)
    ext = p.suffix.lower()
    if ext == '.pdf':
        return parse_pdf_units(path)
    if ext == '.docx':
        return parse_docx_units(path)
    if ext in {'.md', '.txt'}:
        return parse_text_units(path)
    if ext in {'.xlsx', '.xls', '.csv'}:
        return parse_table_units(path)
    if file_type == 'scans' and ext in {'.jpg', '.jpeg', '.png', '.tiff'}:
        return parse_image_ocr(path)
    return []


def parse_text(path: str, file_type: str) -> str:
    return '\n'.join(unit['text'] for unit in parse_document(path, file_type))


def split_chunks(text: str, chunk_size: int = 800, overlap: int = 120) -> list[str]:
    """Split text near paragraph/sentence boundaries with a small overlap."""
    text = text.strip()
    if not text:
        return []
    if chunk_size < 100:
        raise ValueError('chunk_size must be at least 100 characters')
    overlap = max(0, min(overlap, chunk_size // 2))

    chunks: list[str] = []
    start = 0
    while start < len(text):
        hard_end = min(len(text), start + chunk_size)
        end = hard_end
        if hard_end < len(text):
            window = text[start:hard_end]
            minimum_boundary = int(chunk_size * 0.55)
            boundary = max(
                window.rfind('\n\n'),
                window.rfind('\n'),
                window.rfind('。'),
                window.rfind('；'),
            )
            if boundary >= minimum_boundary:
                end = start + boundary + 1

        chunk = text[start:end].strip()
        if chunk:
            chunks.append(chunk)
        if end >= len(text):
            break
        start = max(start + 1, end - overlap)
        while start < len(text) and text[start].isspace():
            start += 1
    return chunks


def chunk_document_units(units: list[dict], chunk_size: int = 800, overlap: int = 120) -> list[dict]:
    """Chunk parsed units while preserving page/section provenance."""
    chunks: list[dict] = []
    for unit_index, unit in enumerate(units):
        unit_chunks = split_chunks(unit.get('text', ''), chunk_size=chunk_size, overlap=overlap)
        for local_index, content in enumerate(unit_chunks):
            chunks.append(
                {
                    'text': content,
                    'metadata': {
                        **(unit.get('metadata') or {}),
                        'unit_index': unit_index,
                        'chunk_in_unit': local_index,
                    },
                }
            )
    return chunks
