import shutil
from pathlib import Path
from typing import Annotated

from fastapi import APIRouter, Depends, File, Query, UploadFile

from src.backend.core.db import create_file_record, list_files
from src.backend.core.security import get_current_user

router = APIRouter()

RAW_ROOT = Path('data/raw')
TYPE_MAP = {
    'documents': 'documents',
    'tables': 'tables',
    'drawings': 'drawings',
    'scans': 'scans',
}


@router.post('/upload')
def upload_data(
    files: list[UploadFile] = File(...),
    file_type: str = Query('documents'),
    user: Annotated[dict, Depends(get_current_user)] = None,
) -> dict:
    target = RAW_ROOT / TYPE_MAP.get(file_type, 'documents')
    target.mkdir(parents=True, exist_ok=True)

    saved = []
    for f in files:
        safe_name = f.filename or 'unnamed'
        path = target / safe_name
        with path.open('wb') as out:
            shutil.copyfileobj(f.file, out)
        meta = {'uploaded_by_api': True, 'path': str(path), 'uploader': user['username']}
        rid = create_file_record(safe_name, file_type, None, meta)
        saved.append({'id': rid, 'file_name': safe_name, 'path': str(path)})

    return {'code': 0, 'message': 'ok', 'data': {'items': saved}}


@router.get('/list')
def get_file_list(
    file_type: str | None = Query(default=None),
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
    _: Annotated[dict, Depends(get_current_user)] = None,
) -> dict:
    items, total = list_files(file_type=file_type, page=page, page_size=page_size)
    return {
        'code': 0,
        'message': 'ok',
        'data': {
            'items': items,
            'pagination': {'page': page, 'page_size': page_size, 'total': total},
        },
    }
