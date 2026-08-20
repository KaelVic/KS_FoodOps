import pytest
import uuid
from decimal import Decimal
from datetime import datetime, timezone
from unittest.mock import AsyncMock, MagicMock, patch

from modules.inventory.service import InventoryService
from modules.inventory.models import (
    StockMovement,
    StockLedgerEntry,
    StockBalanceProjection,
    InventorySession,
    LossRecord
)
from modules.sales.service import SalesService
from modules.sales.models import Sale, SalesImport
from modules.reporting.consolidated import ConsolidatedReportService


@pytest.mark.asyncio
async def test_reverse_movement_immutable_logic():
    """Validates immutable reversal creates counter-movement with inverted ledger entries."""
    mock_db = MagicMock()
    tenant_id = uuid.uuid4()
    location_id = uuid.uuid4()
    sku_id = uuid.uuid4()
    orig_mov_id = uuid.uuid4()
    actor_id = uuid.uuid4()

    # Original movement
    original_movement = StockMovement(
        id=orig_mov_id,
        tenant_id=tenant_id,
        location_id=location_id,
        type='RECEIPT',
        status='POSTED',
        posted_at=datetime.now(timezone.utc)
    )

    # Original entry (e.g. +100 kg at R$ 25.50)
    original_entry = StockLedgerEntry(
        id=uuid.uuid4(),
        tenant_id=tenant_id,
        movement_id=orig_mov_id,
        sku_id=sku_id,
        quantity=Decimal("100.00"),
        unit_cost=Decimal("25.50"),
        conversion_version_id=None,
        balance_after=Decimal("100.00")
    )

    # Balance projection
    balance_projection = StockBalanceProjection(
        id=uuid.uuid4(),
        tenant_id=tenant_id,
        location_id=location_id,
        sku_id=sku_id,
        quantity=Decimal("100.00"),
        total_value=Decimal("2550.00")
    )

    # Setup mock query results
    mock_acct_period = MagicMock()
    mock_acct_period.scalars.return_value.first.return_value = None

    mock_res_mov = MagicMock()
    mock_res_mov.scalar_one_or_none.return_value = original_movement

    mock_res_entries = MagicMock()
    mock_res_entries.scalars.return_value.all.return_value = [original_entry]

    mock_res_bal = MagicMock()
    mock_res_bal.scalar_one_or_none.return_value = balance_projection

    mock_db.execute = AsyncMock(side_effect=[
        mock_acct_period,
        mock_res_mov,
        mock_res_entries,
        mock_res_bal
    ])
    mock_db.flush = AsyncMock()
    mock_db.add = MagicMock()

    service = InventoryService(mock_db)
    
    with patch("packages.audit.service.AuditService.log_action", new_callable=AsyncMock) as mock_audit:
        reversal = await service.reverse_movement(
            movement_id=orig_mov_id,
            tenant_id=tenant_id,
            actor_user_id=actor_id,
            reason="Entered wrong batch"
        )

        assert reversal.type == "REVERSAL"
        assert reversal.status == "POSTED"
        assert reversal.reference_id == orig_mov_id
        assert reversal.reference_type == "StockMovement"
        assert reversal.actor_user_id == actor_id
        assert reversal.reason_code == "Entered wrong batch"

        # Check that original movement status changed to REVERSED
        assert original_movement.status == "REVERSED"

        # Check balance subtracted
        assert balance_projection.quantity == Decimal("0.00")
        assert balance_projection.total_value == Decimal("0.00")

        # Check audit log was called
        mock_audit.assert_called_once()
        call_args = mock_audit.call_args[1]
        assert call_args["action"] == "STOCK_MOVEMENT_REVERSED"
        assert call_args["tenant_id"] == tenant_id
        assert call_args["actor_id"] == actor_id


