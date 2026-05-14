from pathlib import Path

import pandas as pd
from docx import Document
from PyPDF2 import PdfReader


def parse_pdf(path: str) -> str:
    text = []
    reader = PdfReader(path)
    for page in reader.pages:
        text.append(page.extract_text() or '')
    return '\n'.join(text)


def parse_docx(path: str) -> str:
    doc = Document(path)
    return '\n'.join([p.text for p in doc.paragraphs])


def parse_table(path: str) -> str:
    ext = Path(path).suffix.lower()
    if ext == '.csv':
        df = pd.read_csv(path)
    else:
        df = pd.read_excel(path)
    return df.fillna('').to_csv(index=False)


def parse_markdown_or_text(path: str) -> str:
    return Path(path).read_text(encoding='utf-8', errors='ignore')


def parse_text(path: str, file_type: str) -> str:
    p = Path(path)
    ext = p.suffix.lower()
    if ext == '.pdf':
        return parse_pdf(path)
    if ext == '.docx':
        return parse_docx(path)
    if ext in {'.md', '.txt'}:
        return parse_markdown_or_text(path)
    if ext in {'.xlsx', '.xls', '.csv'}:
        return parse_table(path)
    if file_type in {'drawings', 'scans'}:
        return f'[OCR_PLACEHOLDER]{p.name}'
    return ''


def split_chunks(text: str, chunk_size: int = 800) -> list[str]:
    text = text.strip()
    if not text:
        return []
    chunks = []
    start = 0
    while start < len(text):
        end = min(len(text), start + chunk_size)
        chunks.append(text[start:end])
        start = end
    return chunks
