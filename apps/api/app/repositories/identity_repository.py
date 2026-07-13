from datetime import datetime, timedelta, timezone
from typing import Any

from app.core.database import transaction
from app.domain.enums import LedgerRole, LedgerType
from app.domain.schemas import (
    LedgerCreate,
    LedgerMemberCreate,
    LedgerMemberRead,
    LedgerRead,
    UserCreate,
    UserRead,
    UserUpdate,
)


def _row_to_user(row: Any) -> UserRead:
    return UserRead(
        id=row["id"],
        email=row["email"],
        display_name=row["display_name"],
        avatar_url=row["avatar_url"],
        created_at=datetime.fromisoformat(row["created_at"]),
        updated_at=datetime.fromisoformat(row["updated_at"]),
    )


def _row_to_ledger(row: Any) -> LedgerRead:
    return LedgerRead(
        id=row["id"],
        owner_user_id=row["owner_user_id"],
        name=row["name"],
        type=LedgerType(row["type"]),
        role=LedgerRole(row["role"]),
        member_count=int(row["member_count"]),
        created_at=datetime.fromisoformat(row["created_at"]),
        updated_at=datetime.fromisoformat(row["updated_at"]),
    )


def _row_to_member(row: Any) -> LedgerMemberRead:
    return LedgerMemberRead(
        id=row["id"],
        ledger_id=row["ledger_id"],
        user_id=row["user_id"],
        email=row["email"],
        display_name=row["display_name"],
        role=LedgerRole(row["role"]),
        created_at=datetime.fromisoformat(row["created_at"]),
    )


