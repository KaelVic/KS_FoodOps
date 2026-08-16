import pytest
import uuid
from sqlalchemy import text
from packages.notifications.service import NotificationDispatcher

@pytest.mark.asyncio
async def test_notification_dispatch_and_retrieve(test_db, tenant_id):
    """
    Test creating a notification and retrieving it as unread.
    """
    # Set the tenant_id context for the app session
    await test_db.execute(
        text("SELECT set_config('app.current_tenant_id', :t_id, false)"),
        {"t_id": str(tenant_id)}
    )
    
    user_id = uuid.uuid4()
    
    # Dispatch notification
    notification = await NotificationDispatcher.dispatch_notification(
        db=test_db,
        tenant_id=tenant_id,
        user_id=user_id,
        type_="STOCK_ALERT",
        title="Low Stock",
        message="Item X is running low",
        metadata_payload={"item_id": 123}
    )
    
    assert notification.id is not None
    assert str(notification.tenant_id) == str(tenant_id)
    assert not notification.is_read
    
    # Retrieve unread
    unread = await NotificationDispatcher.get_unread_notifications(
        db=test_db,
        tenant_id=tenant_id,
        user_id=user_id
    )
    
    assert len(unread) == 1
    assert unread[0].id == notification.id
    
    # Mark as read
    await NotificationDispatcher.mark_as_read(test_db, notification.id)
    
    # Retrieve unread again
    unread_after = await NotificationDispatcher.get_unread_notifications(
        db=test_db,
        tenant_id=tenant_id,
        user_id=user_id
    )
    
    assert len(unread_after) == 0

@pytest.mark.asyncio
async def test_notification_rls(owner_session, test_db, tenant_id):
    """
    Test that RLS properly isolates notifications by tenant.
    """
    tenant_1 = tenant_id
    tenant_2 = uuid.uuid4()
    
    # Create tenant 2 via owner session
    await owner_session.execute(
        text("INSERT INTO tenants (id, name) VALUES (:id, 'Tenant 2')"),
        {"id": str(tenant_2)}
    )
    await owner_session.commit()
    
    user_id = uuid.uuid4()
    
    # Insert notifications for both tenants
    await owner_session.execute(
        text("INSERT INTO notifications (id, tenant_id, user_id, type, title, message, is_read) "
             "VALUES (:id, :t_id, :u_id, 'ALERT', 'Title', 'Message', false)"),
        [
            {"id": str(uuid.uuid4()), "t_id": str(tenant_1), "u_id": str(user_id)},
            {"id": str(uuid.uuid4()), "t_id": str(tenant_2), "u_id": str(user_id)}
        ]
    )
    await owner_session.commit()
    
    # Set the tenant_id context for the app session to tenant 1
    await test_db.execute(
        text("SELECT set_config('app.current_tenant_id', :t_id, false)"),
        {"t_id": str(tenant_1)}
    )
    
    # Retrieve unread using test_db
    result = await test_db.execute(text("SELECT tenant_id FROM notifications"))
    rows = result.scalars().all()
    
    # Ensure RLS restricted the view to only tenant 1
    assert len(rows) >= 1
    for row_tenant_id in rows:
        assert str(row_tenant_id) == str(tenant_1)
