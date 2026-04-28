from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict


class SubmissionBase(BaseModel):
    student_id: str
    student_name: str
    assignment_id: int
    file_name: str


class SubmissionCreate(SubmissionBase):
    pass


class SubmissionUpdate(BaseModel):
    final_score: float | None = None
    teacher_comment: str | None = None
    review_status: Literal["pending", "reviewed", "confirmed"] | None = None


class SubmissionResponse(SubmissionBase):
    id: int
    submit_time: datetime
    parse_status: str | None
    ai_score: float | None
    ai_comment: str | None
    ai_score_reason: str | None
    parse_confidence: float | None
    extracted_content: str | None
    final_score: float | None
    teacher_comment: str | None = None
    review_status: str
    file_url: str | None = None

    model_config = ConfigDict(from_attributes=True)
