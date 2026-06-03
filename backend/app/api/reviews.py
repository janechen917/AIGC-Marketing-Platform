"""批量好评 API。"""

from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.db import get_db
from app.core.security import get_current_user
from app.models.user import User
from app.schemas.reviews import ReviewsGenerateRequest, ReviewsGenerateResponse
from app.services.llm_router import LLMRouterError
from app.services.review_generator import generate_reviews

router = APIRouter(prefix="/api/reviews", tags=["reviews"])


@router.post("/generate", response_model=ReviewsGenerateResponse)
def generate_reviews_api(
    req: ReviewsGenerateRequest,
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
) -> ReviewsGenerateResponse:
    try:
        return generate_reviews(req=req, db=db, user_id=current_user.id)
    except LLMRouterError as e:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"模型调用失败: {e}",
        )
