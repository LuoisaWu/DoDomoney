from fastapi import APIRouter, Depends, HTTPException

from app.api.dependencies import RequestContext, get_request_context
from app.domain.schemas import ChatMessageRead, ChatRecordRequest, ChatRecordResponse, EntryCreate, LoanCreate
from app.repositories.chat_repository import ChatRepository
from app.repositories.loan_repository import LoanRepository
from app.services.ai_parser import AiParser
from app.services.assistant_reply_service import AssistantReplyService
from app.services.ledger_service import LedgerService
from app.services.llm_client import LlmError
from app.services.loan_parser import LoanParser, is_cancellation, is_confirmation, is_loan_message
from app.services.persona_service import PersonaService

router = APIRouter()
ai_parser = AiParser()
ledger_service = LedgerService()
reply_service = AssistantReplyService()
persona_service = PersonaService()
chat_repository = ChatRepository()
loan_repository = LoanRepository()
loan_parser = LoanParser()


def _loan_confirmation_reply(parsed) -> str:
    method = (
        "一次性还款"
        if parsed.repayment_months == 1
        else "等额本息" if parsed.repayment_method == "equal_payment" else "等额本金"
    )
    rate = "免息" if parsed.annual_rate == 0 else f"年利率 {parsed.annual_rate}%"
    return (
        "我已经整理好了，请确认后再入库：\n"
        f"从 {parsed.creditor} 借入 ¥{parsed.principal}；借款日 {parsed.borrowed_at.isoformat()}；"
        f"{parsed.repayment_months} 期，{rate}，{method}；首次还款日 {parsed.first_payment_date.isoformat()}。\n"
        "信息正确请回复“确认”，需要修改可以直接说，例如“借款日改成7月14日”。"
    )


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

    if payload.pending_loan or (not payload.pending_context and is_loan_message(payload.message)):
        if payload.pending_loan and is_cancellation(payload.message):
            reply = "好的，这笔借款已取消，不会写入数据库。"
            chat_repository.add_message(context.ledger.id, context.user.id, "assistant", reply)
            return ChatRecordResponse(
                assistant_name=persona.assistant_name,
                assistant_avatar=persona.avatar,
                reply=reply,
                record_type="loan",
            )
        if payload.pending_loan and payload.pending_loan.awaiting_confirmation:
            confirmed = is_confirmation(payload.message)
            parsed_loan = payload.pending_loan
        else:
            confirmed = False
            parsed_loan = None

        if not confirmed:
            try:
                parsed_loan = loan_parser.parse(payload.message, payload.pending_loan)
            except LlmError as exc:
                raise HTTPException(status_code=503, detail=str(exc)) from exc

        if not parsed_loan.is_complete:
            reply = parsed_loan.follow_up_question or "还需要补充一些借款信息。"
            chat_repository.add_message(
                context.ledger.id,
                context.user.id,
                "assistant",
                reply,
                parsed_loan=parsed_loan,
            )
            return ChatRecordResponse(
                assistant_name=persona.assistant_name,
                assistant_avatar=persona.avatar,
                reply=reply,
                record_type="loan",
                parsed_loan=parsed_loan,
                needs_follow_up=True,
            )

        if not confirmed:
            parsed_loan = parsed_loan.model_copy(update={"awaiting_confirmation": True})
            reply = _loan_confirmation_reply(parsed_loan)
            chat_repository.add_message(
                context.ledger.id,
                context.user.id,
                "assistant",
                reply,
                parsed_loan=parsed_loan,
            )
            return ChatRecordResponse(
                assistant_name=persona.assistant_name,
                assistant_avatar=persona.avatar,
                reply=reply,
                record_type="loan",
                parsed_loan=parsed_loan,
                needs_follow_up=True,
            )

        loan = loan_repository.create(
            LoanCreate(
                ledger_id=context.ledger.id,
                creditor=parsed_loan.creditor,
                borrowed_at=parsed_loan.borrowed_at,
                principal=parsed_loan.principal,
                repayment_months=parsed_loan.repayment_months,
                annual_rate=parsed_loan.annual_rate,
                repayment_method=parsed_loan.repayment_method,
                first_payment_date=parsed_loan.first_payment_date,
                note=parsed_loan.note,
            ),
            context.ledger.id,
        )
        reply = (
            f"借款已记录：从{loan.creditor}借入 ¥{loan.principal}，"
            f"共 {loan.repayment_months} 期，首次还款日 {loan.first_payment_date.isoformat()}。"
        )
        chat_repository.add_message(
            context.ledger.id,
            context.user.id,
            "assistant",
            reply,
            parsed_loan=parsed_loan,
            recorded=True,
        )
        return ChatRecordResponse(
            assistant_name=persona.assistant_name,
            assistant_avatar=persona.avatar,
            reply=reply,
            loan_id=loan.id,
            record_type="loan",
            parsed_loan=parsed_loan,
        )

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
