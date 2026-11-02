from app.database.database import localSession
from app.roles.repository import RoleRepository
from app.seeders.roles_seeder import seed as seed_roles
from app.users.dto.CreateUser import CreateUser
from app.users.repository import UserRepository
from app.users.service import hash_password

# Idempotent: creates the default admin if missing, never changes an existing password.
# Seeds roles first so the "admin" role exists.
# Run: python -m app.seeders.admin_seeder

admin_email = "admin@gmail.com"
admin_password = "Admin@12345"
admin_first_name = "Admin"
admin_last_name = "User"

def seed():
    seed_roles()
    db = localSession()
    try:
        users = UserRepository(db)
        roles = RoleRepository(db)
        user = users.get_by_email(admin_email)
        if not user:
            data = CreateUser(first_name=admin_first_name, last_name=admin_last_name, email=admin_email, password=admin_password)
            user = users.create(data, hash_password(data.password))
            print(f"Created admin {admin_email}")
        if not user.email_verified_at:
            users.mark_email_verified(user)
        roles.add_user_roles(user.id, [roles.get_role_by_name("admin").id])
        print(f"{admin_email} is admin")
    finally:
        db.close()

if __name__ == "__main__":
    seed()
