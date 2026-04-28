from io import BytesIO

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse
from openpyxl import Workbook
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.models.assignment import Assignment
from app.models.submission import Submission


router = APIRouter()


@router.get("/{assignment_id}")
async def export_grades(
    assignment_id: int,
    db: AsyncSession = Depends(get_db),
) -> StreamingResponse:
    assignment_result = await db.execute(
        select(Assignment).where(Assignment.id == assignment_id)
    )
    assignment = assignment_result.scalar_one_or_none()
    if assignment is None:
        raise HTTPException(status_code=404, detail="Assignment not found")

    result = await db.execute(
        select(Submission)
        .where(Submission.assignment_id == assignment_id)
        .order_by(Submission.submit_time.asc(), Submission.id.asc())
    )
    submissions = list(result.scalars().all())

    workbook = Workbook()
    worksheet = workbook.active
    worksheet.title = "Grades"
    worksheet.append(
        [
            "学号",
            "姓名",
            "是否迟交",
            "文件名",
            "AI建议分",
            "教师最终分",
            "AI评语",
            "教师评语",
            "复核状态",
        ]
    )

    for submission in submissions:
        worksheet.append(
            [
                submission.student_id,
                submission.student_name,
                "是" if submission.is_late else "否",
                submission.file_name,
                submission.ai_score,
                submission.final_score,
                submission.ai_comment,
                submission.teacher_comment,
                submission.review_status,
            ]
        )

    output = BytesIO()
    workbook.save(output)
    output.seek(0)

    return StreamingResponse(
        output,
        media_type=(
            "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        ),
        headers={
            "Content-Disposition": (
                f'attachment; filename="grades_{assignment_id}.xlsx"'
            )
        },
    )
