import hashlib
import json
from datetime import datetime
from pathlib import Path

from src.backend.core.db import create_file_record
from src.knowledge_base.data_loader.file_scanner import scan_raw_files
from src.knowledge_base.graph_builder.neo4j_writer import build_graph
from src.knowledge_base.knowledge_extraction.extractor import fake_extract_entities, fake_extract_relations
from src.knowledge_base.preprocess.parsers import parse_text, split_chunks
from src.knowledge_base.vector_store.zvec_store import build_vectors


class KnowledgeBuildPipeline:
    def __init__(self) -> None:
        self.processed_path = Path('data/processed/build_artifacts.json')

    def _load_state(self) -> dict:
        if not self.processed_path.exists():
            return {'files': []}
        return json.loads(self.processed_path.read_text(encoding='utf-8'))

    def _save_state(self, state: dict) -> None:
        self.processed_path.parent.mkdir(parents=True, exist_ok=True)
        self.processed_path.write_text(json.dumps(state, ensure_ascii=False, indent=2), encoding='utf-8')

    def run(self, mode: str = 'incremental') -> dict:
        state = self._load_state()
        known = {f['fingerprint'] for f in state.get('files', [])}

        if mode == 'full':
            known = set()
            state = {'files': []}

        files = scan_raw_files()
        chunks: list[dict] = []
        all_entities: list[dict] = []
        all_relations: list[dict] = []
        processed_count = 0

        for item in files:
            fingerprint = hashlib.md5(f"{item['path']}|{Path(item['path']).stat().st_mtime}".encode()).hexdigest()
            if fingerprint in known:
                continue

            text = parse_text(item['path'], item['file_type'])
            text_chunks = split_chunks(text)
            entities = fake_extract_entities(text, item['metadata'])
            relations = fake_extract_relations(entities)

            for idx, c in enumerate(text_chunks):
                chunk_id = f"ck-{hashlib.md5((item['path'] + str(idx)).encode()).hexdigest()[:16]}"
                chunks.append({'chunk_id': chunk_id, 'text': c, 'metadata': {'file_name': item['file_name'], **item['metadata']}})

            all_entities.extend(entities)
            all_relations.extend(relations)
            state['files'].append({'path': item['path'], 'fingerprint': fingerprint, 'updated_at': datetime.utcnow().isoformat()})
            create_file_record(item['file_name'], item['file_type'], item['metadata'].get('station_name'), item['metadata'])
            processed_count += 1

        graph_result = build_graph(all_entities, all_relations, mode=mode)
        vector_result = build_vectors(chunks)
        self._save_state(state)

        report = {
            'mode': mode,
            'processed_files': processed_count,
            'total_scanned_files': len(files),
            'chunk_count': len(chunks),
            'graph': graph_result,
            'vector': vector_result,
            'finished_at': datetime.utcnow().isoformat(),
        }
        return report
