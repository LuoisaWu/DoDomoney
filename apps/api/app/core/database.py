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
        _migrate_existing_database(conn)


def _has_column(conn: sqlite3.Connection, table: str, column: str) -> bool:
    rows = conn.execute(f"PRAGMA table_info({table})").fetchall()
    return any(row["name"] == column for row in rows)


def _upgrade_persona_schema(conn: sqlite3.Connection) -> None:
    """Remove the legacy snark slider and allow the distinct witty-dark mode."""
    row = conn.execute(
        "SELECT sql FROM sqlite_master WHERE type = 'table' AND name = 'assistant_personas'"
    ).fetchone()
    table_sql = row["sql"] if row else ""
    if "snark_level" not in table_sql and "witty_dark" in table_sql:
        return

    has_snark_level = _has_column(conn, "assistant_personas", "snark_level")
    migrated_mode = (
        "CASE WHEN snark_level >= 4 THEN 'witty_dark' ELSE mode END"
        if has_snark_level
        else "mode"
    )
    conn.execute("ALTER TABLE assistant_personas RENAME TO assistant_personas_legacy")
    conn.execute(
        """
        CREATE TABLE assistant_personas (
            user_id INTEGER PRIMARY KEY REFERENCES users(id) ON DELETE CASCADE,
            assistant_name TEXT NOT NULL DEFAULT '账小喵',
            avatar TEXT NOT NULL DEFAULT '🐱',
            voice_style TEXT NOT NULL CHECK (voice_style IN ('warm', 'playful', 'direct', 'calm')) DEFAULT 'warm',
            mode TEXT NOT NULL CHECK (mode IN ('balanced', 'cute', 'rational', 'encouraging', 'witty_dark')) DEFAULT 'cute',
            reply_length TEXT NOT NULL DEFAULT 'short',
            emoji_level INTEGER NOT NULL DEFAULT 1,
            proactive_insights INTEGER NOT NULL DEFAULT 1,
            custom_instructions TEXT NOT NULL DEFAULT '',
            created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
            updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
        )
        """
    )
    conn.execute(
        f"""
        INSERT INTO assistant_personas (
            user_id, assistant_name, avatar, voice_style, mode, reply_length,
            emoji_level, proactive_insights, custom_instructions, created_at, updated_at
        )
        SELECT
            user_id, assistant_name, avatar, voice_style, {migrated_mode}, reply_length,
            emoji_level, proactive_insights, custom_instructions, created_at, updated_at
        FROM assistant_personas_legacy
        """
    )
    conn.execute("DROP TABLE assistant_personas_legacy")


def _migrate_existing_database(conn: sqlite3.Connection) -> None:
    if not _has_column(conn, "users", "password_hash"):
        conn.execute("ALTER TABLE users ADD COLUMN password_hash TEXT")
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS auth_sessions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
            token_hash TEXT NOT NULL UNIQUE,
            expires_at TEXT NOT NULL,
            created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
        )
        """
    )
    conn.execute("CREATE INDEX IF NOT EXISTS idx_auth_sessions_user ON auth_sessions (user_id)")
    conn.execute(
        "INSERT OR IGNORE INTO users (id, email, display_name) VALUES (1, 'local@dodomoney.app', '本地用户')"
    )
    conn.execute(
        "INSERT OR IGNORE INTO ledgers (id, owner_user_id, name, type) VALUES (1, 1, '个人账本', 'personal')"
    )
    conn.execute(
        "INSERT OR IGNORE INTO ledger_members (ledger_id, user_id, role) VALUES (1, 1, 'owner')"
    )
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS assistant_personas (
            user_id INTEGER PRIMARY KEY REFERENCES users(id) ON DELETE CASCADE,
            assistant_name TEXT NOT NULL DEFAULT '账小喵',
            avatar TEXT NOT NULL DEFAULT '🐱',
            voice_style TEXT NOT NULL CHECK (voice_style IN ('warm', 'playful', 'direct', 'calm')) DEFAULT 'warm',
            mode TEXT NOT NULL CHECK (mode IN ('balanced', 'cute', 'rational', 'encouraging', 'witty_dark')) DEFAULT 'cute',
            created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
            updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
        )
        """
    )
    conn.execute("INSERT OR IGNORE INTO assistant_personas (user_id) SELECT id FROM users")

    persona_columns = {
        "reply_length": "TEXT NOT NULL DEFAULT 'short'",
        "emoji_level": "INTEGER NOT NULL DEFAULT 1",
        "proactive_insights": "INTEGER NOT NULL DEFAULT 1",
        "custom_instructions": "TEXT NOT NULL DEFAULT ''",
    }
    for column, definition in persona_columns.items():
        if not _has_column(conn, "assistant_personas", column):
            conn.execute(f"ALTER TABLE assistant_personas ADD COLUMN {column} {definition}")
    _upgrade_persona_schema(conn)

    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS chat_messages (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            ledger_id INTEGER NOT NULL REFERENCES ledgers(id) ON DELETE CASCADE,
            user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
            role TEXT NOT NULL CHECK (role IN ('user', 'assistant')),
            content TEXT NOT NULL,
            parsed_json TEXT,
            recorded INTEGER NOT NULL DEFAULT 0,
            created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
        )
        """
    )
    conn.execute(
        "CREATE INDEX IF NOT EXISTS idx_chat_messages_context ON chat_messages (ledger_id, user_id, id)"
    )

    if not _has_column(conn, "entries", "ledger_id"):
        conn.execute("ALTER TABLE entries ADD COLUMN ledger_id INTEGER NOT NULL DEFAULT 1")
    if not _has_column(conn, "budgets", "ledger_id"):
        conn.execute("ALTER TABLE budgets ADD COLUMN ledger_id INTEGER NOT NULL DEFAULT 1")
    if not _has_column(conn, "category_preferences", "user_id"):
        conn.execute("ALTER TABLE category_preferences ADD COLUMN user_id INTEGER NOT NULL DEFAULT 1")

    conn.execute(
        "CREATE INDEX IF NOT EXISTS idx_entries_ledger_occurred_at ON entries (ledger_id, occurred_at)"
    )
    conn.execute(
        "CREATE INDEX IF NOT EXISTS idx_entries_ledger_category ON entries (ledger_id, category)"
    )
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS loans (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            ledger_id INTEGER NOT NULL REFERENCES ledgers(id) ON DELETE CASCADE,
            creditor TEXT NOT NULL,
            borrowed_at TEXT NOT NULL,
            principal TEXT NOT NULL,
            repayment_months INTEGER NOT NULL CHECK (repayment_months > 0),
            annual_rate TEXT NOT NULL DEFAULT '0',
            repayment_method TEXT NOT NULL CHECK (repayment_method IN ('equal_payment', 'equal_principal')) DEFAULT 'equal_payment',
            first_payment_date TEXT NOT NULL,
            note TEXT NOT NULL DEFAULT '',
            created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
            updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
        )
        """
    )
    conn.execute(
        "CREATE INDEX IF NOT EXISTS idx_loans_ledger_borrowed_at ON loans (ledger_id, borrowed_at DESC)"
    )
