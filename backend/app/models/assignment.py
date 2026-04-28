from sqlalchemy import Column, Integer, String, Text, JSON, ForeignKey, DateTime, Float
from sqlalchemy.orm import relationship
from app.core.database import Base

class Assignment(Base):
    __tablename__ = "assignments"

    id = Column(Integer, primary_key=True, index=True)
    course_id = Column(Integer, ForeignKey("courses.id"))
    name = Column(String(200))
    description = Column(Text)
    due_date = Column(DateTime)
    grading_rubric = Column(JSON)
    total_points = Column(Float, default=100.0)

    course = relationship("Course", back_populates="assignments")
    submissions = relationship("Submission", back_populates="assignment")