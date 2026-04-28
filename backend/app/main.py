from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.v1.endpoints import assignments, courses, export, health, submissions
from app.core.database import Base, engine
from app.models import assignment, course, submission


async def init_db() -> None:
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)


app = FastAPI(
    title="Grading System",
    description="Backend API for the grading system",
)


@app.on_event("startup")
async def startup_event() -> None:
    await init_db()


app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(health.router, prefix="/api/v1", tags=["health"])
app.include_router(courses.router, prefix="/api/v1/courses", tags=["courses"])
app.include_router(
    assignments.router,
    prefix="/api/v1/assignments",
    tags=["assignments"],
)
app.include_router(
    submissions.router,
    prefix="/api/v1/submissions",
    tags=["submissions"],
)
app.include_router(export.router, prefix="/api/v1/export", tags=["export"])


@app.get("/")
async def root() -> dict[str, str]:
    return {"message": "Backend is running"}
