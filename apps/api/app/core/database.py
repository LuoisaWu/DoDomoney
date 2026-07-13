from contextlib import contextmanager
from pathlib import Path
import sqlite3

from app.core.config import settings


def _database_path() -> Path:
    if not settings.database_url.startswith("sqlite:///"):
        raise ValueError("Only sqlite database URLs are supported in the starter framework.")
    raw_path = settings.database_url.replace("sqlite:///", "", 1)
    return Path(raw_path)


def get_connection() -> sqlite3.Connection:
    conn = sqlite3.connect(_database_path())
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


@contextmanager
def transaction():
    conn = get_connection()
    try:
        yield conn
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


def initialize_database() -> None:
    schema_path = Path(__file__).resolve().parents[2] / "migrations" / "001_init.sql"
    with transaction() as conn:
        conn.executescript(schema_path.read_text(encoding="utf-8"))
