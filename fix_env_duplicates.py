"""
Fix duplicate DATABASE_URL entries in .env file
"""

from pathlib import Path

def fix_env_file():
    env_file = Path(".env")
    
    # Read all lines
    with open(env_file, 'r') as f:
        lines = f.readlines()
    
    # Remove duplicate DATABASE_URL entries
    new_lines = []
    database_url_found = False
    
    for line in lines:
        if line.strip().startswith('DATABASE_URL='):
            if not database_url_found:
                # Keep only the asyncpg version (the second one)
                if 'postgresql+asyncpg' in line:
                    new_lines.append(line)
                    database_url_found = True
                else:
                    # Skip the first one
                    continue
            else:
                # Skip any additional DATABASE_URL entries
                continue
        else:
            new_lines.append(line)
    
    # Write back
    with open(env_file, 'w') as f:
        f.writelines(new_lines)
    
    print("✓ Fixed duplicate DATABASE_URL entries in .env file")
    
    # Show the current DATABASE_URL
    with open(env_file, 'r') as f:
        for line in f:
            if line.strip().startswith('DATABASE_URL='):
                print(f"Current DATABASE_URL: {line.strip()}")

if __name__ == "__main__":
    fix_env_file()
