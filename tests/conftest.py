import pytest

from src.backend.core.config import settings
from src.backend.core.db import init_db


@pytest.fixture(scope='session', autouse=True)
def initialized_test_database(tmp_path_factory):
    """Run tests against an isolated, initialized SQLite database."""
    original_path = settings.sqlite_db_path
    settings.sqlite_db_path = str(tmp_path_factory.mktemp('db') / 'test-meta.db')
    init_db()
    yield
    settings.sqlite_db_path = original_path
