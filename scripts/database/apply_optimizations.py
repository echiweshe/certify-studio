"""
Apply performance optimizations to existing database
"""

import psycopg2
from pathlib import Path
import os

def apply_optimizations():
    # Load connection from .env.postgresql
    env_file = Path(__file__).parent.parent.parent / '.env.postgresql'
    config = {}
    
    if env_file.exists():
        with open(env_file, 'r') as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith('#') and '=' in line:
                    key, value = line.split('=', 1)
                    config[key.strip()] = value.strip().strip('"').strip("'")
    
    try:
        # Connect to database
        conn = psycopg2.connect(
            host=config.get('DATABASE_HOST', 'localhost'),
            port=config.get('DATABASE_PORT', '5432'),
            user=config.get('DATABASE_USER', 'postgres'),
            password=config.get('DATABASE_PASSWORD', ''),
            database=config.get('DATABASE_NAME', 'Certify Studio Local')
        )
        
        print("Connected to database...")
        
        # Read optimization script
        script_path = Path(__file__).parent / '03_optimize_performance.sql'
        with open(script_path, 'r') as f:
            sql_content = f.read()
        
        # Execute
        cursor = conn.cursor()
        cursor.execute(sql_content)
        conn.commit()
        
        print("✓ Performance optimizations applied successfully!")
        
        cursor.close()
        conn.close()
        
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    apply_optimizations()
