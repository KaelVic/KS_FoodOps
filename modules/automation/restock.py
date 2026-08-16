import logging
import uuid
from typing import List
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from modules.intelligence.service import IntelligenceService
from modules.intelligence.models import PurchaseSuggestion
from modules.catalog.models import Category # Using standard tables for location queries if needed

logger = logging.getLogger(__name__)

class RestockEngine:
    """
    Automation engine for triggering and orchestrating stock replenishment.
    """
    
    @staticmethod
    async def run_restock_cycle(db: AsyncSession, tenant_id: uuid.UUID, location_id: uuid.UUID) -> List[PurchaseSuggestion]:
        """
        Runs the intelligence service to generate purchase suggestions for a given location.
        """
        logger.info(f"Running restock cycle for tenant {tenant_id}, location {location_id}")
        
        intelligence = IntelligenceService(db)
        
        # 1. Update operational alerts for stockout risks
        await intelligence.generate_operational_alerts(tenant_id, location_id)
        
        # 2. Generate deterministic purchase suggestions
        suggestions = await intelligence.generate_purchase_suggestions(tenant_id, location_id)
        
        # Commit the transaction to save generated suggestions
        await db.commit()
        
        logger.info(f"Restock cycle generated {len(suggestions)} suggestions.")
        return suggestions
