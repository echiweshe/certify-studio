"""
Example usage of Certify Studio API.

This script demonstrates how to use the API to:
1. Upload a certification guide
2. Extract domain knowledge
3. Generate educational content
4. Check quality
5. Export the final content
"""

import asyncio
import time
from pathlib import Path
from typing import Dict, Any

import httpx


# API Configuration
API_BASE_URL = "http://localhost:8000"
API_KEY = "your-api-key-here"  # In production, use proper authentication


class CertifyStudioClient:
    """Client for interacting with Certify Studio API."""
    
    def __init__(self, base_url: str = API_BASE_URL):
        self.base_url = base_url
        self.client = httpx.AsyncClient(base_url=base_url, timeout=60.0)
        self.token = None
    
    async def __aenter__(self):
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.client.aclose()
    
    async def login(self, email: str, password: str) -> Dict[str, Any]:
        """Authenticate and get access token."""
        response = await self.client.post(
            "/api/auth/login",
            data={"username": email, "password": password}
        )
        response.raise_for_status()
        
        data = response.json()
        self.token = data["access_token"]
        return data
    
    @property
    def auth_headers(self) -> Dict[str, str]:
        """Get authentication headers."""
        if not self.token:
            raise ValueError("Not authenticated. Call login() first.")
        return {"Authorization": f"Bearer {self.token}"}
    
    async def upload_file(self, file_path: Path) -> Dict[str, Any]:
        """Upload a certification guide."""
        print(f"📤 Uploading {file_path.name}...")
        
        with open(file_path, "rb") as f:
            files = {"file": (file_path.name, f, "application/pdf")}
            response = await self.client.post(
                "/api/generation/upload",
                files=files,
                headers=self.auth_headers
            )
        
        response.raise_for_status()
        return response.json()
    
    async def extract_domain_knowledge(self, upload_id: str, cert_type: str) -> Dict[str, Any]:
        """Extract domain knowledge from uploaded content."""
        print("🔍 Extracting domain knowledge...")
        
        response = await self.client.post(
            "/api/domains/extract",
            json={
                "upload_id": upload_id,
                "certification_type": cert_type,
                "extract_prerequisites": True,
                "extract_learning_paths": True,
                "extract_exam_weights": True
            },
            headers=self.auth_headers
        )
        
        response.raise_for_status()
        return response.json()
    
    async def wait_for_extraction(self, extraction_id: str, max_wait: int = 300) -> Dict[str, Any]:
        """Wait for extraction to complete."""
        start_time = time.time()
        
        while time.time() - start_time < max_wait:
            response = await self.client.get(
                f"/api/domains/extract/{extraction_id}",
                headers=self.auth_headers
            )
            response.raise_for_status()
            
            data = response.json()
            if data["status"] == "completed":
                return data
            elif data["status"] == "failed":
                raise Exception(f"Extraction failed: {data.get('error')}")
            
            print(f"⏳ Extraction in progress... ({int(time.time() - start_time)}s)")
            await asyncio.sleep(5)
        
        raise TimeoutError("Extraction timed out")
    
    async def generate_content(
        self,
        upload_id: str,
        title: str,
        cert_type: str,
        duration_minutes: int = 30,
        output_formats: list = None
    ) -> Dict[str, Any]:
        """Generate educational content."""
        print("🎬 Starting content generation...")
        
        if output_formats is None:
            output_formats = ["video/mp4", "pdf/document"]
        
        response = await self.client.post(
            "/api/generation/generate",
            json={
                "certification_type": cert_type,
                "upload_id": upload_id,
                "title": title,
                "duration_minutes": duration_minutes,
                "output_formats": output_formats,
                "quality_level": "standard",
                "enable_interactivity": True,
                "enable_accessibility": True
            },
            headers=self.auth_headers
        )
        
        response.raise_for_status()
        return response.json()
    
    async def track_generation_progress(self, task_id: str) -> None:
        """Track generation progress via WebSocket."""
        print("📊 Tracking generation progress...")
        
        # For demo, we'll poll the status endpoint
        # In production, use WebSocket for real-time updates
        
        while True:
            response = await self.client.get(
                f"/api/generation/status/{task_id}",
                headers=self.auth_headers
            )
            response.raise_for_status()
            
            data = response.json()
            progress = data.get("progress", 0)
            phase = data.get("current_phase", "unknown")
            status = data.get("generation_status")
            
            print(f"📈 Progress: {progress}% - Phase: {phase}")
            
            if status == "completed":
                print("✅ Generation completed!")
                return data
            elif status == "failed":
                raise Exception(f"Generation failed: {data.get('error')}")
            
            await asyncio.sleep(5)
    
    async def check_quality(self, content_id: str) -> Dict[str, Any]:
        """Run quality checks on generated content."""
        print("🔍 Running quality checks...")
        
        response = await self.client.post(
            "/api/quality/check",
            json={
                "content_id": content_id,
                "check_technical_accuracy": True,
                "check_pedagogical_effectiveness": True,
                "check_accessibility": True,
                "check_certification_alignment": True
            },
            headers=self.auth_headers
        )
        
        response.raise_for_status()
        return response.json()
    
    async def export_content(self, content_id: str, format: str = "video/mp4") -> Dict[str, Any]:
        """Export content in specified format."""
        print(f"📦 Exporting content as {format}...")
        
        response = await self.client.post(
            "/api/export/",
            json={
                "content_id": content_id,
                "export_options": {
                    "format": format,
                    "video_resolution": "1920x1080",
                    "video_fps": 30,
                    "include_captions": True
                }
            },
            headers=self.auth_headers
        )
        
        response.raise_for_status()
        return response.json()
    
    async def download_export(self, export_id: str, output_path: Path) -> None:
        """Download exported content."""
        print(f"⬇️ Downloading to {output_path}...")
        
        response = await self.client.get(
            f"/api/export/{export_id}/download",
            headers=self.auth_headers
        )
        response.raise_for_status()
        
        # Write to file
        with open(output_path, "wb") as f:
            async for chunk in response.aiter_bytes(chunk_size=8192):
                f.write(chunk)
        
        print(f"✅ Downloaded to {output_path}")


