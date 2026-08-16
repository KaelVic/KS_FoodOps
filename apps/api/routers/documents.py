import hashlib
import uuid
from typing import List, Optional
from datetime import datetime
from decimal import Decimal

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile, status, Request
from pydantic import BaseModel, ConfigDict
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload

from modules.documents.models import DocumentExtraction, DocumentExtractionLine, DocumentUpload
from modules.suppliers.models import Supplier
from modules.documents.service import IngestionPipeline, DocumentApprovalService
from packages.security.dependencies import get_secure_session
from apps.api.main import limiter

router = APIRouter(tags=["Documents"])


class UploadNFEResponse(BaseModel):
    id: uuid.UUID
    invoice_number: str
    status: str
    total_amount: float


class ExtractionListResponse(BaseModel):
    id: uuid.UUID
    invoice_number: str
    issue_date: Optional[datetime]
    total_amount: float
    status: str
    created_at: datetime
    supplier_name: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)


class ExtractionLineResponse(BaseModel):
    id: uuid.UUID
    raw_description: Optional[str]
    raw_code: Optional[str]
    raw_quantity: float
    raw_uom: Optional[str]
    raw_unit_price: float
    match_status: str

    model_config = ConfigDict(from_attributes=True)


class ExtractionDetailResponse(BaseModel):
    id: uuid.UUID
    invoice_number: str
    issue_date: Optional[datetime]
    total_amount: float
    status: str
    created_at: datetime
    supplier_name: Optional[str] = None
    lines: List[ExtractionLineResponse]


class ApproveResponse(BaseModel):
    success: bool
    invoice_id: uuid.UUID


@router.post("/upload-nfe", response_model=UploadNFEResponse, status_code=status.HTTP_201_CREATED)
@limiter.limit("10/minute")
async def upload_nfe(
    request: Request,
    file: UploadFile = File(..., description="NFe XML file"),
    db: AsyncSession = Depends(get_secure_session)
) -> UploadNFEResponse:
    """
    Upload and process an NFe XML file.
    
    - Computes SHA-256 hash of the file content
    - Parses the XML using the NFe parser
    - Creates DocumentExtraction with lines and matches SKUs
    """
    if file.content_type not in ["text/xml", "application/xml"]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="File must be XML (text/xml or application/xml)"
        )

    # Read file content
    content = await file.read()
    
    if len(content) > 10 * 1024 * 1024:
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail="File size exceeds 10MB limit"
        )
    
    # Compute SHA-256 hash
    file_hash = hashlib.sha256(content).hexdigest()
    
    # Decode as UTF-8
    try:
        xml_content = content.decode("utf-8")
    except UnicodeDecodeError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="File must be valid UTF-8 encoded XML"
        )
    
    # Get tenant_id from session (RLS context)
    from packages.tenant.rls import get_current_tenant_id
    tenant_id = get_current_tenant_id()
    if not tenant_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Tenant context not found"
        )
    
    # Generate a safe file path
    file_path = f"uploads/{tenant_id}/{file_hash}_{file.filename}"
    
    # Process through ingestion pipeline
    pipeline = IngestionPipeline(db)
    try:
        extraction = await pipeline.ingest_nfe_xml(
            tenant_id=tenant_id,
            file_path=file_path,
            file_hash=file_hash,
            xml_content=xml_content
        )
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    
    await db.commit()
    
    return UploadNFEResponse(
        id=extraction.id,
        invoice_number=extraction.invoice_number_candidate or "UNKNOWN",
        status="NEEDS_REVIEW",
        total_amount=float(extraction.total_amount_candidate or 0.0)
    )

class UploadBatchResponse(BaseModel):
    batch_id: str
    document_ids: List[uuid.UUID]
    status: str
    message: str

@router.post("/upload-nfe-batch", response_model=UploadBatchResponse, status_code=status.HTTP_202_ACCEPTED)
@limiter.limit("5/minute")
async def upload_nfe_batch(
    request: Request,
    files: List[UploadFile] = File(..., description="Multiple NFe XML files"),
    db: AsyncSession = Depends(get_secure_session)
) -> UploadBatchResponse:
    """
    Upload and process multiple NFe XML files asynchronously via Celery worker.
    """
    from packages.tenant.rls import get_current_tenant_id
    from apps.worker.tasks import process_nfe_batch_task
    import os

    tenant_id = get_current_tenant_id()
    if not tenant_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Tenant context not found"
        )
        
    pipeline = IngestionPipeline(db)
    raw_doc_ids = []
    
    for file in files:
        if file.content_type not in ["text/xml", "application/xml"]:
            continue
            
        content = await file.read()
        if len(content) > 10 * 1024 * 1024:
            continue
            
        file_hash = hashlib.sha256(content).hexdigest()
        
        try:
            xml_content = content.decode("utf-8")
        except UnicodeDecodeError:
            continue # Skip invalid files
            
        file_path = f"uploads/{tenant_id}/{file_hash}_{file.filename}"
        os.makedirs(os.path.dirname(file_path), exist_ok=True)
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(xml_content)
            
        raw_doc = await pipeline.create_raw_document(tenant_id, file_path, file_hash)
        raw_doc_ids.append(str(raw_doc.id))
        
    await db.commit()
    
    if not raw_doc_ids:
        raise HTTPException(status_code=400, detail="No valid XML files provided.")
        
    batch_id = str(uuid.uuid4())
    process_nfe_batch_task.delay(str(tenant_id), raw_doc_ids)
    
    return UploadBatchResponse(
        batch_id=batch_id,
        document_ids=[uuid.UUID(doc_id) for doc_id in raw_doc_ids],
        status="PROCESSING",
        message=f"Queued {len(raw_doc_ids)} documents for asynchronous extraction."
    )


