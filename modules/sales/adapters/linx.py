from typing import Dict, Any, List
from datetime import datetime, timezone
from modules.sales.adapters.base import POSAdapter

class LinxAdapter(POSAdapter):
    def parse(self, payload: Dict[str, Any]) -> List[Dict[str, Any]]:
        # Mock Linx Degust payload parsing
        # Example payload: {"TicketNumber": "ABC-123", "Timestamp": "2023-10-01T12:00:00Z", "Products": [{"SKU": "uuid", "Quantity": 2, "UnitPrice": 10.0, "FinalPrice": 20.0}]}
        parsed_items = []
        order_id = payload.get("TicketNumber", "unknown")
        sale_date = payload.get("Timestamp", datetime.now(timezone.utc).isoformat())
        
        for item in payload.get("Products", []):
            parsed_items.append({
                "pos_order_id": order_id,
                "sale_date": sale_date,
                "sku_id": item.get("SKU"),
                "quantity": float(item.get("Quantity", 0)),
                "unit_price": float(item.get("UnitPrice", 0)),
                "net_amount": float(item.get("FinalPrice", 0))
            })
        return parsed_items
