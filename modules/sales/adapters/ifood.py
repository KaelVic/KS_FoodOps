from typing import Dict, Any, List
from datetime import datetime, timezone
from modules.sales.adapters.base import POSAdapter

class IfoodAdapter(POSAdapter):
    def parse(self, payload: Dict[str, Any]) -> List[Dict[str, Any]]:
        # Mock iFood payload parsing
        # Example payload: {"orderId": "ifood-123", "createdAt": "2023-10-01T12:00:00Z", "items": [{"externalCode": "uuid", "quantity": 2, "price": 10.0, "totalPrice": 20.0}]}
        parsed_items = []
        order_id = payload.get("orderId", "unknown")
        sale_date = payload.get("createdAt", datetime.now(timezone.utc).isoformat())
        
        for item in payload.get("items", []):
            parsed_items.append({
                "pos_order_id": order_id,
                "sale_date": sale_date,
                "sku_id": item.get("externalCode"),
                "quantity": float(item.get("quantity", 0)),
                "unit_price": float(item.get("price", 0)),
                "net_amount": float(item.get("totalPrice", 0))
            })
        return parsed_items
