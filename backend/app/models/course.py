from sqlalchemy import Column, Integer, String
from sqlalchemy.orm import relationship
from app.core.database import Base

class Course(Base):
    __tablename__ = "courses"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(200))
    code = Column(String(50))

    assignments = relationship("Assignment", back_populates="course")
    submissions = relationship("Submission", back_populates="course")