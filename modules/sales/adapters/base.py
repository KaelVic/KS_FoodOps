from abc import ABC, abstractmethod
from typing import Dict, Any, List

class POSAdapter(ABC):
    @abstractmethod
    def parse(self, payload: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Parses a POS webhook payload into the canonical format expected by SalesService:
        [
            {
                "pos_order_id": "string",
                "sale_date": "datetime string",
                "sku_id": "uuid string",
                "quantity": float,
                "unit_price": float,
                "net_amount": float
            },
            ...
        ]
        """
        pass
