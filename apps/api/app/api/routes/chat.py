from fastapi import APIRouter, HTTPException

from app.domain.schemas import ChatRecordRequest, ChatRecordResponse, EntryCreate
from app.services.ai_parser import AiParser
from app.services.assistant_reply_service import AssistantReplyService
from app.services.ledger_service import LedgerService

router = APIRouter()
ai_parser = AiParser()
ledger_service = LedgerService()
reply_service = AssistantReplyService()


@router.post("/record", response_model=ChatRecordResponse)
def record_from_chat(payload: ChatRecordRequest) -> ChatRecordResponse:
    try:
        parsed = ai_parser.parse(payload.message)
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc

    entry = ledger_service.create_entry(
        EntryCreate(
            type=parsed.type,
            amount=parsed.amount,
            category=parsed.category,
            subcategory=parsed.subcategory,
            description=parsed.description,
            occurred_at=parsed.occurred_at,
            raw_text=payload.message,
            source="chat",
        )
    )

    return ChatRecordResponse(
        reply=reply_service.build_reply(parsed, payload.assistant_tone),
        entry=entry,
        parsed=parsed,
    )
