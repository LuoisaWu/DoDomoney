from pathlib import Path

from fastapi import APIRouter, Depends, HTTPException

from app.api.dependencies import RequestContext, get_request_context
from app.domain.schemas import ChatMessageRead, ChatRecordRequest, ChatRecordResponse, DocumentOcrContext, EntryCreate, LoanCreate, ReimbursementCreate
from app.api.routes.uploads import ALLOWED_TYPES, UPLOAD_DIR, vision_service
from app.repositories.chat_repository import ChatRepository
from app.repositories.loan_repository import LoanRepository
from app.repositories.reimbursement_repository import ReimbursementRepository
from app.services.ai_parser import AiParser
from app.services.assistant_reply_service import AssistantReplyService
from app.services.identity_service import IdentityService
from app.services.ledger_target_service import extract_ledger_directive, find_accessible_ledger
from app.services.ledger_service import LedgerService
from app.services.llm_client import LlmError
from app.services.loan_parser import LoanParser, is_cancellation, is_confirmation, is_loan_message
from app.services.persona_service import PersonaService
from app.services.reimbursement_parser import ReimbursementParser, is_reimbursement_message

router = APIRouter()
ai_parser = AiParser()
ledger_service = LedgerService()
reply_service = AssistantReplyService()
persona_service = PersonaService()
chat_repository = ChatRepository()
loan_repository = LoanRepository()
loan_parser = LoanParser()
reimbursement_repository = ReimbursementRepository()
reimbursement_parser = ReimbursementParser()
identity_service = IdentityService()


def _loan_confirmation_reply(parsed) -> str:
    method = (
        "一次性还款"
        if parsed.repayment_months == 1
        else "等额本息" if parsed.repayment_method == "equal_payment" else "等额本金"
    )
    rate = "免息" if parsed.annual_rate == 0 else f"年利率 {parsed.annual_rate}%"
    ledger_line = f"\n目标账本：“{parsed.target_ledger_name}”。" if parsed.target_ledger_name else ""
    return (
        "我已经整理好了，请确认后再入库：\n"
        f"从 {parsed.creditor} 借入 ¥{parsed.principal}；借款日 {parsed.borrowed_at.isoformat()}；"
        f"{parsed.repayment_months} 期，{rate}，{method}；首次还款日 {parsed.first_payment_date.isoformat()}。"
        f"{ledger_line}\n"
        "信息正确请回复“确认”，需要修改可以直接说，例如“借款日改成7月14日”。"
    )


def _reimbursement_confirmation_reply(parsed) -> str:
    invoice_number = f"，发票号 {parsed.invoice_number}" if parsed.invoice_number else ""
    invoice_title = f"\n发票抬头：{parsed.invoice_title}。" if parsed.invoice_title else ""
    ledger_line = f"\n目标账本：“{parsed.target_ledger_name}”。" if parsed.target_ledger_name else ""
    return (
        "我已整理好这笔报销，请确认后再入库：\n"
        f"{parsed.invoice_date.isoformat()} · 开具单位：{parsed.merchant} · ¥{parsed.amount} · {parsed.category}{invoice_number}。"
        f"{invoice_title}"
        f"{ledger_line}\n"
        "信息正确请回复“确认”，需要修改可以直接告诉我。"
    )


def _pending_target(payload: ChatRecordRequest) -> tuple[int | None, str | None]:
    pending = payload.pending_reimbursement or payload.pending_loan or payload.pending_context
    if pending is None:
        return None, None
    return pending.target_ledger_id, pending.target_ledger_name


def _record_type_for(payload: ChatRecordRequest) -> str:
    if payload.pending_reimbursement:
        return "reimbursement"
    if payload.pending_loan:
        return "loan"
    return "transaction"


def _target_update(ledger) -> dict[str, object]:
    return {"target_ledger_id": ledger.id, "target_ledger_name": ledger.name}


