from datetime import datetime
from sqlalchemy.orm import declarative_base
from sqlalchemy import Column, Integer, String, Text, DateTime

Base = declarative_base()

class LLMFeedback(Base):
    __tablename__ = "llm_feedback"

    id = Column(Integer, primary_key=True, index=True)
    question = Column(Text, nullable=False)
    answer = Column(Text, nullable=False)
    feedback = Column(String(16), nullable=False)  # like / dislike
    created_at = Column(DateTime, default=datetime.utcnow) 