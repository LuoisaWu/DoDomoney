from pathlib import Path
from uuid import uuid4

from fastapi import APIRouter, Depends, File, HTTPException, Request, UploadFile

from app.api.dependencies import RequestContext, get_request_context
from app.domain.schemas import AvatarUploadResponse

router = APIRouter()
UPLOAD_DIR = Path(__file__).resolve().parents[3] / "uploads"
ALLOWED_TYPES = {"image/jpeg": ".jpg", "image/png": ".png", "image/webp": ".webp", "image/gif": ".gif"}
MAX_AVATAR_BYTES = 5 * 1024 * 1024


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
    base = str(request.base_url).rstrip("/")
    return AvatarUploadResponse(url=f"{base}/media/{filename}")
