import logging
from typing import List, Dict, Any, Optional
import uuid

from apps.worker.worker import celery_app, tenant_session, run_async
from modules.documents.service import IngestionPipeline
from modules.intelligence.service import IntelligenceService
from modules.sales.service import SalesService

logger = logging.getLogger(__name__)

@celery_app.task
def process_nfe_batch_task(tenant_id: str, raw_document_ids: List[str]):
    """Processes a batch of raw NFe documents asynchronously."""
    async def _process():
        async with tenant_session(tenant_id) as session:
            pipeline = IngestionPipeline(session)
            results = []
            for doc_id in raw_document_ids:
                try:
                    ext = await pipeline.process_document(uuid.UUID(doc_id))
                    results.append({"doc_id": doc_id, "status": "success", "extraction_id": str(ext.id)})
                except Exception as e:
                    logger.error(f"Error processing document {doc_id}: {e}")
                    results.append({"doc_id": doc_id, "status": "error", "message": str(e)})
            
            await session.commit()
            return results
            
    return run_async(_process())

@celery_app.task
def recalculate_nightly_intelligence_task(tenant_id: str, location_id: Optional[str] = None):
    """Nightly recalculation of ABC curves, purchase suggestions, and operational alerts."""
    async def _process():
        async with tenant_session(tenant_id) as session:
            service = IntelligenceService(session)
            loc_uuid = uuid.UUID(location_id) if location_id else None
            
            # Since ABC needs a specific location, if location is None we might want to iterate all locations.
            # For simplicity, if location_id is provided, process it.
            if loc_uuid:
                await service.calculate_abc_classification(uuid.UUID(tenant_id), loc_uuid)
                await service.generate_purchase_suggestions(uuid.UUID(tenant_id), loc_uuid)
                await service.generate_operational_alerts(uuid.UUID(tenant_id), loc_uuid)
            else:
                # Ideally fetch all locations for the tenant
                from sqlalchemy import select
                from packages.tenant.models import Location
                stmt = select(Location).where(Location.tenant_id == uuid.UUID(tenant_id))
                locations = (await session.execute(stmt)).scalars().all()
                for loc in locations:
                    await service.calculate_abc_classification(uuid.UUID(tenant_id), loc.id)
                    await service.generate_purchase_suggestions(uuid.UUID(tenant_id), loc.id)
                    await service.generate_operational_alerts(uuid.UUID(tenant_id), loc.id)
            
            await session.commit()
            return "Intelligence recalculated"
            
    return run_async(_process())

@celery_app.task
def process_pos_sales_batch_task(tenant_id: str, pos_system: str, import_reference: str, sales_data: List[Dict[str, Any]]):
    """Processes POS sales import asynchronously."""
    async def _process():
        async with tenant_session(tenant_id) as session:
            service = SalesService(session)
            # 1. Idempotently import sales
            sales_import = await service.import_sales(
                tenant_id=uuid.UUID(tenant_id),
                pos_system=pos_system,
                import_reference=import_reference,
                sales_data=sales_data
            )
            # 2. Process theoretical consumption
            await service.process_theoretical_consumption(sales_import.id, uuid.UUID(tenant_id))
            
            await session.commit()
            return {"sales_import_id": str(sales_import.id), "status": sales_import.status}
            
    return run_async(_process())

@celery_app.task
def schedule_intelligence_for_all_tenants():
    """Dispatches the nightly intelligence recalculation for all active tenants."""
    async def _process():
        from sqlalchemy import select
        from packages.tenant.models import Tenant
        from packages.tenant.database import async_session_maker
        
        async with async_session_maker() as session:
            stmt = select(Tenant).where(Tenant.is_active == True)
            tenants = (await session.execute(stmt)).scalars().all()
            
            for tenant in tenants:
                recalculate_nightly_intelligence_task.delay(str(tenant.id))
                
        return f"Dispatched intelligence for {len(tenants)} tenants."
        
    return run_async(_process())

@celery_app.task
def process_outbox_messages_task():
    """Periodic task to process pending outbox messages."""
    async def _process():
        from packages.jobs.worker import OutboxWorker
        worker = OutboxWorker(poll_interval=0)
        await worker.process_pending_messages()
        return "Outbox processed"
        
    return run_async(_process())

@celery_app.task
def cleanup_temporary_files_task():
    """Daily task to clean up old files in the uploads folder."""
    import os
    import time
    
    deleted_count = 0
    uploads_dir = "uploads"
    if not os.path.exists(uploads_dir):
        return "No uploads dir to clean."
        
    now = time.time()
    cutoff = now - (24 * 60 * 60) # 24 hours ago
    
    for root, dirs, files in os.walk(uploads_dir):
        for f in files:
            path = os.path.join(root, f)
            if os.stat(path).st_mtime < cutoff:
                try:
                    os.remove(path)
                    deleted_count += 1
                except Exception as e:
                    logger.error(f"Error removing {path}: {e}")
                    
    return f"Cleaned {deleted_count} temporary files."
