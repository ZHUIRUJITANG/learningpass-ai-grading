import asyncio
import os
import tempfile
from pathlib import Path
from typing import List
from uuid import uuid4

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.database import get_db
from app.core.minio_client import minio_client
from app.models.assignment import Assignment
from app.models.course import Course
from app.models.submission import Submission
from app.schemas.submission import SubmissionResponse, SubmissionUpdate
from app.services.file_parser import parse_file
from app.services.file_storage import get_file_url, upload_file
from app.services.llm_grader import grade_submission


router = APIRouter()


async def _get_assignment(db: AsyncSession, assignment_id: int) -> Assignment | None:
    result = await db.execute(select(Assignment).where(Assignment.id == assignment_id))
    return result.scalar_one_or_none()


async def _get_course(db: AsyncSession, course_id: int) -> Course | None:
    result = await db.execute(select(Course).where(Course.id == course_id))
    return result.scalar_one_or_none()


async def _get_submission(db: AsyncSession, submission_id: int) -> Submission | None:
    result = await db.execute(select(Submission).where(Submission.id == submission_id))
    return result.scalar_one_or_none()


def _serialize_submission(submission: Submission) -> SubmissionResponse:
    file_url = get_file_url(submission.file_path) if submission.file_path else None
    return SubmissionResponse.model_validate(submission).model_copy(
        update={"file_url": file_url}
    )


@router.post("/", response_model=SubmissionResponse, status_code=201)
async def create_submission(
    student_id: str = Form(...),
    student_name: str = Form(...),
    assignment_id: int = Form(...),
    file: UploadFile = File(...),
    db: AsyncSession = Depends(get_db),
) -> SubmissionResponse:
    assignment = await _get_assignment(db, assignment_id)
    if assignment is None:
        raise HTTPException(status_code=404, detail="Assignment not found")

    course = await _get_course(db, assignment.course_id)
    safe_file_name = Path(file.filename or "uploaded_file").name or "uploaded_file"
    object_name = f"submissions/{assignment_id}/{student_id}/{uuid4().hex}_{safe_file_name}"
    file_content = await file.read()
    file_type = file.content_type or "application/octet-stream"
    stored_object_name: str | None = None

    try:
        stored_object_name = await upload_file(
            file_content=file_content,
            object_name=object_name,
            content_type=file_type,
        )

        parse_status = "failed"
        extracted_text = ""
        parse_confidence = 0.0
        ai_score: float | None = None
        ai_comment: str | None = None
        ai_score_reason: str | None = None

        temp_file = tempfile.NamedTemporaryFile(
            delete=False,
            suffix=os.path.splitext(safe_file_name)[1],
        )
        temp_file_path = Path(temp_file.name)
        temp_file.close()

        try:
            try:
                await asyncio.to_thread(
                    minio_client.fget_object,
                    settings.MINIO_BUCKET,
                    stored_object_name,
                    str(temp_file_path),
                )

                parse_result = await parse_file(str(temp_file_path), file_type)
                extracted_text = str(parse_result.get("extracted_text", "") or "")
                parse_confidence = float(parse_result.get("confidence", 0.0) or 0.0)
                parse_status = "completed"

                try:
                    grading_result = await grade_submission(
                        extracted_text=extracted_text,
                        assignment_requirements=str(assignment.description or ""),
                        grading_rubric=assignment.grading_rubric,
                    )
                    ai_score_value = grading_result.get("score")
                    ai_score = (
                        float(ai_score_value) if ai_score_value is not None else None
                    )
                    ai_comment = str(grading_result.get("comment", "") or "")
                    ai_score_reason = str(grading_result.get("reason", "") or "")
                except Exception as exc:
                    print(
                        f"[LLM] Failed to grade submission '{stored_object_name}': {exc}"
                    )
            except Exception as exc:
                print(f"Failed to parse submission file '{stored_object_name}': {exc}")
                parse_status = "failed"
                extracted_text = ""
                parse_confidence = 0.0
        finally:
            try:
                await asyncio.to_thread(os.unlink, temp_file_path)
            except FileNotFoundError:
                pass
            except Exception as exc:
                print(f"Failed to remove temp file '{temp_file_path}': {exc}")

        submission = Submission(
            course_id=assignment.course_id,
            course_name=course.name if course is not None else None,
            assignment_id=assignment.id,
            assignment_name=assignment.name,
            student_id=student_id,
            student_name=student_name,
            file_name=safe_file_name,
            file_type=file_type,
            file_path=stored_object_name,
            parse_status=parse_status,
            extracted_content=extracted_text,
            parse_confidence=parse_confidence,
            ai_score=ai_score,
            ai_comment=ai_comment,
            ai_score_reason=ai_score_reason,
        )

        db.add(submission)
        await db.commit()
        await db.refresh(submission)
        return _serialize_submission(submission)
    except Exception as exc:
        await db.rollback()
        if stored_object_name is not None:
            try:
                await asyncio.to_thread(
                    minio_client.remove_object,
                    settings.MINIO_BUCKET,
                    stored_object_name,
                )
            except Exception:
                pass
        raise HTTPException(status_code=500, detail="Failed to create submission") from exc


@router.get("/", response_model=List[SubmissionResponse])
async def list_submissions(
    assignment_id: int | None = None,
    db: AsyncSession = Depends(get_db),
) -> List[SubmissionResponse]:
    query = select(Submission)
    if assignment_id is not None:
        query = query.where(Submission.assignment_id == assignment_id)

    result = await db.execute(query)
    return [_serialize_submission(submission) for submission in result.scalars().all()]


@router.get("/{submission_id}", response_model=SubmissionResponse)
async def get_submission(
    submission_id: int,
    db: AsyncSession = Depends(get_db),
) -> SubmissionResponse:
    submission = await _get_submission(db, submission_id)
    if submission is None:
        raise HTTPException(status_code=404, detail="Submission not found")
    return _serialize_submission(submission)


@router.put("/{submission_id}", response_model=SubmissionResponse)
async def update_submission(
    submission_id: int,
    submission_in: SubmissionUpdate,
    db: AsyncSession = Depends(get_db),
) -> SubmissionResponse:
    submission = await _get_submission(db, submission_id)
    if submission is None:
        raise HTTPException(status_code=404, detail="Submission not found")

    update_data = submission_in.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(submission, field, value)

    try:
        await db.commit()
        await db.refresh(submission)
    except Exception as exc:
        await db.rollback()
        raise HTTPException(status_code=500, detail="Failed to update submission") from exc

    return _serialize_submission(submission)


@router.delete("/{submission_id}")
async def delete_submission(
    submission_id: int,
    db: AsyncSession = Depends(get_db),
) -> dict[str, str]:
    submission = await _get_submission(db, submission_id)
    if submission is None:
        raise HTTPException(status_code=404, detail="Submission not found")

    try:
        await asyncio.to_thread(
            minio_client.remove_object,
            settings.MINIO_BUCKET,
            submission.file_path,
        )
    except Exception as exc:
        raise HTTPException(status_code=500, detail="Failed to delete file") from exc

    try:
        await db.delete(submission)
        await db.commit()
    except Exception as exc:
        await db.rollback()
        raise HTTPException(status_code=500, detail="Failed to delete submission") from exc

    return {"message": "Deleted successfully"}
