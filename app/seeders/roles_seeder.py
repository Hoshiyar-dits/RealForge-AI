from app.database.database import localSession
from app.roles.repository import RoleRepository

# Seeds every role and permission. Idempotent: creates whatever is missing, never removes anything,
# so changes made through the sync APIs are kept.
# Run: python -m app.seeders.roles_seeder

default_permissions = {
    "product.view": "View products",
    "product.create": "Create products",
    "product.update": "Update products",
    "product.delete": "Delete products",
    "assistant.product": "Ask the product assistant about products and their features",
    "assistant.technician": "Ask the technician assistant about parts, how they work and repairs",
    "assistant.admin": "Ask the admin assistant about the whole catalog and knowledge base",
    "user.manage": "List users and sync their roles",
    "technician.manage": "Add, update and delete technicians",
    "role.manage": "Sync the permissions of a role",
}

default_roles = {
    "admin": ("Full access", list(default_permissions)),
    "technician": ("Asks about parts, how they work and repair steps", ["product.view", "assistant.product", "assistant.technician"]),
    "user": ("Asks about products and their features", ["product.view", "assistant.product"]),
}

def seed():
    db = localSession()
    try:
        repository = RoleRepository(db)
        permission_ids = {}
        for name, description in default_permissions.items():
            permission = repository.get_permission_by_name(name) or repository.create_permission(name, description)
            permission_ids[name] = permission.id

        for name, (description, permissions) in default_roles.items():
            role = repository.get_role_by_name(name) or repository.create_role(name, description)
            repository.add_role_permissions(role.id, [permission_ids[p] for p in permissions])
        print(f"Seeded {len(default_permissions)} permissions and {len(default_roles)} roles")
    finally:
        db.close()

if __name__ == "__main__":
    seed()
