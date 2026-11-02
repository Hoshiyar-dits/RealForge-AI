from app.database.database import localSession
from app.roles.repository import RoleRepository
from app.roles.dto.CreateRole import CreateRole
from app.roles.dto.CreatePermission import CreatePermission

# Idempotent: creates whatever is missing, never removes anything.
# Run: python -m app.seeders.roles_seeder

default_permissions = {
    "product.view": "View products",
    "product.create": "Create products",
    "product.update": "Update products",
    "product.delete": "Delete products",
    "assistant.product": "Ask the product assistant about products and their features",
    "assistant.technician": "Ask the technician assistant about parts, how they work and repairs",
    "assistant.admin": "Ask the admin assistant about the whole catalog and knowledge base",
    "user.manage": "List users and assign roles / permissions to them",
    "technician.manage": "Add, update and delete technicians",
    "role.manage": "Manage roles and their permissions",
    "permission.manage": "Manage permissions",
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
            permission = repository.get_permission_by_name(name) or repository.create_permission(CreatePermission(name=name, description=description))
            permission_ids[name] = permission.id

        for name, (description, permissions) in default_roles.items():
            role = repository.get_role_by_name(name) or repository.create_role(CreateRole(name=name, description=description))
            repository.add_role_permissions(role.id, [permission_ids[p] for p in permissions])
        print(f"Seeded {len(default_permissions)} permissions and {len(default_roles)} roles")
    finally:
        db.close()

if __name__ == "__main__":
    seed()
