"""
Quick PostgreSQL connection test for Certify Studio
"""

import psycopg2
from psycopg2 import sql
import os
from pathlib import Path

def test_connection():
    """Test PostgreSQL connection and display basic info"""
    
    # Try to load connection info from .env.postgresql
    env_file = Path(__file__).parent.parent.parent / '.env.postgresql'
    
    if env_file.exists():
        print(f"Loading configuration from {env_file}")
        config = {}
        with open(env_file, 'r') as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith('#') and '=' in line:
                    key, value = line.split('=', 1)
                    config[key.strip()] = value.strip().strip('"').strip("'")
        
        host = config.get('DATABASE_HOST', 'localhost')
        port = config.get('DATABASE_PORT', '5432')
        user = config.get('DATABASE_USER', 'postgres')
        password = config.get('DATABASE_PASSWORD', '')
        dbname = config.get('DATABASE_NAME', 'Certify Studio Local')
    else:
        # Default values
        host = 'localhost'
        port = '5432'
        user = 'postgres'
        password = input("Enter PostgreSQL password: ")
        dbname = 'Certify Studio Local'
    
    try:
        # Connect to PostgreSQL
        print(f"\nConnecting to PostgreSQL at {host}:{port}...")
        conn = psycopg2.connect(
            host=host,
            port=port,
            user=user,
            password=password,
            database=dbname
        )
        cursor = conn.cursor()
        
        print("✓ Successfully connected to PostgreSQL!")
        print(f"✓ Database: {dbname}")
        
        # Get PostgreSQL version
        cursor.execute("SELECT version();")
        version = cursor.fetchone()[0]
        print(f"✓ PostgreSQL Version: {version.split(',')[0]}")
        
        # Check if our schema exists
        cursor.execute("""
            SELECT COUNT(*) 
            FROM information_schema.schemata 
            WHERE schema_name = 'certify_studio'
        """)
        schema_exists = cursor.fetchone()[0] > 0
        
        if schema_exists:
            print("\n✓ Certify Studio schema is installed")
            
            # Get table counts
            cursor.execute("""
                SELECT 
                    (SELECT COUNT(*) FROM certify_studio.users) as users,
                    (SELECT COUNT(*) FROM certify_studio.agents) as agents,
                    (SELECT COUNT(*) FROM certify_studio.projects) as projects,
                    (SELECT COUNT(*) FROM knowledge_graph.concepts) as concepts
            """)
            counts = cursor.fetchone()
            
            print("\nTable Statistics:")
            print(f"  - Users: {counts[0]}")
            print(f"  - Agents: {counts[1]}")
            print(f"  - Projects: {counts[2]}")
            print(f"  - Concepts: {counts[3]}")
            
            # Show agents
            cursor.execute("""
                SELECT name, agent_type, status 
                FROM certify_studio.agents 
                ORDER BY name
            """)
            agents = cursor.fetchall()
            
            if agents:
                print("\nRegistered Agents:")
                for name, agent_type, status in agents:
                    print(f"  - {name} ({agent_type}): {status}")
        else:
            print("\n⚠ Certify Studio schema not found!")
            print("Run setup_postgresql.bat to create the schema")
        
        cursor.close()
        conn.close()
        
        print("\n✓ Connection test completed successfully!")
        return True
        
    except psycopg2.OperationalError as e:
        print(f"\n✗ Connection failed: {e}")
        print("\nTroubleshooting:")
        print("1. Ensure PostgreSQL is running")
        print("2. Check your connection parameters")
        print("3. Verify the database exists")
        print("4. Check pg_hba.conf for authentication settings")
        return False
        
    except Exception as e:
        print(f"\n✗ Unexpected error: {e}")
        return False


if __name__ == "__main__":
    print("PostgreSQL Connection Test for Certify Studio")
    print("=" * 50)
    
    success = test_connection()
    
    if success:
        print("\n✓ Your PostgreSQL database is ready to use!")
        print("\nNext steps:")
        print("1. Update your .env file with the DATABASE_URL")
        print("2. Restart the backend server")
        print("3. Run the test suite")
    else:
        print("\n✗ Please fix the connection issues and try again")
        print("\nTo set up the database, run:")
        print("  cd scripts/database")
        print("  setup_postgresql.bat")
