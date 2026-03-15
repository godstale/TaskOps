"""Database connection management.
DB 연결 관리 모듈.
"""
import sqlite3
from .schema import create_tables


def get_connection(db_path):
    """Open (or create) DB and ensure schema exists.
    DB를 열고 (또는 생성하고) 스키마가 존재하는지 확인.
    """
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL;")
    conn.execute("PRAGMA foreign_keys=ON;")
    create_tables(conn)
    return conn


def close_connection(conn):
    """Close DB connection.
    DB 연결 종료.
    """
    if conn:
        conn.close()
