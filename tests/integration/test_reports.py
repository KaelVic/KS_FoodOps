import pytest
import uuid
from datetime import datetime, timezone, timedelta
from decimal import Decimal
from sqlalchemy import text
from modules.reporting.consolidated import ConsolidatedReportService

@pytest.mark.asyncio
async def test_consolidated_report_empty(test_db, tenant_id):
    await test_db.execute(text("SELECT set_config('app.current_tenant_id', :t, false)"), {"t": str(tenant_id)})
    
    now = datetime.now(timezone.utc)
    start = now - timedelta(days=7)
    end = now
    loc_id = uuid.uuid4()
    
    report_service = ConsolidatedReportService(test_db)
    report = await report_service.generate(uuid.UUID(tenant_id), loc_id, start, end)
    
    assert isinstance(report['total_revenue'], Decimal)
    assert isinstance(report['actual_cmv'], Decimal)
    assert isinstance(report['theoretical_consumption'], Decimal)
    assert isinstance(report['registered_losses'], Decimal)
    assert isinstance(report['unexplained_variance'], Decimal)
