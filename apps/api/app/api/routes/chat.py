from fastapi import APIRouter, Depends, HTTPException

from app.api.dependencies import RequestContext, get_request_context
from app.domain.schemas import ChatMessageRead, ChatRecordRequest, ChatRecordResponse, EntryCreate
from app.repositories.chat_repository import ChatRepository
from app.services.ai_parser import AiParser
from app.services.assistant_reply_service import AssistantReplyService
from app.services.ledger_service import LedgerService
from app.services.llm_client import LlmError
from app.services.persona_service import PersonaService

router = APIRouter()
ai_parser = AiParser()
ledger_service = LedgerService()
reply_service = AssistantReplyService()
persona_service = PersonaService()
chat_repository = ChatRepository()


@router.get("/messages", response_model=list[ChatMessageRead])
def list_messages(
    limit: int = 200,
    context: RequestContext = Depends(get_request_context),
) -> list[ChatMessageRead]:
    return chat_repository.list_messages(context.ledger.id, context.user.id, min(max(limit, 1), 500))


@router.delete("/messages", status_code=204)
def clear_messages(context: RequestContext = Depends(get_request_context)) -> None:
    chat_repository.clear_messages(context.ledger.id, context.user.id)


@router.post("/record", response_model=ChatRecordResponse)
def record_from_chat(
    payload: ChatRecordRequest,
    context: RequestContext = Depends(get_request_context),
) -> ChatRecordResponse:
    persona = persona_service.get(context.user.id)
    chat_repository.add_message(context.ledger.id, context.user.id, "user", payload.message)
    try:
        parsed = ai_parser.parse(payload.message, payload.pending_context)
        recent_replies = [
            message.content
            for message in chat_repository.list_messages(context.ledger.id, context.user.id, 10)
            if message.role == "assistant"
        ]
        reply = reply_service.build_reply(
            parsed,
            persona,
            original_message=payload.message,
            recent_replies=recent_replies,
        )
    except LlmError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc

    if not parsed.is_complete:
        chat_repository.add_message(
            context.ledger.id, context.user.id, "assistant", reply, parsed=parsed
        )
        return ChatRecordResponse(
            assistant_name=persona.assistant_name,
            assistant_avatar=persona.avatar,
            reply=reply,
            parsed=parsed,
            needs_follow_up=True,
        )

    entry = ledger_service.create_entry(
        EntryCreate(
            ledger_id=context.ledger.id,
            type=parsed.type,
            amount=parsed.amount,
            category=parsed.category,
            subcategory=parsed.subcategory,
            description=parsed.description or parsed.category,
            occurred_at=parsed.occurred_at,
            raw_text=payload.message,
            source="llm_chat",
        ),
        context.ledger.id,
    )
    chat_repository.add_message(
        context.ledger.id, context.user.id, "assistant", reply, parsed=parsed, recorded=True
    )
    return ChatRecordResponse(
        assistant_name=persona.assistant_name,
        assistant_avatar=persona.avatar,
        reply=reply,
        entry=entry,
        parsed=parsed,
    )
