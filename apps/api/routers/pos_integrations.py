import logging
import uuid
from typing import Dict, Any

from fastapi import APIRouter, Depends, HTTPException, status, Request, BackgroundTasks
from pydantic import BaseModel

from modules.sales.adapters.totvs import TOTVSAdapter
from modules.sales.adapters.linx import LinxAdapter
from modules.sales.adapters.saipos import SaiposAdapter
from modules.sales.adapters.ifood import IfoodAdapter
from packages.tenant.rls import get_current_tenant_id
from modules.sales.tasks import process_pos_sales_background_task
from apps.api.main import limiter

logger = logging.getLogger(__name__)

router = APIRouter(tags=["POS Integrations"])

class WebhookResponse(BaseModel):
    message: str
    import_reference: str

ADAPTERS = {
    "totvs": TOTVSAdapter(),
    "linx": LinxAdapter(),
    "saipos": SaiposAdapter(),
    "ifood": IfoodAdapter(),
}

import hmac
import os

@router.post("/webhook/{pos_system}", response_model=WebhookResponse, status_code=status.HTTP_202_ACCEPTED)
@limiter.limit("100/minute")
async def pos_webhook(
    pos_system: str,
    request: Request,
    background_tasks: BackgroundTasks
) -> WebhookResponse:
    """
    Ingest sales data from a POS system via webhook.
    Requires X-Tenant-ID and X-Webhook-Secret headers.
    """
    tenant_id = request.headers.get("X-Tenant-ID")
    if not tenant_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Missing X-Tenant-ID header"
        )
        
    # Validate Webhook Secret / Signature to prevent unauthorized webhook spoofing
    configured_secret = os.environ.get("POS_WEBHOOK_SECRET", "ksfoodops_pos_webhook_secret_key_default")
    received_secret = request.headers.get("X-Webhook-Secret")
    if not received_secret or not hmac.compare_digest(received_secret, configured_secret):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or missing X-Webhook-Secret"
        )

    pos_system = pos_system.lower()
    if pos_system not in ADAPTERS:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Unsupported POS system: {pos_system}"
        )

        
    try:
        payload = await request.json()
    except Exception:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid JSON payload")

    adapter = ADAPTERS[pos_system]
    try:
        parsed_items = adapter.parse(payload)
    except Exception as e:
        logger.error(f"Error parsing payload from {pos_system}: {e}")
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Error parsing payload")

    import_reference = f"webhook_{pos_system}_{uuid.uuid4()}"
    
    try:
        from apps.worker.tasks import process_pos_sales_batch_task
        process_pos_sales_batch_task.delay(
            tenant_id=tenant_id,
            pos_system=pos_system,
            import_reference=import_reference,
            sales_data=parsed_items
        )
    except Exception as e:
        logger.warning(f"Celery dispatch failed, falling back to native background task: {e}")
        background_tasks.add_task(
            process_pos_sales_background_task,
            tenant_id=tenant_id,
            pos_system=pos_system,
            import_reference=import_reference,
            sales_data=parsed_items
        )
    
    return WebhookResponse(
        message=f"Received payload from {pos_system}. Processing asynchronously.",
        import_reference=import_reference
    )
