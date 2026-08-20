from typing import List, Set

# Standard RBAC model mapping roles to permissions
VALID_ROLES: Set[str] = {"admin", "manager", "viewer"}

ROLE_PERMISSIONS = {
    "admin": [
        "inventory.read",
        "inventory.count",
        "inventory.close",
        "inventory.adjust",
        "purchasing.read",
        "purchasing.create",
        "purchasing.approve",
        "purchasing.receive",
        "recipes.read",
        "recipes.edit",
        "recipes.publish",
        "documents.read",
        "documents.review",
        "users.manage",
        "menu.read",
        "menu.edit",
        "reports.view",
        "orders.read",
        "orders.manage",
        "production.read",
        "production.manage",
        "rfq.read",
        "rfq.manage",
        "labor.read",
        "labor.manage",
        "financial.read",
        "financial.manage",
    ],
    "manager": [
        "inventory.read",
        "inventory.count",
        "inventory.adjust",
        "purchasing.read",
        "purchasing.create",
        "purchasing.receive",
        "recipes.read",
        "recipes.edit",
        "documents.read",
        "documents.review",
        "menu.read",
        "menu.edit",
        "reports.view",
        "orders.read",
        "orders.manage",
        "production.read",
        "production.manage",
        "rfq.read",
        "labor.read",
        "labor.manage",
        "financial.read",
    ],
    "viewer": [
        "inventory.read",
        "purchasing.read",
        "recipes.read",
        "documents.read",
        "menu.read",
        "reports.view",
        "orders.read",
        "production.read",
        "rfq.read",
        "labor.read",
        "financial.read",
    ]
}

def has_permission(role: str, required_permission: str) -> bool:
    """Check if a role has a specific permission."""
    permissions = ROLE_PERMISSIONS.get(role, [])
    return required_permission in permissions
