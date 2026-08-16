from typing import Dict, Any, List
from datetime import datetime, timezone
from modules.sales.adapters.base import POSAdapter

class SaiposAdapter(POSAdapter):
    def parse(self, payload: Dict[str, Any]) -> List[Dict[str, Any]]:
        # Mock Saipos payload parsing
        # Example payload: {"id_pedido": "999", "data_hora": "2023-10-01T12:00:00Z", "itens": [{"id_produto": "uuid", "quantidade": 2, "valor_unitario": 10.0, "valor_total": 20.0}]}
        parsed_items = []
        order_id = payload.get("id_pedido", "unknown")
        sale_date = payload.get("data_hora", datetime.now(timezone.utc).isoformat())
        
        for item in payload.get("itens", []):
            parsed_items.append({
                "pos_order_id": str(order_id),
                "sale_date": sale_date,
                "sku_id": item.get("id_produto"),
                "quantity": float(item.get("quantidade", 0)),
                "unit_price": float(item.get("valor_unitario", 0)),
                "net_amount": float(item.get("valor_total", 0))
            })
        return parsed_items
