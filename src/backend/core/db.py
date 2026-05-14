import json
import sqlite3
from datetime import datetime
from pathlib import Path
from typing import Any

from src.backend.core.config import settings
from src.backend.core.logger import get_logger

logger = get_logger(__name__)


def _connect() -> sqlite3.Connection:
    db_path: Path = settings.sqlite_path
    db_path.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    return conn


def init_db() -> None:
    conn = _connect()
    cur = conn.cursor()

    cur.execute(
        '''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            password_hash TEXT NOT NULL,
            role TEXT NOT NULL,
            created_at TEXT NOT NULL
        )
        '''
    )

    cur.execute(
        '''
        CREATE TABLE IF NOT EXISTS files (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            file_name TEXT NOT NULL,
            file_type TEXT NOT NULL,
            station_name TEXT,
            metadata_json TEXT,
            created_at TEXT NOT NULL
        )
        '''
    )

    cur.execute(
        '''
        CREATE TABLE IF NOT EXISTS build_tasks (
            task_id TEXT PRIMARY KEY,
            mode TEXT NOT NULL,
            status TEXT NOT NULL,
            progress INTEGER NOT NULL,
            logs TEXT,
            report_json TEXT,
            created_at TEXT NOT NULL,
            updated_at TEXT NOT NULL
        )
        '''
    )

    cur.execute(
        '''
        CREATE TABLE IF NOT EXISTS chat_sessions (
            session_id TEXT PRIMARY KEY,
            user_id TEXT NOT NULL,
            created_at TEXT NOT NULL
        )
        '''
    )

    cur.execute(
        '''
        CREATE TABLE IF NOT EXISTS chat_messages (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            session_id TEXT NOT NULL,
            role TEXT NOT NULL,
            content TEXT NOT NULL,
            citations_json TEXT,
            created_at TEXT NOT NULL
        )
        '''
    )

    cur.execute(
        '''
        CREATE TABLE IF NOT EXISTS system_config (
            key TEXT PRIMARY KEY,
            value TEXT NOT NULL,
            updated_at TEXT NOT NULL
        )
        '''
    )
    conn.commit()

    cur.execute('SELECT COUNT(*) AS cnt FROM users WHERE username = ?', ('admin',))
    from src.backend.core.security import hash_password

    if cur.fetchone()['cnt'] == 0:
        cur.execute(
            'INSERT INTO users (username, password_hash, role, created_at) VALUES (?, ?, ?, ?)',
            ('admin', hash_password('admin123'), 'admin', datetime.utcnow().isoformat()),
        )

    default_config = {
        'llm_api_base_url': settings.llm_api_base_url,
        'llm_api_key': settings.llm_api_key,
        'llm_model_name': settings.llm_model_name,
        'embedding_provider': settings.embedding_provider,
        'embedding_api_base_url': settings.embedding_api_base_url,
        'embedding_api_key': settings.embedding_api_key,
        'embedding_model_name': settings.embedding_model_name,
        'reranker_provider': settings.reranker_provider,
        'reranker_api_base_url': settings.reranker_api_base_url,
        'reranker_api_key': settings.reranker_api_key,
        'reranker_model_name': settings.reranker_model_name,
        'retrieve_top_n': str(settings.retrieve_top_n),
        'rerank_top_n': str(settings.rerank_top_n),
        'similarity_threshold': str(settings.similarity_threshold),
    }
    now = datetime.utcnow().isoformat()
    for key, value in default_config.items():
        val = '' if value is None else str(value)
        if val.strip() == '':
            continue
        cur.execute(
            'INSERT OR IGNORE INTO system_config (key, value, updated_at) VALUES (?, ?, ?)',
            (key, val, now),
        )

    conn.commit()
    conn.close()
    logger.info('SQLite 初始化完成')


def get_user_by_username(username: str) -> dict[str, Any] | None:
    conn = _connect()
    cur = conn.cursor()
    cur.execute('SELECT * FROM users WHERE username = ?', (username,))
    row = cur.fetchone()
    conn.close()
    return dict(row) if row else None


def create_file_record(file_name: str, file_type: str, station_name: str | None, metadata: dict[str, Any]) -> int:
    conn = _connect()
    cur = conn.cursor()
    cur.execute(
        'INSERT INTO files (file_name, file_type, station_name, metadata_json, created_at) VALUES (?, ?, ?, ?, ?)',
        (file_name, file_type, station_name, json.dumps(metadata, ensure_ascii=False), datetime.utcnow().isoformat()),
    )
    conn.commit()
    rid = cur.lastrowid
    conn.close()
    return int(rid)


