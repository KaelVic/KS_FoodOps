import pytest
import uuid
from sqlalchemy import text
from packages.audit.service import AuditService
from packages.audit.models import AuditLog

@pytest.mark.asyncio
async def test_audit_log_creation(test_db, tenant_id):
    """
    Test that an audit log can be successfully created and saved.
    """
    actor_id = uuid.uuid4() # Mock actor
    
    # Set the tenant_id context for the app session
    from sqlalchemy import text
    await test_db.execute(
        text("SELECT set_config('app.current_tenant_id', :t_id, false)"),
        {"t_id": str(tenant_id)}
    )
    
    # 1. Log an action
    audit_entry = await AuditService.log_action(
        db=test_db,
        tenant_id=tenant_id,
        actor_id=actor_id,
        action="TEST_ACTION",
        resource_type="tests",
        changes_payload={"old": "a", "new": "b"},
        client_ip="127.0.0.1"
    )
    
    assert audit_entry.id is not None
    assert str(audit_entry.tenant_id) == str(tenant_id)
    assert str(audit_entry.actor_id) == str(actor_id)
    assert audit_entry.action == "TEST_ACTION"
    assert audit_entry.changes_payload == {"old": "a", "new": "b"}

@pytest.mark.asyncio
async def test_audit_log_rls(owner_session, test_db, tenant_id):
    """
    Test that RLS properly isolates audit logs by tenant.
    """
    tenant_1 = tenant_id
    tenant_2 = uuid.uuid4()
    
    # Create tenant 2 via owner session
    await owner_session.execute(
        text("INSERT INTO tenants (id, name) VALUES (:id, 'Tenant 2')"),
        {"id": str(tenant_2)}
    )
    await owner_session.commit()
    
    actor_id = uuid.uuid4()
    
    # Insert audit logs for both tenants
    await owner_session.execute(
        text("INSERT INTO audit_logs (id, tenant_id, actor_id, action, resource_type, changes_payload) "
             "VALUES (:id, :t_id, :a_id, 'ACTION', 'res', '{}')"),
        [
            {"id": str(uuid.uuid4()), "t_id": str(tenant_1), "a_id": str(actor_id)},
            {"id": str(uuid.uuid4()), "t_id": str(tenant_2), "a_id": str(actor_id)}
        ]
    )
    await owner_session.commit()
    
    # Set the tenant_id context for the app session to tenant 1
    await test_db.execute(
        text("SELECT set_config('app.current_tenant_id', :t_id, false)"),
        {"t_id": str(tenant_1)}
    )
    
    # When querying with test_db (which is bound to tenant_1 by RLS)
    # it should only return logs for tenant 1
    result = await test_db.execute(text("SELECT tenant_id FROM audit_logs"))
    rows = result.scalars().all()
    
    # Ensure RLS restricted the view to only tenant 1
    assert len(rows) >= 1
    for row_tenant_id in rows:
        assert str(row_tenant_id) == str(tenant_1)
