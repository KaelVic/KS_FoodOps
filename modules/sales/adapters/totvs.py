from typing import Dict, Any, List
from datetime import datetime, timezone
from modules.sales.adapters.base import POSAdapter

class TOTVSAdapter(POSAdapter):
    def parse(self, payload: Dict[str, Any]) -> List[Dict[str, Any]]:
        # Mock TOTVS Chef payload parsing
        # Example payload: {"ReceiptId": "123", "Date": "2023-10-01T12:00:00Z", "Items": [{"ProductId": "uuid", "Qty": 2, "Price": 10.0, "Total": 20.0}]}
        parsed_items = []
        order_id = payload.get("ReceiptId", "unknown")
        sale_date = payload.get("Date", datetime.now(timezone.utc).isoformat())
        
        for item in payload.get("Items", []):
            parsed_items.append({
                "pos_order_id": order_id,
                "sale_date": sale_date,
                "sku_id": item.get("ProductId"),
                "quantity": float(item.get("Qty", 0)),
                "unit_price": float(item.get("Price", 0)),
                "net_amount": float(item.get("Total", 0))
            })
        return parsed_items