def list_files(file_type: str | None = None, page: int = 1, page_size: int = 20) -> tuple[list[dict], int]:
    offset = (page - 1) * page_size
    conn = _connect()
    cur = conn.cursor()
    if file_type:
        cur.execute('SELECT COUNT(*) AS cnt FROM files WHERE file_type = ?', (file_type,))
        total = cur.fetchone()['cnt']
        cur.execute('SELECT * FROM files WHERE file_type = ? ORDER BY id DESC LIMIT ? OFFSET ?', (file_type, page_size, offset))
    else:
        cur.execute('SELECT COUNT(*) AS cnt FROM files')
        total = cur.fetchone()['cnt']
        cur.execute('SELECT * FROM files ORDER BY id DESC LIMIT ? OFFSET ?', (page_size, offset))
    rows = [dict(row) for row in cur.fetchall()]
    conn.close()
    return rows, total


def upsert_build_task(task_id: str, mode: str, status: str, progress: int, logs: str, report: dict[str, Any] | None = None) -> None:
    now = datetime.utcnow().isoformat()
    conn = _connect()
    cur = conn.cursor()
    cur.execute(
        '''
        INSERT INTO build_tasks(task_id, mode, status, progress, logs, report_json, created_at, updated_at)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        ON CONFLICT(task_id) DO UPDATE SET
            mode=excluded.mode,
            status=excluded.status,
            progress=excluded.progress,
            logs=excluded.logs,
            report_json=excluded.report_json,
            updated_at=excluded.updated_at
        ''',
        (task_id, mode, status, progress, logs, json.dumps(report, ensure_ascii=False) if report else None, now, now),
    )
    conn.commit()
    conn.close()


def get_build_task(task_id: str) -> dict[str, Any] | None:
    conn = _connect()
    cur = conn.cursor()
    cur.execute('SELECT * FROM build_tasks WHERE task_id = ?', (task_id,))
    row = cur.fetchone()
    conn.close()
    if not row:
        return None
    data = dict(row)
    if data.get('report_json'):
        data['report'] = json.loads(data['report_json'])
    return data


def get_all_config() -> dict[str, str]:
    conn = _connect()
    cur = conn.cursor()
    cur.execute('SELECT key, value FROM system_config')
    rows = cur.fetchall()
    conn.close()
    return {row['key']: row['value'] for row in rows}


def update_config(items: dict[str, str]) -> None:
    conn = _connect()
    cur = conn.cursor()
    now = datetime.utcnow().isoformat()
    for k, v in items.items():
        raw = '' if v is None else str(v)
        if raw.strip() == '':
            cur.execute('DELETE FROM system_config WHERE key = ?', (k,))
        else:
            cur.execute(
                '''
                INSERT INTO system_config (key, value, updated_at)
                VALUES (?, ?, ?)
                ON CONFLICT(key) DO UPDATE SET value=excluded.value, updated_at=excluded.updated_at
                ''',
                (k, raw, now),
            )
    conn.commit()
    conn.close()


def save_session(session_id: str, user_id: str) -> None:
    conn = _connect()
    cur = conn.cursor()
    cur.execute('INSERT OR IGNORE INTO chat_sessions (session_id, user_id, created_at) VALUES (?, ?, ?)', (session_id, user_id, datetime.utcnow().isoformat()))
    conn.commit()
    conn.close()


def list_sessions(user_id: str) -> list[dict[str, Any]]:
    conn = _connect()
    cur = conn.cursor()
    cur.execute('SELECT * FROM chat_sessions WHERE user_id = ? ORDER BY created_at DESC', (user_id,))
    rows = [dict(r) for r in cur.fetchall()]
    conn.close()
    return rows


def save_message(session_id: str, role: str, content: str, citations: list[dict[str, Any]] | None = None) -> None:
    conn = _connect()
    cur = conn.cursor()
    cur.execute(
        'INSERT INTO chat_messages (session_id, role, content, citations_json, created_at) VALUES (?, ?, ?, ?, ?)',
        (session_id, role, content, json.dumps(citations, ensure_ascii=False) if citations else None, datetime.utcnow().isoformat()),
    )
    conn.commit()
    conn.close()


def get_session_messages(session_id: str, page: int = 1, page_size: int = 20) -> list[dict[str, Any]]:
    offset = (page - 1) * page_size
    conn = _connect()
    cur = conn.cursor()
    cur.execute(
        'SELECT * FROM chat_messages WHERE session_id = ? ORDER BY id DESC LIMIT ? OFFSET ?',
        (session_id, page_size, offset),
    )
    rows = [dict(r) for r in cur.fetchall()]
    conn.close()
    data = []
    for row in reversed(rows):
        if row.get('citations_json'):
            row['citations'] = json.loads(row['citations_json'])
        data.append(row)
    return data
