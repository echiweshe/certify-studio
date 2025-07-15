"""
Update .env file to use PostgreSQL configuration
"""

import os
from pathlib import Path
import urllib.parse

def update_env_file():
    """Update the main .env file with PostgreSQL configuration"""
    
    # Paths
    project_root = Path(__file__).parent.parent.parent
    env_file = project_root / '.env'
    env_postgresql = project_root / '.env.postgresql'
    
    # Load PostgreSQL config
    pg_config = {}
    if env_postgresql.exists():
        with open(env_postgresql, 'r') as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith('#') and '=' in line:
                    key, value = line.split('=', 1)
                    pg_config[key.strip()] = value.strip().strip('"').strip("'")
    
    # Build correct DATABASE_URL with URL encoding for special characters
    password = urllib.parse.quote(pg_config['DATABASE_PASSWORD'])
    db_name = urllib.parse.quote(pg_config['DATABASE_NAME'])
    database_url = f"postgresql://{pg_config['DATABASE_USER']}:{password}@{pg_config['DATABASE_HOST']}:{pg_config['DATABASE_PORT']}/{db_name}"
    
    # Also create asyncpg version for async operations
    database_url_async = f"postgresql+asyncpg://{pg_config['DATABASE_USER']}:{password}@{pg_config['DATABASE_HOST']}:{pg_config['DATABASE_PORT']}/{db_name}"
    
    # Read current .env file
    env_lines = []
    if env_file.exists():
        with open(env_file, 'r') as f:
            env_lines = f.readlines()
    
    # Update DATABASE_URL
    updated = False
    for i, line in enumerate(env_lines):
        if line.strip().startswith('DATABASE_URL='):
            env_lines[i] = f'DATABASE_URL={database_url_async}\n'
            updated = True
            break
    
    if not updated:
        # Add DATABASE_URL if not found
        env_lines.append(f'\n# PostgreSQL Database\nDATABASE_URL={database_url_async}\n')
    
    # Write back
    with open(env_file, 'w') as f:
        f.writelines(env_lines)
    
    # Also fix the .env.postgresql file
    pg_lines = []
    with open(env_postgresql, 'r') as f:
        pg_lines = f.readlines()
    
    # Fix the DATABASE_URL in .env.postgresql
    for i, line in enumerate(pg_lines):
        if line.strip().startswith('DATABASE_URL='):
            pg_lines[i] = f'DATABASE_URL="{database_url}"\n'
            break
    
    with open(env_postgresql, 'w') as f:
        f.writelines(pg_lines)
    
    print("✓ Updated .env file with PostgreSQL configuration")
    print(f"  DATABASE_URL: {database_url_async}")
    print("\n✓ Fixed .env.postgresql file")
    print("\nNext steps:")
    print("1. Restart the backend server:")
    print("   uv run uvicorn certify_studio.main:app --reload")
    print("2. Test the connection:")
    print("   python test_connection.py")

if __name__ == "__main__":
    update_env_file()
