import uuid
from sqlalchemy import Column, String, DateTime, ForeignKey, Numeric, Boolean
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.sql import func
from packages.tenant.database import Base

class DocumentUpload(Base):
    __tablename__ = "document_uploads"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id = Column(UUID(as_uuid=True), ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False, index=True)
    
    file_hash = Column(String(255), nullable=False, index=True) # For idempotency / dedup
    file_path = Column(String(1024), nullable=False) # local path or s3 uri
    format = Column(String(50), nullable=False) # XML, PDF, IMAGE
    status = Column(String(50), nullable=False, default="PENDING") # PENDING, EXTRACTING, NEEDS_REVIEW, APPROVED, REJECTED
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

RawDocument = DocumentUpload

class DocumentExtraction(Base):
    __tablename__ = "document_extractions"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id = Column(UUID(as_uuid=True), ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False, index=True)
    document_upload_id = Column(UUID(as_uuid=True), ForeignKey("document_uploads.id", ondelete="CASCADE"), nullable=False, unique=True)
    
    # Header Candidates
    supplier_cnpj_candidate = Column(String(50), nullable=True)
    supplier_name_candidate = Column(String(255), nullable=True)
    invoice_number_candidate = Column(String(100), nullable=True)
    total_amount_candidate = Column(Numeric(precision=24, scale=12), nullable=True)
    issue_date_candidate = Column(DateTime(timezone=True), nullable=True)
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())

class DocumentExtractionLine(Base):
    __tablename__ = "document_extraction_lines"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id = Column(UUID(as_uuid=True), ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False, index=True)
    document_extraction_id = Column(UUID(as_uuid=True), ForeignKey("document_extractions.id", ondelete="CASCADE"), nullable=False, index=True)
    
    # Raw extracted line data
    raw_description = Column(String(255), nullable=True)
    raw_code = Column(String(100), nullable=True)
    raw_quantity = Column(Numeric(precision=24, scale=12), nullable=True)
    raw_uom = Column(String(50), nullable=True)
    raw_unit_price = Column(Numeric(precision=24, scale=12), nullable=True)
    
    # Matching (AI/Deterministic)
    normalized_sku_id = Column(UUID(as_uuid=True), ForeignKey("skus.id", ondelete="SET NULL"), nullable=True)
    confidence_score = Column(Numeric(precision=5, scale=4), nullable=True) # 0.0 to 1.0
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())
