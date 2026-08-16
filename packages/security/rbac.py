from typing import List

# Simple RBAC model mapping roles to permissions
# In a real-world scenario, this might be loaded from a database or a config file.

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
        "documents.review"
    ],
    "manager": [
        "inventory.read",
        "inventory.count",
        "purchasing.read",
        "purchasing.create",
        "purchasing.receive",
        "recipes.read",
        "documents.read"
    ],
    "viewer": [
        "inventory.read",
        "purchasing.read",
        "recipes.read",
        "documents.read"
    ]
}

def has_permission(role: str, required_permission: str) -> bool:
    """Check if a role has a specific permission."""
    permissions = ROLE_PERMISSIONS.get(role, [])
    return required_permission in permissions
