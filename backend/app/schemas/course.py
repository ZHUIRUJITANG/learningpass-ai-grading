from typing import Optional

from pydantic import BaseModel, ConfigDict


class CourseBase(BaseModel):
    name: str
    code: str


class CourseCreate(CourseBase):
    pass


class CourseUpdate(CourseBase):
    name: Optional[str] = None
    code: Optional[str] = None


class CourseResponse(CourseBase):
    id: int

    model_config = ConfigDict(from_attributes=True)
