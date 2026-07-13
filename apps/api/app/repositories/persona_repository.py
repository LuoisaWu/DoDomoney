from datetime import datetime
from typing import Any

from app.core.database import transaction
from app.domain.enums import PersonaMode, VoiceStyle
from app.domain.schemas import AssistantPersonaRead, AssistantPersonaUpdate


def _row_to_persona(row: Any) -> AssistantPersonaRead:
    return AssistantPersonaRead(
        user_id=row["user_id"],
        assistant_name=row["assistant_name"],
        avatar=row["avatar"],
        voice_style=VoiceStyle(row["voice_style"]),
        snark_level=row["snark_level"],
        mode=PersonaMode(row["mode"]),
        reply_length=row["reply_length"],
        emoji_level=row["emoji_level"],
        proactive_insights=bool(row["proactive_insights"]),
        custom_instructions=row["custom_instructions"],
        created_at=datetime.fromisoformat(row["created_at"]),
        updated_at=datetime.fromisoformat(row["updated_at"]),
    )


class PersonaRepository:
    def get_for_user(self, user_id: int) -> AssistantPersonaRead:
        with transaction() as conn:
            conn.execute("INSERT OR IGNORE INTO assistant_personas (user_id) VALUES (?)", (user_id,))
            row = conn.execute("SELECT * FROM assistant_personas WHERE user_id = ?", (user_id,)).fetchone()
        if row is None:
            raise RuntimeError("Assistant persona could not be loaded.")
        return _row_to_persona(row)

    def update_for_user(self, user_id: int, payload: AssistantPersonaUpdate) -> AssistantPersonaRead:
        with transaction() as conn:
            conn.execute("INSERT OR IGNORE INTO assistant_personas (user_id) VALUES (?)", (user_id,))
            conn.execute(
                """
                UPDATE assistant_personas
                SET assistant_name = ?, avatar = ?, voice_style = ?, snark_level = ?, mode = ?,
                    reply_length = ?, emoji_level = ?, proactive_insights = ?, custom_instructions = ?,
                    updated_at = CURRENT_TIMESTAMP
                WHERE user_id = ?
                """,
                (
                    payload.assistant_name.strip(),
                    payload.avatar.strip(),
                    payload.voice_style.value,
                    payload.snark_level,
                    payload.mode.value,
                    payload.reply_length,
                    payload.emoji_level,
                    int(payload.proactive_insights),
                    payload.custom_instructions.strip(),
                    user_id,
                ),
            )
            row = conn.execute("SELECT * FROM assistant_personas WHERE user_id = ?", (user_id,)).fetchone()
        return _row_to_persona(row)
