import pytest
import uuid
from decimal import Decimal
from datetime import datetime, timezone, timedelta

from packages.jobs.models import OutboxMessage
from packages.jobs.worker import OutboxWorker
from modules.automation.restock import RestockEngine
from modules.intelligence.models import InventoryPolicy, PurchaseSuggestion
from packages.tenant.models import Tenant
from sqlalchemy import text, select

@pytest.mark.asyncio
async def test_restock_engine(owner_session, test_db, tenant_id):
    """
    Tests that the restock engine successfully calls intelligence layer.
    """
    location_id = uuid.uuid4()
    sku_id = uuid.uuid4()
    
    await test_db.execute(
        text("SELECT set_config('app.current_tenant_id', :t_id, false)"),
        {"t_id": str(tenant_id)}
    )
    
    # Needs some DB setup to avoid FK errors: Category, UOM, SKU, BU, Location
    bu_id = uuid.uuid4()
    await test_db.execute(text("INSERT INTO business_units (id, tenant_id, name) VALUES (:id, :t_id, 'BU')"), {"id": str(bu_id), "t_id": str(tenant_id)})
    await test_db.execute(text("INSERT INTO locations (id, tenant_id, business_unit_id, name) VALUES (:id, :t_id, :bu_id, 'Loc')"), {"id": str(location_id), "t_id": str(tenant_id), "bu_id": str(bu_id)})
    
    uom_id = uuid.uuid4()
    await test_db.execute(text("INSERT INTO uoms (id, tenant_id, name, symbol, base_type) VALUES (:id, :t_id, 'Unit', 'UN', 'count')"), {"id": str(uom_id), "t_id": str(tenant_id)})
    
    await test_db.execute(text("INSERT INTO skus (id, tenant_id, name, base_uom_id) VALUES (:id, :t_id, 'Item', :uom_id)"), {"id": str(sku_id), "t_id": str(tenant_id), "uom_id": str(uom_id)})
    
    # Create InventoryPolicy
    policy = InventoryPolicy(
        tenant_id=uuid.UUID(tenant_id),
        location_id=location_id,
        sku_id=sku_id,
        abc_class='A',
        min_stock=Decimal('10.0'),
        target_stock=Decimal('50.0')
    )
    test_db.add(policy)
    await test_db.commit()
    
    await test_db.execute(
        text("SELECT set_config('app.current_tenant_id', :t_id, false)"),
        {"t_id": str(tenant_id)}
    )
    
    # Run restock cycle
    suggestions = await RestockEngine.run_restock_cycle(test_db, uuid.UUID(tenant_id), location_id)
    
    # Expect 1 suggestion since on_hand = 0 and target = 50
    assert len(suggestions) == 1
    
    # Re-set context because RestockEngine commits and drops connection
    await test_db.execute(
        text("SELECT set_config('app.current_tenant_id', :t_id, false)"),
        {"t_id": str(tenant_id)}
    )
    
    # Query it back instead of reading from expired instance
    result = await test_db.execute(select(PurchaseSuggestion).where(PurchaseSuggestion.sku_id == sku_id))
    sugg = result.scalar_one()
    assert sugg.suggested_quantity == Decimal('50.0')

@pytest.mark.asyncio
async def test_worker_exponential_backoff(test_db, tenant_id):
    """
    Tests that a failing message in the outbox is correctly retried with exponential backoff.
    """
    await test_db.execute(
        text("SELECT set_config('app.current_tenant_id', :t_id, false)"),
        {"t_id": str(tenant_id)}
    )
    
    msg_id = uuid.uuid4()
    msg = OutboxMessage(
        id=msg_id,
        tenant_id=uuid.UUID(tenant_id),
        aggregate_type="Test",
        aggregate_id="123",
        type="TestEvent",
        payload={"foo": "bar"},
        status="PENDING",
        retry_count=0
    )
    test_db.add(msg)
    await test_db.commit()
    
    # Create a mock session maker that returns our test_db (with RLS context)
    from contextlib import asynccontextmanager
    @asynccontextmanager
    async def mock_session_maker():
        await test_db.execute(
            text("SELECT set_config('app.current_tenant_id', :t_id, false)"),
            {"t_id": str(tenant_id)}
        )
        yield test_db
        
    worker = OutboxWorker(poll_interval=1, session_maker=mock_session_maker)
    
    # We monkey-patch handle_message to always raise an exception
    async def mock_handle_message(message):
        print("HANDLING MESSAGE", message.id)
        raise ValueError("Simulated failure")
        
    worker.handle_message = mock_handle_message
    
    # Process pending (will pick up the message and fail it)
    await worker.process_pending_messages()
    
    print("FINISHED WORKER")
    
    # Re-set context just in case commit cleared it
    await test_db.execute(
        text("SELECT set_config('app.current_tenant_id', :t_id, false)"),
        {"t_id": str(tenant_id)}
    )
    
    # Fetch message from DB
    result = await test_db.execute(select(OutboxMessage).where(OutboxMessage.id == msg_id))
    updated_msg = result.scalar_one()
    
    assert updated_msg.status == 'PENDING'
    assert updated_msg.retry_count == 1
    assert updated_msg.next_retry_at is not None
    
    # Check that next_retry_at is in the future
    assert updated_msg.next_retry_at > datetime.now(timezone.utc)
