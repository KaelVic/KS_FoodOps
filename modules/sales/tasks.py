import logging
from typing import List, Dict, Any
import uuid

from apps.worker.worker import tenant_session
from modules.sales.service import SalesService

logger = logging.getLogger(__name__)

async def process_pos_sales_background_task(tenant_id: str, pos_system: str, import_reference: str, sales_data: List[Dict[str, Any]]):
    """
    Processes POS sales import asynchronously natively within FastAPI's event loop.
    Does not require Celery.
    """
    try:
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
            logger.info(f"Successfully processed POS sales batch {import_reference} for tenant {tenant_id}")
    except Exception as e:
        logger.error(f"Error processing POS sales batch {import_reference}: {e}")
