from typing import List

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.models.assignment import Assignment
from app.models.course import Course
from app.schemas.assignment import AssignmentCreate, AssignmentResponse, AssignmentUpdate


router = APIRouter()


async def _get_course(db: AsyncSession, course_id: int) -> Course | None:
    result = await db.execute(select(Course).where(Course.id == course_id))
    return result.scalar_one_or_none()


async def _get_assignment(db: AsyncSession, assignment_id: int) -> Assignment | None:
    result = await db.execute(select(Assignment).where(Assignment.id == assignment_id))
    return result.scalar_one_or_none()


@router.post("/", response_model=AssignmentResponse, status_code=201)
async def create_assignment(
    assignment_in: AssignmentCreate,
    db: AsyncSession = Depends(get_db),
) -> AssignmentResponse:
    course = await _get_course(db, assignment_in.course_id)
    if course is None:
        raise HTTPException(status_code=404, detail="Course not found")

    assignment = Assignment(**assignment_in.model_dump())
    db.add(assignment)
    await db.commit()
    await db.refresh(assignment)
    return assignment


@router.get("/", response_model=List[AssignmentResponse])
async def list_assignments(
    db: AsyncSession = Depends(get_db),
) -> List[AssignmentResponse]:
    result = await db.execute(select(Assignment))
    return list(result.scalars().all())


@router.get("/{assignment_id}", response_model=AssignmentResponse)
async def get_assignment(
    assignment_id: int,
    db: AsyncSession = Depends(get_db),
) -> AssignmentResponse:
    assignment = await _get_assignment(db, assignment_id)
    if assignment is None:
        raise HTTPException(status_code=404, detail="Assignment not found")
    return assignment


@router.put("/{assignment_id}", response_model=AssignmentResponse)
async def update_assignment(
    assignment_id: int,
    assignment_in: AssignmentUpdate,
    db: AsyncSession = Depends(get_db),
) -> AssignmentResponse:
    assignment = await _get_assignment(db, assignment_id)
    if assignment is None:
        raise HTTPException(status_code=404, detail="Assignment not found")

    update_data = assignment_in.model_dump(exclude_unset=True)
    if "course_id" in update_data and update_data["course_id"] is not None:
        course = await _get_course(db, update_data["course_id"])
        if course is None:
            raise HTTPException(status_code=404, detail="Course not found")

    for field, value in update_data.items():
        setattr(assignment, field, value)

    await db.commit()
    await db.refresh(assignment)
    return assignment


@router.delete("/{assignment_id}")
async def delete_assignment(
    assignment_id: int,
    db: AsyncSession = Depends(get_db),
) -> dict[str, str]:
    assignment = await _get_assignment(db, assignment_id)
    if assignment is None:
        raise HTTPException(status_code=404, detail="Assignment not found")

    await db.delete(assignment)
    await db.commit()
    return {"message": "Deleted successfully"}
