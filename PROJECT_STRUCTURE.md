# Certify Studio Project Structure

## Overview
Certify Studio is an AI-powered certification content generation platform that automatically creates enterprise-grade training materials from exam guides using advanced AI agents and professional animation frameworks.

## Project Structure

```
certify-studio/
├── src/certify_studio/          # Main application source code
│   ├── __init__.py             # Package initialization
│   ├── main.py                 # FastAPI application entry point
│   ├── config.py               # Configuration management
│   │
│   ├── api/                    # API layer
│   │   ├── main.py            # API router configuration
│   │   ├── middleware.py       # Custom middleware
│   │   └── v1/                # API version 1
│   │       └── endpoints/     # API endpoints
│   │
│   ├── core/                   # Core business logic
│   │   ├── domain/            # Domain models
│   │   ├── services/          # Business services
│   │   └── repositories/      # Data repositories
│   │
│   ├── agents/                 # AI Agents
│   │   ├── orchestrator.py    # Agent orchestration
│   │   ├── certification/     # Certification-specific agents
│   │   ├── content/           # Content generation agents
│   │   ├── quality/           # Quality control agents
│   │   └── bedrock/           # AWS Bedrock integration
│   │
│   ├── manim_extensions/       # Enhanced Manim framework
│   │   ├── __init__.py        # Package exports
│   │   ├── constants.py       # Certification constants
│   │   ├── scenes/            # Scene classes
│   │   │   └── certification_scene.py
│   │   ├── icons/             # Icon management
│   │   │   └── icon_library.py
│   │   ├── animations/        # Animation patterns
│   │   │   └── aws_animations.py
│   │   ├── themes/            # Visual themes
│   │   │   └── base_theme.py
│   │   ├── interactive/       # Interactive elements
│   │   ├── accessibility/     # Accessibility features
│   │   └── exports/           # Export handlers
│   │
│   ├── diagrams/              # Diagram generation
│   │   ├── providers/         # Cloud provider diagrams
│   │   ├── templates/         # Diagram templates
│   │   └── renderers/         # Rendering engines
│   │
│   ├── database/              # Database layer
│   │   ├── connection.py      # Database management
│   │   ├── models.py          # SQLAlchemy models
│   │   └── migrations/        # Alembic migrations
│   │
│   ├── integrations/          # External integrations
│   │   ├── aws/              # AWS services
│   │   ├── azure/            # Azure services
│   │   ├── gcp/              # Google Cloud services
│   │   ├── storage/          # Storage backends
│   │   └── observability/    # Logging, metrics, tracing
│   │
│   └── utils/                # Utility modules
│
├── frontend/                  # React TypeScript frontend
│   ├── src/
│   │   ├── components/       # React components
│   │   ├── pages/           # Page components
│   │   ├── hooks/           # Custom hooks
│   │   ├── services/        # API services
│   │   └── types/           # TypeScript types
│   └── public/              # Static assets
│
├── docs/                     # Documentation
│   ├── architecture/        # System architecture
│   ├── api/                # API documentation
│   ├── deployment/         # Deployment guides
│   ├── development/        # Development setup
│   └── user-guide/         # User documentation
│
├── tests/                   # Test suites
│   ├── unit/               # Unit tests
│   ├── integration/        # Integration tests
│   ├── performance/        # Performance tests
│   ├── e2e/               # End-to-end tests
│   └── fixtures/          # Test data
│
├── scripts/                # Automation scripts
│   ├── setup/             # Setup scripts
│   │   └── install_dependencies.py
│   ├── deployment/        # Deployment scripts
│   ├── data/              # Data management
│   └── maintenance/       # Maintenance scripts
│
├── config/                 # Configuration files
│   ├── settings/          # Environment configs
│   ├── docker/            # Docker configs
│   ├── kubernetes/        # K8s manifests
│   └── monitoring/        # Monitoring configs
│
├── assets/                # Static assets
│   ├── icons/            # Cloud provider icons
│   ├── templates/        # Content templates
│   ├── fonts/            # Typography
│   └── images/           # Images
│
├── .github/              # GitHub configuration
│   └── workflows/        # CI/CD workflows
│
├── pyproject.toml        # Python project config
├── README.md            # Project documentation
├── LICENSE              # MIT License
├── .gitignore           # Git ignore rules
├── .env.example         # Environment template
├── Dockerfile           # Docker container
├── docker-compose.yml   # Docker services
└── Makefile            # Development commands
```

## Key Components

### 1. Manim Extensions
- **CertificationScene**: Base scene class with provider themes
- **OfficialIconLibrary**: Manages AWS/Azure/GCP/K8s icons
- **AWSArchitectureAnimations**: AWS-specific animations
- **CertificationTheme**: Accessibility-compliant theming

### 2. AI Agent System
- **AgentOrchestrator**: Coordinates multi-agent pipeline
- **Domain Extraction**: Analyzes exam guides
- **Content Generation**: Creates diagrams and animations
- **Quality Control**: Multi-agent consensus validation

### 3. Export Pipeline
- **Video (MP4)**: Manim-rendered animations
- **PowerPoint**: Editable presentations
- **Interactive Web**: React components
- **Blender**: 3D scenes and scripts

## Getting Started

1. **Prerequisites**
   - Python 3.11+
   - Node.js 18+
   - Docker & Docker Compose
   - Poetry
   - FFmpeg
   - Graphviz

2. **Setup**
   ```bash
   cd scripts/setup
   python install_dependencies.py
   ```

3. **Development**
   ```bash
   make dev
   ```

4. **Access**
   - Backend API: http://localhost:8000
   - API Docs: http://localhost:8000/docs
   - Frontend: http://localhost:3000

## Technology Stack

- **Backend**: FastAPI, SQLAlchemy, Celery, Redis
- **AI/ML**: LangChain, AWS Bedrock, OpenAI, Anthropic
- **Animation**: Manim, Python Diagrams, SVG
- **Database**: PostgreSQL, Redis
- **Frontend**: React, TypeScript, Tailwind CSS
- **Cloud**: AWS, Azure, GCP integrations
- **DevOps**: Docker, Kubernetes, GitHub Actions

## Features

- 🎯 Multi-cloud certification support (AWS, Azure, GCP, K8s)
- 🤖 AI-powered content generation from exam guides
- 🎨 Official provider icons and enterprise layouts
- 📹 Multi-format export (Video, PPT, Web, 3D)
- ✅ Quality control with multi-agent consensus
- ♿ WCAG 2.1 AA accessibility compliance
- 🚀 Scalable microservices architecture
- 🔒 Enterprise security and compliance

## Contributing

See [docs/development/contributing.md](docs/development/contributing.md) for guidelines.

## License

MIT License - see [LICENSE](LICENSE) file.
