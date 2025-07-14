# Certify Studio

**AI-Powered Certification Content Generation Platform**

Certify Studio is a revolutionary platform that transforms certification exam guides into complete, production-ready educational content through domain abstraction and intelligent automation.

## 🚀 Features

- **Multi-Agent AI System**: Autonomous agents that collaborate to create pedagogically-sound content
- **Cognitive Load Optimization**: Content structured based on cognitive science principles
- **Multimodal Generation**: Create videos, interactive content, quizzes, and more
- **Enterprise-Ready**: Built for scale with proper authentication, monitoring, and deployment
- **Knowledge Graph**: Intelligent concept mapping and prerequisite tracking
- **Quality Assurance**: Automated quality checks and continuous improvement

## 📋 Requirements

- Python 3.11 or higher
- PostgreSQL 15+
- Redis 7+
- Neo4j 5+ (for knowledge graph)
- Qdrant (for vector search)
- Docker (recommended for services)

## 🛠️ Installation

### Quick Start (Windows)

```bash
# 1. Clone and setup
git clone https://github.com/certify-studio/certify-studio.git
cd certify-studio
setup.bat

# 2. Start services
run.bat services

# 3. Initialize database
init_db.bat

# 4. Run the application
run.bat
```

### Quick Start (Linux/Mac)

```bash
# 1. Clone and setup
git clone https://github.com/certify-studio/certify-studio.git
cd certify-studio
./scripts/setup.sh

# 2. Start services
./scripts/run.sh services

# 3. Initialize database
./scripts/init_db.sh

# 4. Run the application
./scripts/run.sh
```

For detailed installation instructions, see [docs/getting-started.md](docs/getting-started.md)

## 🏃 Running the Application

```bash
# Start development server
run.bat

# Run tests
test.bat

# Start all services with Docker
run.bat docker
```

The API will be available at `http://localhost:8000`
API documentation at `http://localhost:8000/docs`

## 🧪 Testing

```bash
# Run unit tests
test.bat

# Run all tests
test.bat all

# Run with coverage
test.bat coverage

# Run specific test
test.bat specific tests/unit/test_basic.py
```

## 📚 Documentation

- [Architecture Overview](docs/architecture.md)
- [API Reference](docs/api.md)
- [Agent Development Guide](docs/agents.md)
- [Deployment Guide](docs/deployment.md)
- [Contributing Guide](CONTRIBUTING.md)

## 🏗️ Project Structure

```
certify-studio/
├── src/
│   └── certify_studio/
│       ├── agents/          # Autonomous AI agents
│       ├── api/             # FastAPI application
│       ├── core/            # Core utilities
│       ├── database/        # Database models and repositories
│       ├── integration/     # Service integration layer
│       ├── knowledge/       # Knowledge graph system
│       └── manim_integration/  # Animation generation
├── tests/                   # Test suites
├── scripts/                 # Utility scripts
├── deployments/            # Docker and Kubernetes configs
├── docs/                   # Documentation
├── setup.bat              # Quick setup (Windows)
├── run.bat                # Run services (Windows)
├── test.bat               # Run tests (Windows)
└── init_db.bat            # Initialize database (Windows)
```

## 🤝 Contributing

We welcome contributions! Please see our [Contributing Guide](CONTRIBUTING.md) for details.

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- Built with FastAPI, SQLAlchemy, and Celery
- Powered by OpenAI and Anthropic AI models
- Animation engine based on Manim
- Inspired by cognitive science and learning theory research

## 📞 Support

- Documentation: [https://docs.certifystudio.com](https://docs.certifystudio.com)
- Issues: [GitHub Issues](https://github.com/certify-studio/certify-studio/issues)
- Discord: [Join our community](https://discord.gg/certifystudio)
- Email: support@certifystudio.com
