from typing import List

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.models.course import Course
from app.schemas.course import CourseCreate, CourseResponse, CourseUpdate


router = APIRouter()


async def _get_course(db: AsyncSession, course_id: int) -> Course | None:
    result = await db.execute(select(Course).where(Course.id == course_id))
    return result.scalar_one_or_none()


@router.post("/", response_model=CourseResponse, status_code=201)
async def create_course(
    course_in: CourseCreate,
    db: AsyncSession = Depends(get_db),
) -> CourseResponse:
    course = Course(**course_in.model_dump())
    db.add(course)
    await db.commit()
    await db.refresh(course)
    return course


@router.get("/", response_model=List[CourseResponse])
async def list_courses(
    db: AsyncSession = Depends(get_db),
) -> List[CourseResponse]:
    result = await db.execute(select(Course))
    return list(result.scalars().all())


@router.get("/{course_id}", response_model=CourseResponse)
async def get_course(
    course_id: int,
    db: AsyncSession = Depends(get_db),
) -> CourseResponse:
    course = await _get_course(db, course_id)
    if course is None:
        raise HTTPException(status_code=404, detail="Course not found")
    return course


@router.put("/{course_id}", response_model=CourseResponse)
async def update_course(
    course_id: int,
    course_in: CourseUpdate,
    db: AsyncSession = Depends(get_db),
) -> CourseResponse:
    course = await _get_course(db, course_id)
    if course is None:
        raise HTTPException(status_code=404, detail="Course not found")

    for field, value in course_in.model_dump(exclude_unset=True).items():
        setattr(course, field, value)

    await db.commit()
    await db.refresh(course)
    return course


@router.delete("/{course_id}")
async def delete_course(
    course_id: int,
    db: AsyncSession = Depends(get_db),
) -> dict[str, str]:
    course = await _get_course(db, course_id)
    if course is None:
        raise HTTPException(status_code=404, detail="Course not found")

    await db.delete(course)
    await db.commit()
    return {"message": "Deleted successfully"}
