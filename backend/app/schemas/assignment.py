from datetime import datetime
from typing import Any, Optional

from pydantic import BaseModel, ConfigDict


class AssignmentBase(BaseModel):
    course_id: int
    name: str
    description: Optional[str] = None
    due_date: Optional[datetime] = None
    grading_rubric: Optional[dict[str, Any]] = None
    total_points: float = 100.0


class AssignmentCreate(AssignmentBase):
    pass


class AssignmentUpdate(AssignmentBase):
    course_id: Optional[int] = None
    name: Optional[str] = None
    description: Optional[str] = None
    due_date: Optional[datetime] = None
    grading_rubric: Optional[dict[str, Any]] = None
    total_points: Optional[float] = None


class AssignmentResponse(AssignmentBase):
    id: int

    model_config = ConfigDict(from_attributes=True)
