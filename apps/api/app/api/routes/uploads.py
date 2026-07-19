from pathlib import Path
from uuid import uuid4

from fastapi import APIRouter, Depends, File, HTTPException, Query, Request, UploadFile

from app.api.dependencies import RequestContext, get_request_context
from app.domain.schemas import AvatarUploadResponse, DocumentOcrResponse
from app.services.vision_service import VisionService
from app.services.llm_client import LlmError

router = APIRouter()
UPLOAD_DIR = Path(__file__).resolve().parents[3] / "uploads"
ALLOWED_TYPES = {"image/jpeg": ".jpg", "image/png": ".png", "image/webp": ".webp", "image/gif": ".gif"}
MAX_AVATAR_BYTES = 5 * 1024 * 1024
MAX_DOCUMENT_BYTES = 12 * 1024 * 1024
vision_service = VisionService()


@router.post("/avatar", response_model=AvatarUploadResponse)
async def upload_avatar(
    request: Request,
    file: UploadFile = File(...),
    _context: RequestContext = Depends(get_request_context),
) -> AvatarUploadResponse:
    extension = ALLOWED_TYPES.get(file.content_type or "")
    if extension is None:
        raise HTTPException(status_code=415, detail="头像仅支持 JPG、PNG、WebP 或 GIF 图片。")
    content = await file.read(MAX_AVATAR_BYTES + 1)
    if len(content) > MAX_AVATAR_BYTES:
        raise HTTPException(status_code=413, detail="头像图片不能超过 5 MB。")
    if not content:
        raise HTTPException(status_code=400, detail="上传的图片为空。")
    UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
    filename = f"avatar-{uuid4().hex}{extension}"
    (UPLOAD_DIR / filename).write_bytes(content)
    return AvatarUploadResponse(url=f"/media/{filename}")


@router.post("/document-ocr", response_model=DocumentOcrResponse)
async def upload_document_for_ocr(
    request: Request,
    file: UploadFile = File(...),
    analyze: bool = Query(default=True),
    _context: RequestContext = Depends(get_request_context),
) -> DocumentOcrResponse:
    extension = ALLOWED_TYPES.get(file.content_type or "")
    if extension is None:
        raise HTTPException(status_code=415, detail="单据图片仅支持 JPG、PNG、WebP 或 GIF。")
    content = await file.read(MAX_DOCUMENT_BYTES + 1)
    if len(content) > MAX_DOCUMENT_BYTES:
        raise HTTPException(status_code=413, detail="单据图片不能超过 12 MB。")
    if not content:
        raise HTTPException(status_code=400, detail="上传的图片为空。")
    UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
    filename = f"document-{uuid4().hex}{extension}"
    (UPLOAD_DIR / filename).write_bytes(content)
    image_url = f"/media/{filename}"
    if not analyze:
        return DocumentOcrResponse(
            image_url=image_url,
            provider_configured=vision_service.provider_configured,
            message="图片已添加，将在发送消息后识别。",
        )
    try:
        result = vision_service.analyze(content, file.content_type or "application/octet-stream")
    except LlmError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc
    configured = vision_service.provider_configured
    return DocumentOcrResponse(
        image_url=image_url,
        extracted_text=result.extracted_text,
        document_type=result.document_type,
        confidence=result.confidence,
        status=result.status,
        provider_configured=configured,
        message="图片识别完成，已提取票面字段。" if result.status == "completed"
        else "图片已上传；视觉模型尚未配置，当前只能结合你输入的文字继续识别。",
    )