async def main():
    """Example workflow using Certify Studio API."""
    
    # Configuration
    email = "demo@example.com"
    password = "demo123"
    cert_guide_path = Path("sample_aws_guide.pdf")
    cert_type = "aws-saa"
    
    async with CertifyStudioClient() as client:
        try:
            # 1. Authenticate
            print("🔐 Authenticating...")
            await client.login(email, password)
            print("✅ Authenticated successfully")
            
            # 2. Upload certification guide
            upload_result = await client.upload_file(cert_guide_path)
            upload_id = upload_result["upload_id"]
            print(f"✅ File uploaded: {upload_id}")
            
            # 3. Extract domain knowledge
            extraction_result = await client.extract_domain_knowledge(upload_id, cert_type)
            extraction_id = extraction_result["extraction_id"]
            
            # Wait for extraction to complete
            extraction_data = await client.wait_for_extraction(extraction_id)
            print(f"✅ Extracted {extraction_data['total_concepts']} concepts")
            print(f"✅ Found {extraction_data['total_relationships']} relationships")
            
            # 4. Generate educational content
            generation_result = await client.generate_content(
                upload_id=upload_id,
                title="AWS Solutions Architect - Complete Course",
                cert_type=cert_type,
                duration_minutes=45,
                output_formats=["video/mp4", "pdf/document", "interactive/html"]
            )
            task_id = generation_result["task_id"]
            
            # Track progress
            final_status = await client.track_generation_progress(task_id)
            
            # 5. Check quality
            # In a real scenario, we'd get content_id from generation result
            # For demo, using a mock ID
            content_id = "mock-content-id"
            quality_result = await client.check_quality(content_id)
            
            print(f"📊 Quality Score: {quality_result.get('overall_quality', 0) * 100:.1f}%")
            
            # 6. Export content
            export_result = await client.export_content(content_id, "video/mp4")
            export_id = export_result["export_id"]
            
            # Wait for export to complete (simplified for demo)
            await asyncio.sleep(5)
            
            # 7. Download final content
            output_path = Path("output") / "aws_course.mp4"
            output_path.parent.mkdir(exist_ok=True)
            await client.download_export(export_id, output_path)
            
            print("\n🎉 Workflow completed successfully!")
            print(f"📹 Your course is ready at: {output_path}")
            
        except Exception as e:
            print(f"\n❌ Error: {e}")
            raise


if __name__ == "__main__":
    print("🚀 Certify Studio API Example")
    print("=" * 50)
    asyncio.run(main())
