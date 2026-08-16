import pytest
import uuid
from datetime import datetime, timezone, timedelta
from sqlalchemy import text
from modules.inventory.models import AccountingPeriod
from modules.inventory.service import InventoryService
from packages.tenant.models import Tenant

@pytest.mark.asyncio
async def test_ledger_guard_prevents_backdating(test_db, tenant_id):
    """
    Test that an attempt to post a StockMovement within a CLOSED AccountingPeriod fails.
    """
    await test_db.execute(text("SELECT set_config('app.current_tenant_id', :t, false)"), {"t": str(tenant_id)})
    
    now = datetime.now(timezone.utc)
    # Create closed period covering 'now'
    period = AccountingPeriod(
        tenant_id=uuid.UUID(tenant_id),
        start_date=now - timedelta(days=30),
        end_date=now + timedelta(days=30),
        status='CLOSED',
        closed_at=now
    )
    test_db.add(period)
    await test_db.commit()

    await test_db.execute(text("SELECT set_config('app.current_tenant_id', :t, false)"), {"t": str(tenant_id)})
    
    inv_service = InventoryService(test_db)
    
    # We can just call _guard_accounting_period directly to unit test the guard
    with pytest.raises(ValueError, match="within a closed accounting period"):
        await inv_service._guard_accounting_period(uuid.UUID(tenant_id), now)

@pytest.mark.asyncio
async def test_close_period(test_db, tenant_id):
    await test_db.execute(text("SELECT set_config('app.current_tenant_id', :t, false)"), {"t": str(tenant_id)})
    now = datetime.now(timezone.utc)
    
    period = AccountingPeriod(
        tenant_id=uuid.UUID(tenant_id),
        start_date=now - timedelta(days=30),
        end_date=now + timedelta(days=30),
        status='OPEN'
    )
    test_db.add(period)
    await test_db.flush()
    
    inv_service = InventoryService(test_db)
    closed = await inv_service.close_period(period.id, uuid.UUID(tenant_id))
    assert closed.status == 'CLOSED'
