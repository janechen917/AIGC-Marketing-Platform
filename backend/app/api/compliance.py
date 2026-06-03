"""规则审核 API。"""

from fastapi import APIRouter

from app.schemas.compliance import ComplianceCheckRequest, ComplianceCheckResponse
from app.services.compliance import check_all

router = APIRouter(prefix="/api/compliance", tags=["compliance"])


@router.post("/check", response_model=ComplianceCheckResponse)
def check_compliance(req: ComplianceCheckRequest) -> ComplianceCheckResponse:
    result = check_all(
        req.text,
        brand_name=req.brand_name,
        required_phrases=req.required_phrases,
        forbidden_competitors=req.forbidden_competitors,
        max_length=req.max_length,
        require_hashtag=req.require_hashtag,
        require_cta=req.require_cta,
        max_emojis=req.max_emojis,
        ad_law_extra_banned_words=req.ad_law_extra_banned_words,
    )
    return ComplianceCheckResponse(**result)
