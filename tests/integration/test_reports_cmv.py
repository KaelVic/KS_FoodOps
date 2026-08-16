import pytest
from fastapi.testclient import TestClient
import os
import jwt
import uuid
from datetime import datetime, timedelta, timezone
from decimal import Decimal
from sqlalchemy import text

from apps.api.main import app
from modules.reporting.service import ReportingService
from modules.reporting.exporter import ReportExporter

client = TestClient(app)

JWT_SECRET = os.environ.get("JWT_SECRET", "dummy_secret_for_development_32_bytes_long_min!")
JWT_ALGORITHM = os.environ.get("JWT_ALGORITHM", "HS256")


def create_test_token(user_id: str = "test-user-123") -> str:
    """Create a valid JWT token for testing."""
    payload = {
        "sub": user_id,
        "email": "admin@ksfoodops.local",
        "exp": datetime.now(timezone.utc) + timedelta(hours=1)
    }
    return jwt.encode(payload, JWT_SECRET, algorithm=JWT_ALGORITHM)


def test_reports_endpoints_require_auth():
    """Test authentication requirements on reports endpoints."""
    # 1. /reports/losses
    res = client.get("/reports/losses")
    assert res.status_code in (401, 422)

    # 2. /reports/inventory/export/csv
    res = client.get("/reports/inventory/export/csv")
    assert res.status_code in (401, 422)

    # 3. /reports/inventory/export/sped
    res = client.get("/reports/inventory/export/sped")
    assert res.status_code in (401, 422)


def test_report_exporter_csv():
    """Unit test for ReportExporter CSV generation."""
    sample_data = [
        {
            "sku_id": "11111111-1111-1111-1111-111111111111",
            "sku_name": "Picanha Argentina",
            "category_name": "Carnes Nobres",
            "uom_symbol": "KG",
            "total_quantity": Decimal("25.500"),
            "unit_cost": Decimal("89.9000"),
            "total_value": Decimal("2292.45")
        },
        {
            "sku_id": "22222222-2222-2222-2222-222222222222",
            "sku_name": "Queijo Parmesao",
            "category_name": "Laticinios",
            "uom_symbol": "KG",
            "total_quantity": Decimal("10.000"),
            "unit_cost": Decimal("65.0000"),
            "total_value": Decimal("650.00")
        }
    ]
    
    csv_str = ReportExporter.export_inventory_valuation_csv(sample_data)
    assert "Insumo" in csv_str
    assert "Picanha Argentina" in csv_str
    assert "Queijo Parmesao" in csv_str
    assert "2292.45" in csv_str
    assert "Valor_Total_Estoque_R$" in csv_str


def test_report_exporter_sped_bloco_h():
    """Unit test for SPED Fiscal Bloco H layout generation."""
    sample_data = [
        {
            "sku_id": "SKU-001",
            "sku_name": "Vinho Malbec",
            "category_name": "Bebidas",
            "uom_symbol": "UN",
            "total_quantity": Decimal("12"),
            "total_value": Decimal("600.00")
        }
    ]
    
    sped_text = ReportExporter.export_to_sped_bloco_h(sample_data, datetime(2026, 8, 16))
    
    assert "|H001|0|" in sped_text
    assert "|H005|16082026|600,00|01|" in sped_text
    assert "|H010|SKU-001|UN|12,000|50,000000|600,00|0|||||" in sped_text
    assert "|H990|4|" in sped_text