@router.get("/extractions", response_model=List[ExtractionListResponse])
async def list_extractions(
    db: AsyncSession = Depends(get_secure_session)
) -> List[ExtractionListResponse]:
    """
    List all document extractions for the current tenant, ordered by created_at DESC.
    """
    from packages.tenant.rls import get_current_tenant_id
    tenant_id = get_current_tenant_id()
    if not tenant_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Tenant context not found"
        )
    
    stmt = (
        select(DocumentExtraction, DocumentUpload.status)
        .join(DocumentUpload, DocumentExtraction.document_upload_id == DocumentUpload.id)
        .where(DocumentExtraction.tenant_id == tenant_id)
        .order_by(DocumentExtraction.created_at.desc())
    )
    
    result = await db.execute(stmt)
    rows = result.all()
    
    response = []
    for extraction, status_ in rows:
        response.append(ExtractionListResponse(
            id=extraction.id,
            invoice_number=extraction.invoice_number_candidate or "UNKNOWN",
            issue_date=extraction.issue_date_candidate,
            total_amount=float(extraction.total_amount_candidate or 0.0),
            status=status_,
            created_at=extraction.created_at,
            supplier_name=extraction.supplier_name_candidate
        ))
    
    return response


@router.get("/extractions/{extraction_id}", response_model=ExtractionDetailResponse)
async def get_extraction(
    extraction_id: uuid.UUID,
    db: AsyncSession = Depends(get_secure_session)
) -> ExtractionDetailResponse:
    """
    Get a document extraction by ID with all its lines.
    """
    from packages.tenant.rls import get_current_tenant_id
    tenant_id = get_current_tenant_id()
    if not tenant_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Tenant context not found"
        )
    
    stmt = (
        select(DocumentExtraction, DocumentUpload.status)
        .join(DocumentUpload, DocumentExtraction.document_upload_id == DocumentUpload.id)
        .where(
            DocumentExtraction.id == extraction_id,
            DocumentExtraction.tenant_id == tenant_id
        )
    )
    result = await db.execute(stmt)
    row = result.first()
    
    if not row:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Extraction not found"
        )
    
    extraction, status_ = row
    
    # Get lines
    stmt_lines = (
        select(DocumentExtractionLine)
        .where(
            DocumentExtractionLine.document_extraction_id == extraction_id,
            DocumentExtractionLine.tenant_id == tenant_id
        )
        .order_by(DocumentExtractionLine.created_at)
    )
    result_lines = await db.execute(stmt_lines)
    lines = result_lines.scalars().all()
    
    return ExtractionDetailResponse(
        id=extraction.id,
        invoice_number=extraction.invoice_number_candidate or "UNKNOWN",
        issue_date=extraction.issue_date_candidate,
        total_amount=float(extraction.total_amount_candidate or 0.0),
        status=status_,
        created_at=extraction.created_at,
        supplier_name=extraction.supplier_name_candidate,
        lines=[
            ExtractionLineResponse(
                id=line.id,
                raw_description=line.raw_description,
                raw_code=line.raw_code,
                raw_quantity=float(line.raw_quantity),
                raw_uom=line.raw_uom,
                raw_unit_price=float(line.raw_unit_price or 0.0),
                match_status="MATCHED" if line.normalized_sku_id else "UNMATCHED"
            )
            for line in lines
        ]
    )


@router.post("/extractions/{extraction_id}/approve", response_model=ApproveResponse)
async def approve_extraction(
    extraction_id: uuid.UUID,
    db: AsyncSession = Depends(get_secure_session)
) -> ApproveResponse:
    """
    Approve a document extraction and create a SupplierInvoice.
    
    Requires extraction to be in READY_FOR_APPROVAL status and all lines matched to SKUs.
    """
    from packages.tenant.rls import get_current_tenant_id
    tenant_id = get_current_tenant_id()
    if not tenant_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Tenant context not found"
        )
    
    approval_service = DocumentApprovalService(db)
    try:
        invoice = await approval_service.approve_extraction(tenant_id, extraction_id)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    
    await db.commit()
    
    return ApproveResponse(
        success=True,
        invoice_id=invoice.id
    )