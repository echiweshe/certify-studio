"""
PostgreSQL Setup Script for Certify Studio
Automates database creation and configuration
"""

import os
import sys
import subprocess
import psycopg2
from psycopg2 import sql
import json
from pathlib import Path
from datetime import datetime
import getpass

class PostgreSQLSetup:
    """Setup PostgreSQL for Certify Studio"""
    
    def __init__(self):
        self.db_name = "Certify Studio Local"
        self.scripts_dir = Path(__file__).parent
        self.project_root = self.scripts_dir.parent.parent
        
    def get_connection_params(self):
        """Get PostgreSQL connection parameters"""
        print("PostgreSQL Connection Setup")
        print("=" * 50)
        
        # Try to load from .env.postgresql if it exists
        env_file = self.project_root / '.env.postgresql'
        if env_file.exists():
            print(f"Loading configuration from {env_file}")
            params = self.load_env_file(env_file)
            if params:
                return params
        
        # Otherwise, prompt for parameters
        params = {
            'host': input("Host [localhost]: ").strip() or 'localhost',
            'port': input("Port [5432]: ").strip() or '5432',
            'user': input("Username [postgres]: ").strip() or 'postgres',
            'password': getpass.getpass("Password: ")
        }
        
        # Save for future use
        save_config = input("\nSave configuration? (y/n): ").lower() == 'y'
        if save_config:
            self.save_env_file(env_file, params)
            
        return params
    
    def load_env_file(self, filepath):
        """Load parameters from .env file"""
        params = {}
        try:
            with open(filepath, 'r') as f:
                for line in f:
                    line = line.strip()
                    if line and not line.startswith('#') and '=' in line:
                        key, value = line.split('=', 1)
                        key = key.strip()
                        value = value.strip().strip('"').strip("'")
                        
                        if key == 'DATABASE_HOST':
                            params['host'] = value
                        elif key == 'DATABASE_PORT':
                            params['port'] = value
                        elif key == 'DATABASE_USER':
                            params['user'] = value
                        elif key == 'DATABASE_PASSWORD':
                            params['password'] = value
            
            # Check if we have all required params
            if all(k in params for k in ['host', 'port', 'user', 'password']):
                return params
        except Exception as e:
            print(f"Error loading env file: {e}")
        
        return None
    
    def save_env_file(self, filepath, params):
        """Save parameters to .env file"""
        try:
            with open(filepath, 'w') as f:
                f.write("# PostgreSQL Configuration for Certify Studio\n")
                f.write(f"DATABASE_HOST={params['host']}\n")
                f.write(f"DATABASE_PORT={params['port']}\n")
                f.write(f"DATABASE_USER={params['user']}\n")
                f.write(f"DATABASE_PASSWORD={params['password']}\n")
                f.write(f'DATABASE_NAME="{self.db_name}"\n')
                f.write(f'DATABASE_URL="postgresql://{params["user"]}:{params["password"]}@{params["host"]}:{params["port"]}/{self.db_name}"\n')
            print(f"✓ Configuration saved to {filepath}")
        except Exception as e:
            print(f"Error saving configuration: {e}")
    
    def test_connection(self, params):
        """Test PostgreSQL connection"""
        try:
            conn = psycopg2.connect(
                host=params['host'],
                port=params['port'],
                user=params['user'],
                password=params['password'],
                database='postgres'  # Connect to default database first
            )
            conn.close()
            print("✓ Successfully connected to PostgreSQL")
            return True
        except Exception as e:
            print(f"✗ Connection failed: {e}")
            return False
    
    def create_database(self, params):
        """Create the Certify Studio database if it doesn't exist"""
        try:
            # Connect to default database
            conn = psycopg2.connect(
                host=params['host'],
                port=params['port'],
                user=params['user'],
                password=params['password'],
                database='postgres'
            )
            conn.autocommit = True
            cursor = conn.cursor()
            
            # Check if database exists
            cursor.execute(
                "SELECT 1 FROM pg_database WHERE datname = %s",
                (self.db_name,)
            )
            
            if cursor.fetchone():
                print(f"✓ Database '{self.db_name}' already exists")
            else:
                # Create database
                cursor.execute(
                    sql.SQL("CREATE DATABASE {} WITH ENCODING 'UTF8'").format(
                        sql.Identifier(self.db_name)
                    )
                )
                print(f"✓ Created database '{self.db_name}'")
            
            cursor.close()
            conn.close()
            return True
            
        except Exception as e:
            print(f"✗ Error creating database: {e}")
            return False
    
    def run_sql_script(self, params, script_path):
        """Run SQL script using psql"""
        try:
            # Build psql command
            env = os.environ.copy()
            env['PGPASSWORD'] = params['password']
            
            cmd = [
                'psql',
                '-h', params['host'],
                '-p', params['port'],
                '-U', params['user'],
                '-d', f'"{self.db_name}"',
                '-f', str(script_path),
                '-v', 'ON_ERROR_STOP=1'
            ]
            
            print(f"\nRunning {script_path.name}...")
            
            # Run the command
            result = subprocess.run(
                cmd,
                env=env,
                capture_output=True,
                text=True
            )
            
            if result.returncode == 0:
                print(f"✓ Successfully executed {script_path.name}")
                return True
            else:
                print(f"✗ Error executing {script_path.name}:")
                print(result.stderr)
                return False
                
        except FileNotFoundError:
            # If psql is not in PATH, try alternative method
            print("psql not found, using Python connection...")
            return self.run_sql_script_python(params, script_path)
        except Exception as e:
            print(f"✗ Error running script: {e}")
            return False
    
    def run_sql_script_python(self, params, script_path):
        """Run SQL script using Python connection"""
        try:
            # Connect to the database
            conn = psycopg2.connect(
                host=params['host'],
                port=params['port'],
                user=params['user'],
                password=params['password'],
                database=self.db_name
            )
            cursor = conn.cursor()
            
            # Read and execute script
            with open(script_path, 'r') as f:
                sql_content = f.read()
            
            # Remove psql-specific commands
            sql_content = sql_content.replace(r'\c "Certify Studio Local";', '')
            sql_content = sql_content.replace('\\c "Certify Studio Local";', '')
            
            # Execute the script
            cursor.execute(sql_content)
            conn.commit()
            
            print(f"✓ Successfully executed {script_path.name}")
            cursor.close()
            conn.close()
            return True
            
        except Exception as e:
            print(f"✗ Error executing script: {e}")
            if 'conn' in locals():
                conn.rollback()
                conn.close()
            return False
    
    def create_initial_user(self, params):
        """Create an initial admin user"""
        try:
            conn = psycopg2.connect(
                host=params['host'],
                port=params['port'],
                user=params['user'],
                password=params['password'],
                database=self.db_name
            )
            cursor = conn.cursor()
            
            print("\nCreate Initial Admin User")
            print("-" * 30)
            email = input("Admin email: ").strip()
            password = getpass.getpass("Admin password: ")
            
            # Hash password (in production, use proper hashing)
            from hashlib import sha256
            password_hash = sha256(password.encode()).hexdigest()
            
            cursor.execute("""
                INSERT INTO certify_studio.users 
                (email, password_hash, full_name, is_active, is_superuser)
                VALUES (%s, %s, %s, %s, %s)
                ON CONFLICT (email) DO NOTHING
                RETURNING id
            """, (email, password_hash, 'Admin User', True, True))
            
            result = cursor.fetchone()
            if result:
                print(f"✓ Created admin user: {email}")
            else:
                print(f"✓ Admin user already exists: {email}")
            
            conn.commit()
            cursor.close()
            conn.close()
            return True
            
        except Exception as e:
            print(f"✗ Error creating admin user: {e}")
            return False
    
    def update_app_config(self, params):
        """Update application configuration"""
        try:
            # Update main .env file
            env_file = self.project_root / '.env'
            env_content = []
            
            if env_file.exists():
                with open(env_file, 'r') as f:
                    env_content = f.readlines()
            
            # Update or add database URL
            db_url = f'postgresql://{params["user"]}:{params["password"]}@{params["host"]}:{params["port"]}/{self.db_name}'
            db_url_line = f'DATABASE_URL="{db_url}"\n'
            
            # Check if DATABASE_URL exists
            updated = False
            for i, line in enumerate(env_content):
                if line.strip().startswith('DATABASE_URL='):
                    env_content[i] = db_url_line
                    updated = True
                    break
            
            if not updated:
                env_content.append(db_url_line)
            
            # Write back
            with open(env_file, 'w') as f:
                f.writelines(env_content)
            
            print(f"✓ Updated {env_file}")
            
            # Also update config.py if needed
            config_file = self.project_root / 'src' / 'certify_studio' / 'config.py'
            if config_file.exists():
                print(f"✓ Configuration files updated")
                print(f"  DATABASE_URL: {db_url}")
            
            return True
            
        except Exception as e:
            print(f"✗ Error updating configuration: {e}")
            return False
    
    def run_setup(self):
        """Run the complete setup process"""
        print("\nCertify Studio PostgreSQL Setup")
        print("=" * 50)
        
        # Get connection parameters
        params = self.get_connection_params()
        
        # Test connection
        print("\nTesting PostgreSQL connection...")
        if not self.test_connection(params):
            return False
        
        # Create database
        print("\nSetting up database...")
        if not self.create_database(params):
            return False
        
        # Run SQL scripts
        sql_scripts = sorted(self.scripts_dir.glob('*.sql'))
        for script in sql_scripts:
            if not self.run_sql_script(params, script):
                print("\nSetup failed. Please check the errors above.")
                return False
        
        # Create initial user
        create_user = input("\nCreate initial admin user? (y/n): ").lower() == 'y'
        if create_user:
            self.create_initial_user(params)
        
        # Update application configuration
        print("\nUpdating application configuration...")
        self.update_app_config(params)
        
        print("\n" + "=" * 50)
        print("✓ PostgreSQL setup completed successfully!")
        print(f"✓ Database: {self.db_name}")
        print(f"✓ Connection: postgresql://{params['user']}@{params['host']}:{params['port']}/{self.db_name}")
        print("\nNext steps:")
        print("1. Restart the backend: uv run uvicorn certify_studio.main:app --reload")
        print("2. Run tests: test_aws_workflow.bat")
        
        return True


def main():
    """Main entry point"""
    setup = PostgreSQLSetup()
    success = setup.run_setup()
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
