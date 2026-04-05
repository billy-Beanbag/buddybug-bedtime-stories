from pydantic import BaseModel


class RecommendedBookScore(BaseModel):
    book_id: int
    title: str
    cover_image_url: str | None = None
    age_band: str
    content_lane_key: str | None = None
    is_classic: bool = False
    language: str
    published: bool
    publication_status: str
    score: float
    reasons: list[str]


class RecommendationsResponse(BaseModel):
    items: list[RecommendedBookScore]


class MoreLikeThisRequest(BaseModel):
    book_id: int
    limit: int = 10


class RecommendationDebugResponse(BaseModel):
    user_id: int
    evaluated_count: int
    items: list[RecommendedBookScore]
