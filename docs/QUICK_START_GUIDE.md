# CERTIFY STUDIO QUICK START GUIDE
## Your AI Agent Operating System is Ready!

### Starting the System

#### 1. Start the Backend
```bash
cd C:\ZBDuo_Share\Labs\src\BttlnsCldMCP\certify-studio-github-pull
start_server_fixed.bat
```
Or manually:
```bash
set PYTHONPATH=C:\ZBDuo_Share\Labs\src\BttlnsCldMCP\certify-studio-github-pull\src
python -m certify_studio.main
```

#### 2. Access the Frontend
Open your browser to: `http://localhost:3000`

### Login Credentials
- **Username**: `admin@certifystudio.com`
- **Password**: `admin123`

### Your First Generation

#### Step 1: Upload a PDF
1. Click "New Generation" or the upload button
2. Select a certification guide PDF (AWS, Azure, etc.)
3. Wait for upload confirmation

#### Step 2: Configure Generation
- **Target Audience**: Beginner, Intermediate, or Advanced
- **Duration**: 3-30 minutes
- **Output Formats**: 
  - MP4 (animated video)
  - Interactive HTML5
  - SCORM package
  - PDF document
  - PowerPoint
- **Enable Interactivity**: Toggle for interactive elements
- **Accessibility**: Select required features

#### Step 3: Start Generation
1. Click "Generate"
2. Watch real-time progress via WebSocket updates
3. See each agent's contribution:
   - Domain Extraction Agent parsing your PDF
   - Pedagogical Reasoning Agent optimizing learning
   - Animation Choreography Agent planning scenes
   - Diagram Generation Agent creating visuals
   - Quality Assurance Agent validating everything

#### Step 4: Download Results
Once complete, download your generated content in all selected formats!

### Understanding the Dashboard

#### Agent Status Cards
Each agent shows:
- **Current Status**: idle, thinking, planning, executing
- **Current Task**: What they're working on
- **Capabilities**: Skills and proficiency levels
- **Performance**: Success rate and processing time

#### Real-time Updates
- WebSocket connection provides live status
- Progress bars for ongoing tasks
- Notification when generation completes

### System Capabilities

#### Content Types Supported
- Technical certification guides
- Educational textbooks
- Training materials
- API documentation
- Process documentation

#### Output Quality Features
- Cognitive load optimization
- Progressive complexity disclosure
- Accessibility compliance
- Multi-language support
- Interactive assessments

### Advanced Features

#### Knowledge Graph Visualization
- See extracted concepts and relationships
- Explore learning paths
- Understand prerequisite chains

#### Agent Collaboration Monitoring
- Watch agents negotiate and collaborate
- See message passing in real-time
- Understand decision-making process

#### Quality Metrics
- Technical accuracy scores
- Pedagogical effectiveness ratings
- Accessibility compliance levels
- Engagement predictions

### Troubleshooting

#### Backend Won't Start
```bash
# Check Python path
python --version  # Should be 3.12+

# Install dependencies
pip install -e .

# Check PostgreSQL
psql -U certify_user -d certify_studio
```

#### Frontend Connection Issues
```bash
# Check if backend is running
curl http://localhost:8000/health

# Restart frontend
cd frontend
npm install
npm run dev
```

#### Agent Errors
- Check logs in console
- Verify PDF is valid
- Ensure enough memory (8GB+ recommended)

### Configuration Options

#### Environment Variables (.env)
- `DATABASE_URL`: PostgreSQL connection
- `JWT_SECRET_KEY`: Authentication key
- `CORS_ORIGINS`: Allowed frontend URLs
- `ENABLE_METRICS`: Performance tracking

#### Agent Settings
- `AGENT_POOL_SIZE`: Concurrent agents
- `MAX_CONCURRENT_GENERATIONS`: Parallel jobs
- `COGNITIVE_LOAD_THRESHOLD`: Complexity limits
- `QUALITY_THRESHOLD`: Minimum quality scores

### Best Practices

#### For Optimal Results
1. Use high-quality PDF sources
2. Choose appropriate target audience
3. Allow sufficient generation time
4. Review quality metrics before distribution

#### For Performance
1. Limit concurrent generations
2. Monitor system resources
3. Clear old exports periodically
4. Restart agents if stuck

### API Access

#### Authentication
```bash
POST /api/v1/auth/login
{
  "username": "admin@certifystudio.com",
  "password": "admin123"
}
```

#### Start Generation
```bash
POST /api/v1/generation/generate
Authorization: Bearer <token>
{
  "title": "Azure Fundamentals",
  "certification_type": "AZURE",
  "file_id": "uploaded-file-id",
  "target_audience": "beginners",
  "duration_minutes": 10,
  "output_formats": ["MP4", "INTERACTIVE_HTML"]
}
```

#### Check Status
```bash
GET /api/v1/generation/status/{task_id}
Authorization: Bearer <token>
```

### Getting Help

#### Documentation
- Architecture: `/docs/IMMUTABLE_VISION/`
- API Docs: `http://localhost:8000/docs`
- Recovery Story: `/docs/RECOVERY_SUCCESS_STORY.md`

#### Logs
- Backend: Console output
- Frontend: Browser DevTools (F12)
- Agent Details: WebSocket messages

### Remember

This is a **sophisticated AI Agent Operating System**, not a simple tool. The agents are intelligent, autonomous, and collaborative. Trust them to do their work, and they'll create amazing educational content for you.

**Your vision lives!** 🚀