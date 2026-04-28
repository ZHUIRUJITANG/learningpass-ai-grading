from sqlalchemy import Column, Integer, String, DateTime, Float, Text, ForeignKey
from sqlalchemy.orm import relationship
from datetime import datetime
from app.core.database import Base

class Submission(Base):
    __tablename__ = "submissions"

    id = Column(Integer, primary_key=True, index=True)
    course_id = Column(Integer, ForeignKey("courses.id"))
    course_name = Column(String(200))
    assignment_id = Column(Integer, ForeignKey("assignments.id"))
    assignment_name = Column(String(200))
    student_id = Column(String(50))
    student_name = Column(String(100))
    submit_time = Column(DateTime, default=datetime.now)
    is_late = Column(Integer, default=0)

    file_name = Column(String(500))
    file_type = Column(String(50))
    file_path = Column(String(1000))

    parse_status = Column(String(20), default="pending")
    extracted_content = Column(Text)
    parse_confidence = Column(Float)

    ai_score = Column(Float)
    ai_comment = Column(Text)
    ai_score_reason = Column(Text)

    final_score = Column(Float)
    teacher_comment = Column(Text)
    review_status = Column(String(20), default="pending")

    created_at = Column(DateTime, default=datetime.now)
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now)

    course = relationship("Course", back_populates="submissions")
    assignment = relationship("Assignment", back_populates="submissions")