class IdentityRepository:
    def get_default_context(self) -> tuple[UserRead, LedgerRead]:
        user = self.get_user(1)
        ledgers = self.list_ledgers(1)
        if user is None or not ledgers:
            raise RuntimeError("Default Dodomoney user or ledger is missing.")
        return user, ledgers[0]

    def get_user(self, user_id: int) -> UserRead | None:
        with transaction() as conn:
            row = conn.execute("SELECT * FROM users WHERE id = ?", (user_id,)).fetchone()
        return _row_to_user(row) if row else None

    def get_user_by_email(self, email: str) -> UserRead | None:
        with transaction() as conn:
            row = conn.execute("SELECT * FROM users WHERE lower(email) = lower(?)", (email,)).fetchone()
        return _row_to_user(row) if row else None

    def get_password_hash(self, email: str) -> str | None:
        with transaction() as conn:
            row = conn.execute(
                "SELECT password_hash FROM users WHERE lower(email) = lower(?)", (email.strip(),)
            ).fetchone()
        return row["password_hash"] if row else None

    def set_password_hash(self, user_id: int, password_hash: str) -> None:
        with transaction() as conn:
            conn.execute(
                "UPDATE users SET password_hash = ?, updated_at = CURRENT_TIMESTAMP WHERE id = ?",
                (password_hash, user_id),
            )

    def create_session(self, user_id: int, token_hash: str) -> None:
        expires_at = datetime.now(timezone.utc) + timedelta(days=30)
        with transaction() as conn:
            conn.execute("DELETE FROM auth_sessions WHERE expires_at <= ?", (datetime.now(timezone.utc).isoformat(),))
            conn.execute(
                "INSERT INTO auth_sessions (user_id, token_hash, expires_at) VALUES (?, ?, ?)",
                (user_id, token_hash, expires_at.isoformat()),
            )

    def get_user_by_session(self, token_hash: str) -> UserRead | None:
        now = datetime.now(timezone.utc).isoformat()
        with transaction() as conn:
            row = conn.execute(
                """
                SELECT u.* FROM auth_sessions s
                JOIN users u ON u.id = s.user_id
                WHERE s.token_hash = ? AND s.expires_at > ?
                """,
                (token_hash, now),
            ).fetchone()
        return _row_to_user(row) if row else None

    def delete_session(self, token_hash: str) -> None:
        with transaction() as conn:
            conn.execute("DELETE FROM auth_sessions WHERE token_hash = ?", (token_hash,))

    def create_user(self, payload: UserCreate) -> UserRead:
        with transaction() as conn:
            cursor = conn.execute(
                """
                INSERT INTO users (email, display_name, avatar_url)
                VALUES (?, ?, ?)
                """,
                (payload.email.strip().lower(), payload.display_name.strip(), payload.avatar_url),
            )
            user_id = cursor.lastrowid
            conn.execute(
                """
                INSERT INTO ledgers (owner_user_id, name, type)
                VALUES (?, ?, 'personal')
                """,
                (user_id, f"{payload.display_name.strip()}的个人账本"),
            )
            ledger_id = conn.execute("SELECT last_insert_rowid() AS id").fetchone()["id"]
            conn.execute(
                "INSERT INTO ledger_members (ledger_id, user_id, role) VALUES (?, ?, 'owner')",
                (ledger_id, user_id),
            )
            row = conn.execute("SELECT * FROM users WHERE id = ?", (user_id,)).fetchone()
            conn.execute("INSERT OR IGNORE INTO assistant_personas (user_id) VALUES (?)", (user_id,))
        return _row_to_user(row)

    def upsert_user_by_email(self, email: str, display_name: str | None = None) -> UserRead:
        existing = self.get_user_by_email(email)
        if existing:
            return existing
        fallback_name = display_name or email.split("@", 1)[0]
        return self.create_user(UserCreate(email=email, display_name=fallback_name))

    def list_users(self) -> list[UserRead]:
        with transaction() as conn:
            rows = conn.execute("SELECT * FROM users ORDER BY created_at DESC, id DESC").fetchall()
        return [_row_to_user(row) for row in rows]

    def update_user(self, user_id: int, payload: UserUpdate) -> UserRead:
        current = self.get_user(user_id)
        if current is None:
            raise RuntimeError("User not found.")
        display_name = payload.display_name.strip() if payload.display_name is not None else current.display_name
        avatar_url = payload.avatar_url if payload.avatar_url is not None else current.avatar_url
        with transaction() as conn:
            conn.execute(
                "UPDATE users SET display_name = ?, avatar_url = ?, updated_at = CURRENT_TIMESTAMP WHERE id = ?",
                (display_name, avatar_url, user_id),
            )
            row = conn.execute("SELECT * FROM users WHERE id = ?", (user_id,)).fetchone()
        return _row_to_user(row)

    def list_ledgers(self, user_id: int) -> list[LedgerRead]:
        with transaction() as conn:
            rows = conn.execute(
                """
                SELECT l.*, lm.role, COUNT(all_members.id) AS member_count
                FROM ledgers l
                JOIN ledger_members lm ON lm.ledger_id = l.id AND lm.user_id = ?
                LEFT JOIN ledger_members all_members ON all_members.ledger_id = l.id
                GROUP BY l.id, lm.role
                ORDER BY l.updated_at DESC, l.id DESC
                """,
                (user_id,),
            ).fetchall()
        return [_row_to_ledger(row) for row in rows]

    def get_ledger_for_user(self, ledger_id: int, user_id: int) -> LedgerRead | None:
        ledgers = [ledger for ledger in self.list_ledgers(user_id) if ledger.id == ledger_id]
        return ledgers[0] if ledgers else None

    def create_ledger(self, owner_user_id: int, payload: LedgerCreate) -> LedgerRead:
        with transaction() as conn:
            cursor = conn.execute(
                "INSERT INTO ledgers (owner_user_id, name, type) VALUES (?, ?, ?)",
                (owner_user_id, payload.name.strip(), payload.type.value),
            )
            ledger_id = cursor.lastrowid
            conn.execute(
                "INSERT INTO ledger_members (ledger_id, user_id, role) VALUES (?, ?, 'owner')",
                (ledger_id, owner_user_id),
            )
        ledger = self.get_ledger_for_user(ledger_id, owner_user_id)
        if ledger is None:
            raise RuntimeError("Created ledger cannot be loaded.")
        return ledger

    def list_members(self, ledger_id: int, user_id: int) -> list[LedgerMemberRead]:
        if self.get_ledger_for_user(ledger_id, user_id) is None:
            return []
        with transaction() as conn:
            rows = conn.execute(
                """
                SELECT lm.*, u.email, u.display_name
                FROM ledger_members lm
                JOIN users u ON u.id = lm.user_id
                WHERE lm.ledger_id = ?
                ORDER BY lm.role ASC, lm.created_at ASC
                """,
                (ledger_id,),
            ).fetchall()
        return [_row_to_member(row) for row in rows]

    def add_member(self, ledger_id: int, actor_user_id: int, payload: LedgerMemberCreate) -> LedgerMemberRead | None:
        ledger = self.get_ledger_for_user(ledger_id, actor_user_id)
        if ledger is None or ledger.role == LedgerRole.MEMBER:
            return None
        user = self.upsert_user_by_email(payload.email, payload.display_name)
        with transaction() as conn:
            conn.execute(
                """
                INSERT INTO ledger_members (ledger_id, user_id, role)
                VALUES (?, ?, ?)
                ON CONFLICT(ledger_id, user_id) DO UPDATE SET role = excluded.role
                """,
                (ledger_id, user.id, payload.role.value),
            )
        members = [member for member in self.list_members(ledger_id, actor_user_id) if member.user_id == user.id]
        return members[0] if members else None
