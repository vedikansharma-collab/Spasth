import uuid
from datetime import datetime
from sqlalchemy import Column, String, Integer, DateTime, ForeignKey, Text
from sqlalchemy.orm import relationship
from app.database.session import Base

class Policy(Base):
    __tablename__ = "policies"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    filename = Column(String, nullable=False)
    original_filename = Column(String, nullable=False)
    file_path = Column(String, nullable=False)
    file_size_bytes = Column(Integer, nullable=False)
    page_count = Column(Integer, nullable=False, default=0)
    uploaded_at = Column(DateTime, default=datetime.utcnow)
    extraction_status = Column(String, nullable=False, default="PENDING")  # PENDING, SUCCESS, FAILED
    error_message = Column(String, nullable=True)

    # Relationship to page-by-page extracted content
    pages = relationship("PolicyPage", back_populates="policy", cascade="all, delete-orphan", order_by="PolicyPage.page_number")


class PolicyPage(Base):
    __tablename__ = "policy_pages"

    id = Column(Integer, primary_key=True, autoincrement=True)
    policy_id = Column(String, ForeignKey("policies.id", ondelete="CASCADE"), nullable=False, index=True)
    page_number = Column(Integer, nullable=False)  # 1-indexed
    char_count = Column(Integer, nullable=False, default=0)
    word_count = Column(Integer, nullable=False, default=0)
    content = Column(Text, nullable=False)

    policy = relationship("Policy", back_populates="pages")
