"""Shared test fixtures for TaskOps tests.
테스트 공통 fixture.
"""
import os
import tempfile
import pytest
from cli.db.connection import get_connection, close_connection


@pytest.fixture
def tmp_db():
    """Provide a temporary DB connection with schema initialized.
    스키마 초기화된 임시 DB 연결 제공.
    """
    with tempfile.NamedTemporaryFile(suffix='.db', delete=False) as f:
        db_path = f.name
    conn = get_connection(db_path)
    yield conn, db_path
    close_connection(conn)
    os.unlink(db_path)


@pytest.fixture
def tmp_project_dir():
    """Provide a temporary project directory.
    임시 프로젝트 디렉토리 제공.
    """
    with tempfile.TemporaryDirectory() as tmpdir:
        yield tmpdir
