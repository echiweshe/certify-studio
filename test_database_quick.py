"""
Quick Database Verification Test
================================
"""

import asyncio
import aiohttp
import json

async def test_database_integration():
    """Test database is properly integrated"""
    base_url = "http://localhost:8000"
    
    async with aiohttp.ClientSession() as session:
        # 1. Check health
        print("1️⃣ Checking server health...")
        async with session.get(f"{base_url}/health") as resp:
            data = await resp.json()
            db_status = data["services"]["database"]
            print(f"   Database status: {db_status}")
            assert db_status == "healthy", "Database not healthy!"
        
        # 2. Test registration
        print("\n2️⃣ Testing user registration...")
        user_data = {
            "email": "db-test@certify-studio.com",
            "password": "DBTest123!",
            "full_name": "Database Test User"
        }
        
        async with session.post(f"{base_url}/api/v1/auth/register", json=user_data) as resp:
            if resp.status in [200, 201]:
                print("   ✅ User registration successful!")
            elif resp.status == 400:
                print("   ℹ️ User already exists (that's ok)")
            else:
                print(f"   ❌ Registration failed: {resp.status}")
        
        # 3. Test login
        print("\n3️⃣ Testing user login...")
        login_data = {
            "username": user_data["email"],
            "password": user_data["password"]
        }
        
        async with session.post(f"{base_url}/api/v1/auth/login", data=login_data) as resp:
            if resp.status == 200:
                data = await resp.json()
                print(f"   ✅ Login successful! Token type: {data['token_type']}")
                return True
            else:
                print(f"   ❌ Login failed: {resp.status}")
                return False
    
    print("\n✅ Database integration test complete!")
    return True

if __name__ == "__main__":
    success = asyncio.run(test_database_integration())
    if success:
        print("\n🎉 Database is fully operational! Ready to run the full test suite.")
    else:
        print("\n❌ Database issues detected. Please check the configuration.")
