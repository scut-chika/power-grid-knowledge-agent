from pathlib import Path

RAW_BASE = Path('data/raw')

SUPPORTED = {
    'documents': {'.pdf', '.docx', '.md', '.txt'},
    'tables': {'.xlsx', '.xls', '.csv'},
    'drawings': {'.pdf'},
    'scans': {'.jpg', '.jpeg', '.png', '.tiff'},
}


def parse_filename_metadata(filename: str) -> dict:
    stem = Path(filename).stem
    parts = stem.split('-')
    data = {
        'station_name': parts[0] if len(parts) > 0 else None,
        'category': parts[1] if len(parts) > 1 else None,
        'name': parts[2] if len(parts) > 2 else stem,
    }
    return data


def scan_raw_files() -> list[dict]:
    results: list[dict] = []
    for sub, exts in SUPPORTED.items():
        folder = RAW_BASE / sub
        if not folder.exists():
            continue
        for path in folder.rglob('*'):
            if not path.is_file():
                continue
            if path.suffix.lower() not in exts:
                continue
            meta = parse_filename_metadata(path.name)
            results.append(
                {
                    'path': str(path),
                    'file_name': path.name,
                    'file_type': sub,
                    'metadata': meta,
                }
            )
    return results
