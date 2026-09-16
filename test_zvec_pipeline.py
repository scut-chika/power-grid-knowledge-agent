"""
端到端测试：PDF → 解析 → 分块 → Embedding → 写入 zvec → 向量检索
"""
import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from src.backend.core.db import init_db
from src.knowledge_base.preprocess.parsers import parse_pdf, split_chunks
from src.knowledge_base.vector_store.zvec_store import build_vectors, query_vectors

def main():
    parser = argparse.ArgumentParser(description='Run a local PDF-to-zvec smoke test.')
    parser.add_argument('--pdf', type=Path, required=True, help='Path to an authorized PDF document.')
    args = parser.parse_args()
    pdf_path = args.pdf.resolve()
    if not pdf_path.is_file():
        parser.error(f'PDF not found: {pdf_path}')

    init_db()

    print("=" * 60)
    print("Step 1: 解析 PDF")
    print("=" * 60)
    text = parse_pdf(str(pdf_path))
    print(f"  提取文本长度: {len(text)} 字符")
    print(f"  前 200 字符预览:\n  {text[:200]}\n")

    print("=" * 60)
    print("Step 2: 文本分块 (chunk_size=800)")
    print("=" * 60)
    raw_chunks = split_chunks(text, chunk_size=800)
    print(f"  分块数量: {len(raw_chunks)}")
    for i, c in enumerate(raw_chunks[:3]):
        print(f"  [chunk {i}] ({len(c)} 字符): {c[:80]}...")
    print()

    chunks = []
    for idx, c in enumerate(raw_chunks):
        chunk_id = f"test-chunk-{idx:04d}"
        chunks.append({
            'chunk_id': chunk_id,
            'text': c,
            'metadata': {
                'file_name': pdf_path.name,
                'station_name': '测试站',
                'category': '技术说明书',
            },
        })

    print("=" * 60)
    print("Step 3: Embedding + 写入 zvec")
    print("=" * 60)
    result = build_vectors(chunks)
    print(f"  写入结果: {json.dumps(result, ensure_ascii=False, indent=2)}\n")

    print("=" * 60)
    print("Step 4: 向量检索测试")
    print("=" * 60)
    test_queries = [
        "PCS-9621保护装置的功能特点",
        "站用变保护定值整定",
        "装置接线端子图",
        "过流保护动作逻辑",
    ]
    for q in test_queries:
        print(f"\n  查询: 「{q}」")
        hits = query_vectors(q, top_n=3)
        if not hits:
            print("    无命中结果")
        for i, h in enumerate(hits):
            print(f"    [{i+1}] score={h['score']:.4f}  source={h['source']}")
            print(f"        {h['content'][:100]}...")

    print("\n" + "=" * 60)
    print("测试完成!")
    print("=" * 60)


if __name__ == '__main__':
    main()