@pytest.mark.asyncio
async def test_cannot_reverse_a_reversal():
    """Anti-loop guard: attempting to reverse a reversal movement must raise ValueError."""
    mock_db = MagicMock()
    tenant_id = uuid.uuid4()
    reversal_mov_id = uuid.uuid4()

    reversal_movement = StockMovement(
        id=reversal_mov_id,
        tenant_id=tenant_id,
        location_id=uuid.uuid4(),
        type='REVERSAL',
        status='POSTED'
    )

    mock_acct_period = MagicMock()
    mock_acct_period.scalars.return_value.first.return_value = None

    mock_res_mov = MagicMock()
    mock_res_mov.scalar_one_or_none.return_value = reversal_movement

    mock_db.execute = AsyncMock(side_effect=[mock_acct_period, mock_res_mov])

    service = InventoryService(mock_db)
    with pytest.raises(ValueError, match="Cannot reverse a movement that is already a reversal"):
        await service.reverse_movement(reversal_mov_id, tenant_id)


@pytest.mark.asyncio
async def test_register_loss_records_actor_and_audit():
    """register_loss must associate actor_user_id and invoke AuditService."""
    mock_db = MagicMock()
    tenant_id = uuid.uuid4()
    location_id = uuid.uuid4()
    sku_id = uuid.uuid4()
    actor_id = uuid.uuid4()

    mock_acct_period = MagicMock()
    mock_acct_period.scalars.return_value.first.return_value = None

    balance_projection = StockBalanceProjection(
        id=uuid.uuid4(),
        tenant_id=tenant_id,
        location_id=location_id,
        sku_id=sku_id,
        quantity=Decimal("50.00"),
        total_value=Decimal("500.00") # unit_cost = 10.00
    )

    mock_res_bal = MagicMock()
    mock_res_bal.scalar_one_or_none.return_value = balance_projection

    mock_db.execute = AsyncMock(side_effect=[mock_acct_period, mock_res_bal])
    mock_db.flush = AsyncMock()
    mock_db.add = MagicMock()

    service = InventoryService(mock_db)

    with patch("packages.audit.service.AuditService.log_action", new_callable=AsyncMock) as mock_audit:
        loss = await service.register_loss(
            location_id=location_id,
            sku_id=sku_id,
            quantity=Decimal("5.00"),
            reason="EXPIRED",
            actor="Chef Rodrigo",
            tenant_id=tenant_id,
            actor_user_id=actor_id
        )

        assert loss.reason == "EXPIRED"
        assert loss.actor == "Chef Rodrigo"
        assert balance_projection.quantity == Decimal("45.00")
        assert balance_projection.total_value == Decimal("450.00")

        mock_audit.assert_called_once()
        assert mock_audit.call_args[1]["action"] == "STOCK_LOSS_RECORDED"
        assert mock_audit.call_args[1]["actor_id"] == actor_id


@pytest.mark.asyncio
async def test_sales_import_location_scoping():
    """SalesService.import_sales must attach location_id to individual Sale records."""
    mock_db = MagicMock()
    tenant_id = uuid.uuid4()
    location_id = uuid.uuid4()

    # Mock no existing import
    mock_existing = MagicMock()
    mock_existing.scalar_one_or_none.return_value = None
    mock_db.execute = AsyncMock(return_value=mock_existing)
    mock_db.flush = AsyncMock()

    sales_added = []
    def capture_add(item):
        if isinstance(item, Sale):
            sales_added.append(item)
    mock_db.add = MagicMock(side_effect=capture_add)

    service = SalesService(mock_db)
    sales_payload = [
        {
            "pos_sale_id": "SALE-001",
            "sale_date": "2026-08-20T12:00:00Z",
            "total_amount": "120.00",
            "lines": [{"pos_product_id": "SKU-BURGER", "quantity": "2", "unit_price": "60.00"}]
        }
    ]

    await service.import_sales(
        tenant_id=tenant_id,
        pos_system="TOAST",
        import_reference="TOAST-BATCH-001",
        sales_data=sales_payload,
        location_id=location_id
    )

    assert len(sales_added) == 1
    assert sales_added[0].location_id == location_id
    assert sales_added[0].total_amount == Decimal("120.00")
