import json
import sqlite3
from pathlib import Path
from typing import Any

BASE_DIR = Path(__file__).resolve().parent
DATABASE_PATH = BASE_DIR / "game_analysis.db"
DATA_PATH = BASE_DIR / "data" / "games.json"

LIST_FIELDS = {"tags", "gameplay_features", "target_users", "advantages", "disadvantages"}


def get_connection() -> sqlite3.Connection:
    connection = sqlite3.connect(DATABASE_PATH)
    connection.row_factory = sqlite3.Row
    return connection


def initialize_database() -> None:
    database_is_new = not DATABASE_PATH.exists()
    with get_connection() as connection:
        connection.execute(
            """
            CREATE TABLE IF NOT EXISTS games (
                id INTEGER PRIMARY KEY,
                name TEXT NOT NULL UNIQUE,
                platform TEXT NOT NULL,
                genre TEXT NOT NULL,
                tags TEXT NOT NULL,
                developer TEXT NOT NULL,
                publisher TEXT NOT NULL,
                release_date TEXT NOT NULL,
                price REAL NOT NULL,
                rating REAL NOT NULL,
                review_count INTEGER NOT NULL,
                positive_rate INTEGER NOT NULL,
                description TEXT NOT NULL,
                gameplay_features TEXT NOT NULL,
                target_users TEXT NOT NULL,
                advantages TEXT NOT NULL,
                disadvantages TEXT NOT NULL
            )
            """
        )
        row_count = connection.execute("SELECT COUNT(*) FROM games").fetchone()[0]
        if database_is_new or row_count == 0:
            _seed_games(connection)


def _seed_games(connection: sqlite3.Connection) -> None:
    with DATA_PATH.open("r", encoding="utf-8") as file:
        games = json.load(file)
    columns = list(games[0].keys())
    placeholders = ", ".join("?" for _ in columns)
    sql = f"INSERT OR REPLACE INTO games ({', '.join(columns)}) VALUES ({placeholders})"
    for game in games:
        values = [json.dumps(game[key], ensure_ascii=False) if key in LIST_FIELDS else game[key] for key in columns]
        connection.execute(sql, values)


def _row_to_game(row: sqlite3.Row) -> dict[str, Any]:
    game = dict(row)
    for field in LIST_FIELDS:
        game[field] = json.loads(game[field])
    return game


def get_all_games() -> list[dict[str, Any]]:
    with get_connection() as connection:
        rows = connection.execute("SELECT * FROM games ORDER BY id").fetchall()
    return [_row_to_game(row) for row in rows]


def get_game(game_id: int) -> dict[str, Any] | None:
    with get_connection() as connection:
        row = connection.execute("SELECT * FROM games WHERE id = ?", (game_id,)).fetchone()
    return _row_to_game(row) if row else None
