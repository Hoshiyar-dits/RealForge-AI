from app.seeders.admin_seeder import seed as seed_admin

# Runs every seeder. The admin seeder seeds roles first.
# Run: python -m app.seeders

if __name__ == "__main__":
    seed_admin()
