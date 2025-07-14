"""
Initialize the database with required data.

This script sets up initial roles, permissions, and other necessary data.
"""

import asyncio
import sys
from pathlib import Path

# Add the src directory to the Python path
project_root = Path(__file__).parents[4]
src_path = project_root / "src"
sys.path.insert(0, str(src_path))

from sqlalchemy.ext.asyncio import AsyncSession
from certify_studio.database import get_db_session
from certify_studio.database.models import Role, Permission, User
from certify_studio.database.repositories import RoleRepository, PermissionRepository, UserRepository
from passlib.context import CryptContext

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


async def create_default_roles_and_permissions(db: AsyncSession):
    """Create default roles and permissions."""
    role_repo = RoleRepository(db)
    perm_repo = PermissionRepository(db)
    
    # Define default permissions
    default_permissions = [
        # Content permissions
        ("content", "create", "Create new content"),
        ("content", "read", "View content"),
        ("content", "update", "Update content"),
        ("content", "delete", "Delete content"),
        ("content", "publish", "Publish content"),
        
        # User permissions
        ("users", "create", "Create users"),
        ("users", "read", "View users"),
        ("users", "update", "Update users"),
        ("users", "delete", "Delete users"),
        ("users", "assign_role", "Assign roles to users"),
        
        # Analytics permissions
        ("analytics", "read", "View analytics"),
        ("analytics", "export", "Export analytics data"),
        
        # System permissions
        ("system", "admin", "System administration"),
        ("system", "configure", "Configure system settings"),
    ]
    
    # Create permissions
    permissions = {}
    for resource, action, description in default_permissions:
        perm = await perm_repo.get_or_create(resource, action, description)
        permissions[f"{resource}:{action}"] = perm
    
    # Define default roles with their permissions
    default_roles = {
        "admin": {
            "description": "System administrator with full access",
            "permissions": list(permissions.keys())
        },
        "content_creator": {
            "description": "Can create and manage content",
            "permissions": [
                "content:create", "content:read", "content:update",
                "analytics:read"
            ]
        },
        "reviewer": {
            "description": "Can review and publish content",
            "permissions": [
                "content:read", "content:update", "content:publish",
                "analytics:read"
            ]
        },
        "viewer": {
            "description": "Can only view published content",
            "permissions": ["content:read"]
        }
    }
    
    # Create roles and assign permissions
    for role_name, role_config in default_roles.items():
        role = await role_repo.get_or_create(role_name, role_config["description"])
        
        # Assign permissions to role
        for perm_key in role_config["permissions"]:
            permission = permissions[perm_key]
            await role_repo.add_permission_to_role(role.id, permission.id)
    
    await db.commit()
    print("✓ Created default roles and permissions")


async def create_admin_user(db: AsyncSession):
    """Create default admin user if it doesn't exist."""
    user_repo = UserRepository(db)
    role_repo = RoleRepository(db)
    
    # Check if admin user exists
    admin_email = "admin@certifystudio.com"
    existing_admin = await user_repo.get_by_email(admin_email)
    
    if not existing_admin:
        # Create admin user
        admin_user = await user_repo.create(
            email=admin_email,
            username="admin",
            hashed_password=pwd_context.hash("admin123"),  # Change this!
            full_name="System Administrator",
            is_superuser=True,
            is_active=True,
            email_verified=True
        )
        
        # Assign admin role
        admin_role = await role_repo.get_by_name("admin")
        if admin_role:
            await user_repo.add_role(admin_user.id, admin_role.id)
        
        await db.commit()
        print("✓ Created admin user (email: admin@certifystudio.com, password: admin123)")
        print("  ⚠️  IMPORTANT: Change the admin password immediately!")
    else:
        print("✓ Admin user already exists")


async def main():
    """Initialize the database."""
    print("Initializing Certify Studio database...")
    print()
    
    async with get_db_session() as db:
        try:
            # Create roles and permissions
            await create_default_roles_and_permissions(db.session)
            
            # Create admin user
            await create_admin_user(db.session)
            
            print()
            print("Database initialization complete!")
            
        except Exception as e:
            print(f"Error initializing database: {e}")
            await db.rollback()
            raise


if __name__ == "__main__":
    asyncio.run(main())
