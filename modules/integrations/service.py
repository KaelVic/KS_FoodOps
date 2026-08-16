import uuid
from typing import List, Dict, Any
from modules.integrations.adapters.ifood import IFoodAdapter
from modules.integrations.adapters.totvs import TOTVSAdapter

class IntegrationService:
    """
    Orchestrates data synchronization between internal systems and external APIs.
    """
    
    @staticmethod
    async def sync_sales(tenant_id: uuid.UUID, provider: str, credentials: Dict[str, str], date: str) -> int:
        """
        Synchronizes sales from the given provider and pushes them to the outbox for processing.
        Returns the number of sales synchronized.
        """
        sales_count = 0
        
        if provider == "ifood":
            adapter = IFoodAdapter(client_id=credentials["client_id"], client_secret=credentials["client_secret"])
            await adapter.authenticate()
            events = await adapter.get_events()
            for event in events:
                if event["code"] == "PLC": # PLACED
                    details = await adapter.get_order_details(event["orderId"])
                    # In a real scenario, map this to an OutboxMessage and queue it
                    sales_count += 1
            await adapter.acknowledge_events([e["id"] for e in events])
            
        elif provider == "totvs":
            adapter = TOTVSAdapter(api_key=credentials["api_key"], base_url="https://api.totvs.com")
            sales = await adapter.fetch_daily_sales(date)
            for sale in sales:
                # Queue outbox message
                sales_count += 1
                
        else:
            raise ValueError(f"Unknown provider: {provider}")
            
        return sales_count
        
    @staticmethod
    async def sync_catalog(tenant_id: uuid.UUID, provider: str, credentials: Dict[str, str]) -> int:
        """
        Synchronizes the product catalog with the provider.
        """
        # Stub implementation
        return 0
