from datetime import datetime

from pydantic import BaseModel, ConfigDict


class QualityIssue(BaseModel):
    code: str
    message: str
    severity: str


class QualityCheckCreate(BaseModel):
    target_type: str
    target_id: int
    check_type: str
    status: str
    score: float | None = None
    issues_json: str | None = None
    summary: str
    created_by_job_id: int | None = None


class QualityCheckRead(QualityCheckCreate):
    model_config = ConfigDict(from_attributes=True)

    id: int
    created_at: datetime
    updated_at: datetime


class QualityCheckBatchResponse(BaseModel):
    target_type: str
    target_id: int
    checks: list[QualityCheckRead]


class DraftQualityRunRequest(BaseModel):
    story_draft_id: int


class StoryPagesQualityRunRequest(BaseModel):
    story_draft_id: int


class QualitySummaryResponse(BaseModel):
    target_type: str
    target_id: int
    overall_status: str
    checks: list[QualityCheckRead]
