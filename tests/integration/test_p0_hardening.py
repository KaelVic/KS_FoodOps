import pytest
import uuid
from decimal import Decimal
from unittest.mock import AsyncMock, MagicMock

from packages.security.rbac import has_permission, VALID_ROLES, ROLE_PERMISSIONS
from packages.tenant.service import TenantService
from packages.tenant.models import TenantMembership
from modules.costing.engine import CostingEngine
from modules.menu.service import MenuService
from modules.recipes.models import RecipeVersion


def test_rbac_permission_matrix():
    """Verify that roles have strict, appropriate permissions."""
    assert "admin" in VALID_ROLES
    assert "manager" in VALID_ROLES
    assert "viewer" in VALID_ROLES

    # Admin should have full access
    assert has_permission("admin", "inventory.close")
    assert has_permission("admin", "users.manage")
    assert has_permission("admin", "recipes.publish")
    assert has_permission("admin", "purchasing.approve")

    # Manager should NOT have admin-only actions
    assert not has_permission("manager", "inventory.close")
    assert not has_permission("manager", "users.manage")
    assert not has_permission("manager", "recipes.publish")
    assert not has_permission("manager", "purchasing.approve")
    # But manager should have operational actions
    assert has_permission("manager", "inventory.count")
    assert has_permission("manager", "inventory.adjust")
    assert has_permission("manager", "purchasing.receive")

    # Viewer should be read-only
    assert has_permission("viewer", "inventory.read")
    assert has_permission("viewer", "recipes.read")
    assert not has_permission("viewer", "inventory.count")
    assert not has_permission("viewer", "inventory.adjust")
    assert not has_permission("viewer", "purchasing.create")
    assert not has_permission("viewer", "purchasing.receive")
    assert not has_permission("viewer", "users.manage")

    # Unknown role should have zero permissions
    assert not has_permission("superadmin", "inventory.read")
    assert not has_permission("hacker", "inventory.close")


@pytest.mark.asyncio
async def test_membership_role_validation():
    """TenantService must reject invalid roles when creating or updating memberships."""
    mock_db = MagicMock()
    mock_db.add = MagicMock()
    mock_db.flush = AsyncMock()
    tenant_id = uuid.uuid4()

    # Reject invalid roles
    with pytest.raises(ValueError, match="Invalid role 'invalid_role'"):
        await TenantService.create_membership(mock_db, tenant_id, "user-1", "invalid_role")

    with pytest.raises(ValueError, match="Invalid role 'super_god_mode'"):
        await TenantService.update_membership_role(mock_db, tenant_id, uuid.uuid4(), "super_god_mode")


@pytest.mark.asyncio
async def test_cannot_demote_only_admin():
    """TenantService must prevent demoting the sole administrator."""
    mock_db = MagicMock()
    tenant_id = uuid.uuid4()
    membership_id = uuid.uuid4()

    admin_membership = TenantMembership(
        id=membership_id,
        tenant_id=tenant_id,
        user_id="admin-1",
        role="admin"
    )

    # Mock get_membership returning the admin
    mock_res_membership = MagicMock()
    mock_res_membership.scalar_one_or_none.return_value = admin_membership

    # Mock count query returning 1 admin
    mock_res_count = MagicMock()
    mock_res_count.scalar.return_value = 1

    mock_db.execute = AsyncMock(side_effect=[mock_res_membership, mock_res_count])
    mock_db.flush = AsyncMock()

    with pytest.raises(ValueError, match="Cannot demote the only administrator"):
        await TenantService.update_membership_role(mock_db, tenant_id, membership_id, "manager")


@pytest.mark.asyncio
async def test_costing_engine_deterministic_zero():
    """CostingEngine must return 0.00 without throwing errors or inventing non-zero fallbacks when SKU has no balance/receipts."""
    mock_db = MagicMock()
    tenant_id = uuid.uuid4()
    sku_id = uuid.uuid4()

    # Mock empty StockBalanceProjection
    mock_bal_res = MagicMock()
    mock_bal_res.scalars.return_value.all.return_value = []

    # Mock empty StockLedgerEntry
    mock_led_res = MagicMock()
    mock_led_res.scalar_one_or_none.return_value = None

    # Mock historical CMP returning 0
    mock_cmp_res = MagicMock()
    mock_cmp_res.scalars.return_value.all.return_value = []

    mock_db.execute = AsyncMock(side_effect=[mock_bal_res, mock_led_res, mock_cmp_res])

    cost = await CostingEngine.get_sku_cost(mock_db, tenant_id, sku_id)
    assert cost == Decimal("0.00")
    assert cost != Decimal("10.00")  # Ensures fake fallback R$ 10 is eliminated
