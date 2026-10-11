import uuid
from datetime import datetime
from decimal import Decimal
from sqlalchemy import (
    Column,
    String,
    Integer,
    Text,
    Numeric,
    DateTime,
    Boolean,
    ForeignKey,
    UniqueConstraint,
    Index
)
from sqlalchemy.orm import relationship
from pgvector.sqlalchemy import Vector
from app.database.session import Base

class Policy(Base):
    __tablename__ = "policies"

    id = Column(String(64), primary_key=True, default=lambda: str(uuid.uuid4()))
    filename = Column(String(255), nullable=False)
    original_filename = Column(String(255), nullable=False)
    file_path = Column(Text, nullable=False)
    file_size_bytes = Column(Integer, nullable=False)
    page_count = Column(Integer, nullable=False, default=0)
    uploaded_at = Column(String(64), nullable=False, default=lambda: datetime.utcnow().isoformat())
    extraction_status = Column(String(32), nullable=False, default="PENDING")
    error_message = Column(Text, nullable=True)
    owner_id = Column(String(64), ForeignKey("users.id", ondelete="SET NULL"), nullable=True, index=True)
    is_public = Column(Boolean, nullable=False, default=False, index=True)

    # Relationships
    owner = relationship(
        "User",
        back_populates="policies"
    )
    pages = relationship(
        "PolicyPage",
        back_populates="policy",
        cascade="all, delete-orphan",
        order_by="PolicyPage.page_number"
    )
    rules = relationship(
        "PolicyRule",
        back_populates="policy",
        cascade="all, delete-orphan",
        order_by="PolicyRule.id"
    )
    chunks = relationship(
        "PolicyChunk",
        back_populates="policy",
        cascade="all, delete-orphan",
        order_by="PolicyChunk.chunk_id"
    )

    def to_dict(self):
        return {
            "id": self.id,
            "filename": self.filename,
            "original_filename": self.original_filename,
            "file_path": self.file_path,
            "file_size_bytes": self.file_size_bytes,
            "page_count": self.page_count,
            "uploaded_at": self.uploaded_at,
            "extraction_status": self.extraction_status,
            "error_message": self.error_message,
            "owner_id": self.owner_id,
            "is_public": bool(self.is_public)
        }


class PolicyPage(Base):
    __tablename__ = "policy_pages"

    id = Column(Integer, primary_key=True, autoincrement=True)
    policy_id = Column(String(64), ForeignKey("policies.id", ondelete="CASCADE"), nullable=False, index=True)
    page_number = Column(Integer, nullable=False)
    char_count = Column(Integer, nullable=False, default=0)
    word_count = Column(Integer, nullable=False, default=0)
    content = Column(Text, nullable=False)
    layout_data = Column(Text, nullable=True)

    policy = relationship("Policy", back_populates="pages")

    def to_dict(self):
        return {
            "id": self.id,
            "policy_id": self.policy_id,
            "page_number": self.page_number,
            "char_count": self.char_count,
            "word_count": self.word_count,
            "content": self.content,
            "layout_data": self.layout_data
        }


class PolicyRule(Base):
    __tablename__ = "policy_rules"

    id = Column(Integer, primary_key=True, autoincrement=True)
    policy_id = Column(String(64), ForeignKey("policies.id", ondelete="CASCADE"), nullable=False, index=True)
    rule_type = Column(String(64), nullable=False)
    rule_key = Column(String(128), nullable=False)
    value = Column(Numeric(14, 2), nullable=True)
    unit = Column(String(64), nullable=True)
    page = Column(Integer, nullable=False, default=1)
    clause = Column(String(255), nullable=True)
    source_text = Column(Text, nullable=False)
    confidence = Column(String(32), nullable=False, default="HIGH")
    qualifiers = Column(Text, nullable=True)
    bbox = Column(Text, nullable=True)
    additional_sources = Column(Text, nullable=True)
    status = Column(String(32), nullable=False, default="VERIFIED")
    formatted_value = Column(String(255), nullable=True)

    policy = relationship("Policy", back_populates="rules")

    def to_dict(self):
        return {
            "id": self.id,
            "policy_id": self.policy_id,
            "rule_type": self.rule_type,
            "rule_key": self.rule_key,
            "value": self.value,
            "unit": self.unit,
            "page": self.page,
            "clause": self.clause,
            "source_text": self.source_text,
            "confidence": self.confidence,
            "qualifiers": self.qualifiers,
            "bbox": self.bbox,
            "additional_sources": self.additional_sources,
            "status": self.status,
            "formatted_value": self.formatted_value
        }


class TreatmentCost(Base):
    __tablename__ = "treatment_costs"

    id = Column(Integer, primary_key=True, autoincrement=True)
    procedure_name = Column(String(255), nullable=False)
    procedure_code = Column(String(64), nullable=True)
    city = Column(String(128), nullable=False)
    city_tier = Column(String(32), nullable=False)
    min_cost = Column(Numeric(14, 2), nullable=False)
    max_cost = Column(Numeric(14, 2), nullable=False)
    source = Column(String(255), nullable=False)
    source_date = Column(String(64), nullable=True)
    notes = Column(Text, nullable=True)
    data_type = Column(String(64), nullable=False, default="synthetic")

    __table_args__ = (
        UniqueConstraint("procedure_name", "city", name="uq_treatment_costs_proc_city"),
        Index("idx_treatment_costs_proc_city", "procedure_name", "city"),
    )

    def to_dict(self):
        return {
            "id": self.id,
            "procedure_name": self.procedure_name,
            "procedure_code": self.procedure_code,
            "city": self.city,
            "city_tier": self.city_tier,
            "min_cost": self.min_cost,
            "max_cost": self.max_cost,
            "source": self.source,
            "source_date": self.source_date,
            "notes": self.notes,
            "data_type": self.data_type
        }


class PolicyChunk(Base):
    __tablename__ = "policy_chunks"

    chunk_id = Column(String(64), primary_key=True)
    policy_id = Column(String(64), ForeignKey("policies.id", ondelete="CASCADE"), nullable=False, index=True)
    document_id = Column(String(64), nullable=False)
    section = Column(String(255), nullable=True)
    clause = Column(String(255), nullable=True)
    rule_type = Column(String(64), nullable=True)
    subtype = Column(String(64), nullable=True)
    text = Column(Text, nullable=False)
    source_page = Column(Integer, nullable=False)
    source_text = Column(Text, nullable=False)
    bbox = Column(Text, nullable=True)
    embedding = Column(Vector(768), nullable=True)
    created_at = Column(String(64), nullable=False, default=lambda: datetime.utcnow().isoformat())

    policy = relationship("Policy", back_populates="chunks")

    __table_args__ = (
        Index("idx_policy_chunks_embedding", "embedding", postgresql_using="hnsw", postgresql_ops={"embedding": "vector_cosine_ops"}),
        Index("idx_policy_chunks_policy_page", "policy_id", "source_page"),
    )

    def to_dict(self):
        return {
            "chunk_id": self.chunk_id,
            "policy_id": self.policy_id,
            "document_id": self.document_id,
            "section": self.section,
            "clause": self.clause,
            "rule_type": self.rule_type,
            "subtype": self.subtype,
            "text": self.text,
            "source_page": self.source_page,
            "source_text": self.source_text,
            "bbox": self.bbox,
            "embedding": self.embedding.tolist() if hasattr(self.embedding, "tolist") else self.embedding,
            "created_at": self.created_at
        }

