from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from src.evaluation.retrieval_metrics import evaluate_retrieval_cases
from src.rag_engine.engine import run_hybrid_retrieval
from src.rag_engine.graph_retriever import retrieve_by_graph
from src.rag_engine.query_processor import preprocess_query
from src.rag_engine.sparse_retriever import retrieve_by_sparse
from src.rag_engine.vector_retriever import retrieve_by_vector


def load_cases(path: Path) -> list[dict]:
    cases = []
    for line_number, line in enumerate(path.read_text(encoding='utf-8').splitlines(), start=1):
        stripped = line.strip()
        if not stripped or stripped.startswith('#'):
            continue
        try:
            cases.append(json.loads(stripped))
        except json.JSONDecodeError as exc:
            raise ValueError(f'Invalid JSON at {path}:{line_number}') from exc
    return cases


def main() -> None:
    parser = argparse.ArgumentParser(description='Evaluate hybrid retrieval against a labelled JSONL dataset.')
    parser.add_argument('--dataset', type=Path, required=True)
    parser.add_argument('--k', type=int, default=10)
    parser.add_argument('--output', type=Path)
    parser.add_argument(
        '--strategy',
        choices=['hybrid', 'dense', 'sparse', 'graph'],
        default='hybrid',
        help='Retrieval configuration used for an ablation run.',
    )
    args = parser.parse_args()

    cases = load_cases(args.dataset)
    search_functions = {
        'hybrid': lambda query: run_hybrid_retrieval(query)['results'],
        'dense': retrieve_by_vector,
        'sparse': retrieve_by_sparse,
        'graph': lambda query: retrieve_by_graph(preprocess_query(query)),
    }
    report = evaluate_retrieval_cases(
        cases,
        search=search_functions[args.strategy],
        k=args.k,
    )
    report['configuration'] = {'strategy': args.strategy, 'k': args.k}
    rendered = json.dumps(report, ensure_ascii=False, indent=2)
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(rendered, encoding='utf-8')
    print(rendered)


if __name__ == '__main__':
    main()
