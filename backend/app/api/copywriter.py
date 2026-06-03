"""广告文案生成 API。"""

from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.db import get_db
from app.core.security import get_current_user
from app.models.user import User
from app.schemas.copywriter import CopyGenerateRequest, CopyGenerateResponse
from app.services.copywriter import generate_copy
from app.services.llm_router import LLMRouterError

router = APIRouter(prefix="/api/copy", tags=["copywriter"])


@router.post("/generate", response_model=CopyGenerateResponse)
def generate_copywriting(
    req: CopyGenerateRequest,
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
) -> CopyGenerateResponse:
    try:
        return generate_copy(req=req, db=db, user_id=current_user.id)
    except LLMRouterError as e:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"模型调用失败: {e}",
        )
