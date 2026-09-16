from __future__ import annotations

import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path

from src.backend.core.config import settings
from src.backend.core.db import ensure_file_record
from src.knowledge_base.data_loader.file_scanner import scan_raw_files
from src.knowledge_base.graph_builder.neo4j_writer import build_graph
from src.knowledge_base.knowledge_extraction.extractor import extract_entities, extract_relations
from src.knowledge_base.preprocess.parsers import chunk_document_units, parse_document
from src.knowledge_base.sparse_store.bm25_store import build_sparse_index
from src.knowledge_base.vector_store.zvec_store import build_vectors


class KnowledgeBuildPipeline:
    """Build consistent vector, sparse and graph indexes from the raw corpus."""

    def __init__(self) -> None:
        self.processed_path = Path('data/processed/build_artifacts.json')

    def _load_state(self) -> dict:
        if not self.processed_path.exists():
            return {'version': 2, 'files': []}
        try:
            return json.loads(self.processed_path.read_text(encoding='utf-8'))
        except (OSError, json.JSONDecodeError):
            return {'version': 2, 'files': []}

    def _save_state(self, state: dict) -> None:
        self.processed_path.parent.mkdir(parents=True, exist_ok=True)
        temp_path = self.processed_path.with_suffix('.json.tmp')
        temp_path.write_text(json.dumps(state, ensure_ascii=False, indent=2), encoding='utf-8')
        temp_path.replace(self.processed_path)

    @staticmethod
    def _fingerprint(path: str) -> str:
        stat = Path(path).stat()
        value = f'{Path(path).resolve()}|{stat.st_size}|{stat.st_mtime_ns}'
        return hashlib.sha256(value.encode('utf-8')).hexdigest()

    def run(self, mode: str = 'incremental') -> dict:
        if mode not in {'incremental', 'full'}:
            raise ValueError("mode must be 'incremental' or 'full'")

        previous_state = self._load_state()
        previous_by_path = {item['path']: item for item in previous_state.get('files', [])}
        files = scan_raw_files()
        current_paths = {item['path'] for item in files}
        removed_paths = sorted(set(previous_by_path) - current_paths)

        current_fingerprints = {item['path']: self._fingerprint(item['path']) for item in files}
        changed_files = [
            item
            for item in files
            if current_fingerprints[item['path']] != previous_by_path.get(item['path'], {}).get('fingerprint')
        ]

        vector_missing = not Path(settings.zvec_data_dir).exists()
        sparse_missing = not Path(settings.sparse_index_path).exists()
        rebuild_required = (
            mode == 'full'
            or bool(changed_files)
            or bool(removed_paths)
            or vector_missing
            or sparse_missing
        )

        chunks: list[dict] = []
        all_entities: list[dict] = []
        skipped_files: list[dict] = []
        skipped_paths: set[str] = set()

        if rebuild_required:
            for item in files:
                try:
                    units = parse_document(item['path'], item['file_type'])
                except Exception as exc:  # noqa: BLE001
                    skipped_files.append({'file_name': item['file_name'], 'reason': str(exc)})
                    skipped_paths.add(item['path'])
                    continue
                if not units:
                    skipped_files.append({'file_name': item['file_name'], 'reason': '未提取到可索引文本'})
                    skipped_paths.add(item['path'])
                    continue

                base_metadata = {
                    'file_name': item['file_name'],
                    'file_type': item['file_type'],
                    **item['metadata'],
                }
                document_id = hashlib.sha256(item['path'].encode('utf-8')).hexdigest()[:16]
                parsed_chunks = chunk_document_units(
                    units,
                    chunk_size=settings.chunk_size,
                    overlap=settings.chunk_overlap,
                )
                for sequence, parsed_chunk in enumerate(parsed_chunks):
                    chunk_digest = hashlib.sha256(
                        f"{item['path']}|{sequence}|{parsed_chunk['text']}".encode('utf-8')
                    ).hexdigest()[:20]
                    chunks.append(
                        {
                            'chunk_id': f'ck-{chunk_digest}',
                            'text': parsed_chunk['text'],
                            'metadata': {
                                **base_metadata,
                                **parsed_chunk['metadata'],
                                'document_id': document_id,
                                'chunk_sequence': sequence,
                            },
                        }
                    )

                full_text = '\n'.join(unit['text'] for unit in units)
                all_entities.extend(extract_entities(full_text, base_metadata))

                if item in changed_files:
                    ensure_file_record(
                        item['file_name'],
                        item['file_type'],
                        item['metadata'].get('station_name'),
                        {**item['metadata'], 'path': item['path']},
                    )

            all_relations = extract_relations(all_entities)
            # Rebuilding all three indexes together avoids stale or partially updated retrieval data.
            graph_result = build_graph(all_entities, all_relations, mode='full')
            vector_result = build_vectors(chunks)
            sparse_result = build_sparse_index(chunks)
        else:
            graph_result = {'status': 'unchanged'}
            vector_result = {'status': 'unchanged'}
            sparse_result = {'status': 'unchanged'}

        now = datetime.now(timezone.utc).isoformat()
        next_files = []
        for item in files:
            if item['path'] in skipped_paths:
                continue
            previous = previous_by_path.get(item['path'], {})
            next_files.append(
                {
                    'path': item['path'],
                    'fingerprint': current_fingerprints[item['path']],
                    'updated_at': now if item in changed_files else previous.get('updated_at', now),
                }
            )
        self._save_state({'version': 2, 'files': next_files})

        return {
            'mode': mode,
            'rebuild_performed': rebuild_required,
            'processed_files': len(changed_files),
            'removed_files': len(removed_paths),
            'total_scanned_files': len(files),
            'indexed_files': len(files) - len(skipped_paths) if rebuild_required else None,
            'chunk_count': len(chunks) if rebuild_required else None,
            'skipped_files': skipped_files,
            'graph': graph_result,
            'vector': vector_result,
            'sparse': sparse_result,
            'finished_at': now,
        }
