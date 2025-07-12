# Certify Studio Quick Start Guide

## 🚀 Quick Setup (5 minutes)

### Prerequisites Check
```bash
# Check Python version (need 3.11+)
python --version

# Check Node.js version (need 18+)
node --version

# Check Docker is running
docker --version

# Install Poetry if not present
pip install poetry
```

### 1. Clone and Setup
```bash
# Clone the repository
git clone https://github.com/your-org/certify-studio.git
cd certify-studio

# Run automated setup
cd scripts/setup
python install_dependencies.py
```

### 2. Configure Environment
```bash
# Copy the generated secrets to .env
cp secrets.txt .env

# Edit .env with your API keys
nano .env
```

Required API keys (at least one):
- `OPENAI_API_KEY` - For OpenAI GPT models
- `ANTHROPIC_API_KEY` - For Claude models
- `AWS_ACCESS_KEY_ID` & `AWS_SECRET_ACCESS_KEY` - For AWS Bedrock

### 3. Start Development Environment
```bash
# From project root
make dev
```

This will:
- Start PostgreSQL and Redis containers
- Run database migrations
- Start the FastAPI backend
- Start the React frontend (if available)

### 4. Access the Application

- **Backend API**: http://localhost:8000
- **API Documentation**: http://localhost:8000/docs
- **Frontend**: http://localhost:3000
- **Flower (Celery monitoring)**: http://localhost:5555

## 🎯 First Content Generation

### 1. Upload Exam Guide
```bash
# Using API directly
curl -X POST "http://localhost:8000/api/v1/certifications/upload" \
  -H "accept: application/json" \
  -H "Content-Type: multipart/form-data" \
  -F "file=@aws-saa-c03-exam-guide.pdf"
```

### 2. Generate Content
```bash
# Start content generation
curl -X POST "http://localhost:8000/api/v1/content/generate" \
  -H "accept: application/json" \
  -H "Content-Type: application/json" \
  -d '{
    "certification_type": "AWS SAA-C03",
    "exam_guide_id": "guide_123",
    "options": {
      "export_formats": ["mp4", "pptx"],
      "voice_style": "professional",
      "learning_level": "associate"
    }
  }'
```

### 3. Monitor Progress
```bash
# Check generation status
curl "http://localhost:8000/api/v1/content/status/{generation_id}"
```

### 4. Download Results
Once complete, download your generated content:
- Video tutorials (MP4)
- PowerPoint presentations
- Interactive web modules
- Blender 3D scenes

## 📚 Sample Workflow

### Creating AWS VPC Animation
```python
from certify_studio.manim_extensions import CertificationScene, AWSArchitectureAnimations

class AWSVPCDemo(CertificationScene):
    def __init__(self):
        super().__init__(
            provider=CertificationProvider.AWS,
            certification="SAA-C03",
            domain="Design Resilient Architectures",
            concept="VPC and Subnets"
        )
    
    def construct(self):
        # Create VPC configuration
        vpc_config = {
            "cidr": "10.0.0.0/16",
            "availability_zones": ["us-east-1a", "us-east-1b"],
            "subnets": [
                {"name": "Public", "cidr": "10.0.1.0/24", "type": "public"},
                {"name": "Private", "cidr": "10.0.2.0/24", "type": "private"}
            ]
        }
        
        # Animate VPC creation
        vpc_animation = AWSArchitectureAnimations.create_vpc_formation(
            vpc_config, 
            scene=self
        )
        self.play(vpc_animation)
```

## 🛠️ Common Commands

```bash
# Run tests
make test

# Format code
make format

# Check code quality
make lint

# Build Docker images
make docker-build

# View logs
docker-compose logs -f backend

# Access database
docker-compose exec postgres psql -U certify_user -d certify_studio

# Clear cache
redis-cli FLUSHALL
```

## 🐛 Troubleshooting

### Database Connection Issues
```bash
# Restart database
docker-compose restart postgres

# Check database logs
docker-compose logs postgres
```

### Port Already in Use
```bash
# Find process using port 8000
lsof -i :8000

# Kill the process
kill -9 <PID>
```

### Missing Dependencies
```bash
# Reinstall Python dependencies
poetry install

# Reinstall Node dependencies
cd frontend && npm install
```

## 📖 Next Steps

1. Read the [Architecture Overview](docs/architecture/README.md)
2. Explore [API Documentation](http://localhost:8000/docs)
3. Check out [Example Animations](docs/examples/)
4. Join our [Discord Community](https://discord.gg/certifystudio)

## 💬 Getting Help

- **Documentation**: [docs/](docs/)
- **Issues**: [GitHub Issues](https://github.com/your-org/certify-studio/issues)
- **Email**: support@certifystudio.com
- **Discord**: [Join our server](https://discord.gg/certifystudio)

Happy content generation! 🎉
