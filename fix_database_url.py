"""
Fix DATABASE_URL encoding issue
"""

from pathlib import Path
import urllib.parse

def fix_database_url():
    env_file = Path(".env")
    
    # Read all lines
    with open(env_file, 'r') as f:
        lines = f.readlines()
    
    # Fix DATABASE_URL
    new_lines = []
    for line in lines:
        if line.strip().startswith('DATABASE_URL='):
            # The correct URL with proper encoding
            # Database name should NOT be URL-encoded in the connection string
            database_url = 'DATABASE_URL=postgresql+asyncpg://postgres:Mucharasa%267108%241939@localhost:5432/Certify Studio Local\n'
            new_lines.append(database_url)
            print(f"Fixed DATABASE_URL: {database_url.strip()}")
        else:
            new_lines.append(line)
    
    # Write back
    with open(env_file, 'w') as f:
        f.writelines(new_lines)
    
    print("✓ Fixed DATABASE_URL in .env file")

if __name__ == "__main__":
    fix_database_url()