def _complete_image_context(image_context: DocumentOcrContext | None) -> DocumentOcrContext | None:
    if image_context is None or image_context.status == "completed":
        return image_context
    prefix = "/media/"
    if not image_context.image_url.startswith(prefix):
        raise HTTPException(status_code=400, detail="单据图片地址无效，请重新选择图片。")
    filename = image_context.image_url.removeprefix(prefix)
    if Path(filename).name != filename or not filename.startswith("document-"):
        raise HTTPException(status_code=400, detail="单据图片地址无效，请重新选择图片。")
    image_path = (UPLOAD_DIR / filename).resolve()
    if image_path.parent != UPLOAD_DIR.resolve() or not image_path.is_file():
        raise HTTPException(status_code=400, detail="单据图片不存在，请重新选择图片。")
    content_type = next(
        (mime for mime, suffix in ALLOWED_TYPES.items() if suffix == image_path.suffix.lower()),
        "application/octet-stream",
    )
    try:
        result = vision_service.analyze(image_path.read_bytes(), content_type)
    except LlmError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc
    return image_context.model_copy(update={
        "extracted_text": result.extracted_text,
        "document_type": result.document_type,
        "confidence": result.confidence,
        "status": result.status,
    })


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
    image_context = _complete_image_context(payload.image_context)
    image_url = image_context.image_url if image_context else None
    chat_repository.add_message(context.ledger.id, context.user.id, "user", payload.message, image_url=image_url)
    directive = extract_ledger_directive(payload.message)
    accessible_ledgers = identity_service.list_ledgers(context.user.id)
    pending_target_id, pending_target_name = _pending_target(payload)
    target_ledger = None
    if directive:
        target_ledger = find_accessible_ledger(directive.ledger_name, accessible_ledgers)
        if target_ledger is None:
            reply = f"您说的“{directive.ledger_name}”账本不存在，或者您没有访问权限，请先在“用户与账本”中创建或加入该账本。"
            chat_repository.add_message(context.ledger.id, context.user.id, "assistant", reply)
            return ChatRecordResponse(
                assistant_name=persona.assistant_name,
                assistant_avatar=persona.avatar,
                reply=reply,
                record_type=_record_type_for(payload),
            )
    elif pending_target_id is not None:
        target_ledger = next((ledger for ledger in accessible_ledgers if ledger.id == pending_target_id), None)
        if target_ledger is None:
            reply = f"之前指定的“{pending_target_name or '目标'}”账本已不存在，或者您已没有访问权限，请重新指定账本。"
            chat_repository.add_message(context.ledger.id, context.user.id, "assistant", reply)
            return ChatRecordResponse(
                assistant_name=persona.assistant_name,
                assistant_avatar=persona.avatar,
                reply=reply,
                record_type=_record_type_for(payload),
            )
    else:
        target_ledger = context.ledger

    effective_message = directive.remaining_message if directive else payload.message
    if not effective_message:
        effective_message = "记录一笔账"
    if image_context and image_context.extracted_text:
        effective_message = f"图片 OCR 文字：{image_context.extracted_text}\n用户补充：{effective_message}"

    is_image_invoice = bool(image_context and image_context.document_type == "invoice")
    if payload.pending_reimbursement or (
        not payload.pending_context and not payload.pending_loan and (is_image_invoice or is_reimbursement_message(effective_message))
    ):
        if payload.pending_reimbursement and is_cancellation(payload.message):
            reply = "好的，这笔发票报销已取消，不会写入数据库。"
            chat_repository.add_message(context.ledger.id, context.user.id, "assistant", reply)
            return ChatRecordResponse(
                assistant_name=persona.assistant_name, assistant_avatar=persona.avatar,
                reply=reply, record_type="reimbursement",
            )
        if payload.pending_reimbursement and payload.pending_reimbursement.awaiting_confirmation:
            confirmed = is_confirmation(payload.message)
            parsed_reimbursement = payload.pending_reimbursement
        else:
            confirmed = False
            parsed_reimbursement = None
        if not confirmed:
            try:
                parsed_reimbursement = reimbursement_parser.parse(effective_message, payload.pending_reimbursement)
            except LlmError as exc:
                raise HTTPException(status_code=503, detail=str(exc)) from exc
            if image_url:
                parsed_reimbursement = parsed_reimbursement.model_copy(update={"image_url": image_url})
        parsed_reimbursement = parsed_reimbursement.model_copy(update=_target_update(target_ledger))
        if not parsed_reimbursement.is_complete:
            reply = parsed_reimbursement.follow_up_question or "还需要补充一些报销信息。"
            chat_repository.add_message(
                context.ledger.id, context.user.id, "assistant", reply,
                parsed_reimbursement=parsed_reimbursement,
            )
            return ChatRecordResponse(
                assistant_name=persona.assistant_name, assistant_avatar=persona.avatar,
                reply=reply, record_type="reimbursement", parsed_reimbursement=parsed_reimbursement,
                needs_follow_up=True,
            )
        if not confirmed:
            parsed_reimbursement = parsed_reimbursement.model_copy(update={"awaiting_confirmation": True})
            reply = _reimbursement_confirmation_reply(parsed_reimbursement)
            chat_repository.add_message(
                context.ledger.id, context.user.id, "assistant", reply,
                parsed_reimbursement=parsed_reimbursement,
            )
            return ChatRecordResponse(
                assistant_name=persona.assistant_name, assistant_avatar=persona.avatar,
                reply=reply, record_type="reimbursement", parsed_reimbursement=parsed_reimbursement,
                needs_follow_up=True,
            )
        parsed_reimbursement = parsed_reimbursement.model_copy(update={"awaiting_confirmation": False})
        item = reimbursement_repository.create(ReimbursementCreate(
            ledger_id=target_ledger.id, merchant=parsed_reimbursement.merchant,
            invoice_title=parsed_reimbursement.invoice_title,
            amount=parsed_reimbursement.amount, invoice_date=parsed_reimbursement.invoice_date,
            category=parsed_reimbursement.category, invoice_number=parsed_reimbursement.invoice_number,
            status=parsed_reimbursement.status, note=parsed_reimbursement.note, image_url=parsed_reimbursement.image_url,
        ), target_ledger.id)
        reply = f"报销已记录到“{target_ledger.name}”账本：{item.merchant} ¥{item.amount}，状态为待报销。"
        chat_repository.add_message(
            context.ledger.id, context.user.id, "assistant", reply,
            parsed_reimbursement=parsed_reimbursement, recorded=True,
        )
        return ChatRecordResponse(
            assistant_name=persona.assistant_name, assistant_avatar=persona.avatar,
            reply=reply, reimbursement_id=item.id, record_type="reimbursement",
            parsed_reimbursement=parsed_reimbursement,
        )

    is_image_loan = bool(image_context and image_context.document_type == "loan_note")
    if payload.pending_loan or (not payload.pending_context and (is_image_loan or is_loan_message(effective_message))):
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
                parsed_loan = loan_parser.parse(effective_message, payload.pending_loan)
            except LlmError as exc:
                raise HTTPException(status_code=503, detail=str(exc)) from exc
        parsed_loan = parsed_loan.model_copy(update=_target_update(target_ledger))

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

        parsed_loan = parsed_loan.model_copy(update={"awaiting_confirmation": False})
        loan = loan_repository.create(
            LoanCreate(
                ledger_id=target_ledger.id,
                creditor=parsed_loan.creditor,
                borrowed_at=parsed_loan.borrowed_at,
                principal=parsed_loan.principal,
                repayment_months=parsed_loan.repayment_months,
                annual_rate=parsed_loan.annual_rate,
                repayment_method=parsed_loan.repayment_method,
                first_payment_date=parsed_loan.first_payment_date,
                note=parsed_loan.note,
            ),
            target_ledger.id,
        )
        reply = (
            f"借款已记录到“{target_ledger.name}”账本：从{loan.creditor}借入 ¥{loan.principal}，"
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
        parsed = ai_parser.parse(effective_message, payload.pending_context)
        parsed = parsed.model_copy(update=_target_update(target_ledger))
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
            ledger_id=target_ledger.id,
            type=parsed.type,
            amount=parsed.amount,
            category=parsed.category,
            subcategory=parsed.subcategory,
            description=parsed.description or parsed.category,
            occurred_at=parsed.occurred_at,
            raw_text=payload.message,
            source="llm_chat",
        ),
        target_ledger.id,
    )
    if target_ledger.id != context.ledger.id:
        reply = f"{reply} 已记入“{target_ledger.name}”账本。"
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
