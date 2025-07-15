"""
Quick Backend Connectivity Test

This script quickly tests if the backend is running and all endpoints are accessible.
"""

import httpx
import asyncio
import json
from datetime import datetime
from colorama import init, Fore, Style

# Initialize colorama
init()


async def test_backend_connectivity():
    """Test all backend endpoints for connectivity"""
    
    print(f"\n{Fore.CYAN}{'='*60}{Style.RESET_ALL}")
    print(f"{Fore.CYAN}CERTIFY STUDIO - BACKEND CONNECTIVITY TEST{Style.RESET_ALL}".center(60))
    print(f"{Fore.CYAN}{'='*60}{Style.RESET_ALL}\n")
    
    base_url = "http://localhost:8000"
    
    # Endpoints to test
    endpoints = [
        ("/", "GET", "Root endpoint"),
        ("/health", "GET", "Health check"),
        ("/api/v1/info", "GET", "API information"),
        ("/docs", "GET", "API documentation"),
        ("/redoc", "GET", "ReDoc documentation"),
    ]
    
    results = []
    
    async with httpx.AsyncClient(base_url=base_url, timeout=10.0) as client:
        for endpoint, method, description in endpoints:
            try:
                print(f"{Fore.BLUE}Testing {method} {endpoint}{Style.RESET_ALL} - {description}...", end="")
                
                if method == "GET":
                    response = await client.get(endpoint)
                
                if response.status_code == 200:
                    print(f" {Fore.GREEN}✓ OK{Style.RESET_ALL}")
                    
                    # Try to parse JSON response
                    try:
                        data = response.json()
                        if endpoint == "/health":
                            print(f"  └─ Status: {data.get('status', 'unknown')}")
                            print(f"  └─ Database: {data.get('services', {}).get('database', 'unknown')}")
                            print(f"  └─ AI Agents: {data.get('services', {}).get('ai_agents', 'unknown')}")
                        elif endpoint == "/api/v1/info":
                            print(f"  └─ Version: {data.get('version', 'unknown')}")
                            print(f"  └─ Agents: {len(data.get('agents', []))}")
                    except:
                        pass
                    
                    results.append((endpoint, True, response.status_code))
                else:
                    print(f" {Fore.RED}✗ Failed (Status: {response.status_code}){Style.RESET_ALL}")
                    results.append((endpoint, False, response.status_code))
                    
            except httpx.ConnectError:
                print(f" {Fore.RED}✗ Connection refused{Style.RESET_ALL}")
                results.append((endpoint, False, "Connection refused"))
            except httpx.TimeoutException:
                print(f" {Fore.RED}✗ Timeout{Style.RESET_ALL}")
                results.append((endpoint, False, "Timeout"))
            except Exception as e:
                print(f" {Fore.RED}✗ Error: {str(e)}{Style.RESET_ALL}")
                results.append((endpoint, False, str(e)))
    
    # Summary
    print(f"\n{Fore.CYAN}{'='*60}{Style.RESET_ALL}")
    print(f"{Fore.CYAN}SUMMARY{Style.RESET_ALL}")
    print(f"{Fore.CYAN}{'='*60}{Style.RESET_ALL}")
    
    successful = sum(1 for _, success, _ in results if success)
    total = len(results)
    
    print(f"Total endpoints tested: {total}")
    print(f"Successful: {Fore.GREEN}{successful}{Style.RESET_ALL}")
    print(f"Failed: {Fore.RED}{total - successful}{Style.RESET_ALL}")
    
    if successful == total:
        print(f"\n{Fore.GREEN}✅ All endpoints are accessible!{Style.RESET_ALL}")
        print(f"{Fore.GREEN}The backend is fully operational.{Style.RESET_ALL}")
        return True
    else:
        print(f"\n{Fore.RED}❌ Some endpoints are not accessible.{Style.RESET_ALL}")
        if any("Connection refused" in str(status) for _, _, status in results):
            print(f"{Fore.YELLOW}⚠️  The backend server might not be running.{Style.RESET_ALL}")
            print(f"{Fore.YELLOW}   Run: uv run uvicorn certify_studio.main:app --reload{Style.RESET_ALL}")
        return False


async def test_api_functionality():
    """Test basic API functionality"""
    
    print(f"\n{Fore.CYAN}{'='*60}{Style.RESET_ALL}")
    print(f"{Fore.CYAN}API FUNCTIONALITY TEST{Style.RESET_ALL}")
    print(f"{Fore.CYAN}{'='*60}{Style.RESET_ALL}\n")
    
    base_url = "http://localhost:8000"
    
    async with httpx.AsyncClient(base_url=base_url, timeout=10.0) as client:
        # Test authentication
        print(f"{Fore.BLUE}Testing authentication...{Style.RESET_ALL}")
        
        # Try to register a test user
        test_user = {
            "email": f"test_{datetime.now().timestamp()}@example.com",
            "password": "TestPassword123!",
            "full_name": "Test User"
        }
        
        try:
            response = await client.post("/api/v1/auth/register", json=test_user)
            if response.status_code in [200, 201]:
                print(f"  {Fore.GREEN}✓ User registration works{Style.RESET_ALL}")
                token = response.json().get("access_token")
                
                if token:
                    # Test authenticated endpoint
                    headers = {"Authorization": f"Bearer {token}"}
                    me_response = await client.get("/api/v1/auth/me", headers=headers)
                    
                    if me_response.status_code == 200:
                        print(f"  {Fore.GREEN}✓ Authentication works{Style.RESET_ALL}")
                        user_data = me_response.json()
                        print(f"    └─ User: {user_data.get('email', 'unknown')}")
            elif response.status_code == 409:
                print(f"  {Fore.YELLOW}⚠ User already exists (this is OK){Style.RESET_ALL}")
            else:
                print(f"  {Fore.RED}✗ Registration failed: {response.status_code}{Style.RESET_ALL}")
        except Exception as e:
            print(f"  {Fore.RED}✗ Authentication test failed: {str(e)}{Style.RESET_ALL}")


async def main():
    """Run all connectivity tests"""
    
    # Test basic connectivity
    backend_ok = await test_backend_connectivity()
    
    if backend_ok:
        # Test API functionality
        await test_api_functionality()
        
        print(f"\n{Fore.GREEN}{'='*60}{Style.RESET_ALL}")
        print(f"{Fore.GREEN}✅ BACKEND IS READY FOR TESTING!{Style.RESET_ALL}".center(60))
        print(f"{Fore.GREEN}{'='*60}{Style.RESET_ALL}\n")
    else:
        print(f"\n{Fore.RED}{'='*60}{Style.RESET_ALL}")
        print(f"{Fore.RED}❌ BACKEND NEEDS TO BE STARTED{Style.RESET_ALL}".center(60))
        print(f"{Fore.RED}{'='*60}{Style.RESET_ALL}\n")


if __name__ == "__main__":
    asyncio.run(main())
