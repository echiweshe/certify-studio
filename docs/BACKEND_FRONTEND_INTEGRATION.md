# Certify Studio - Backend & Frontend Integration Guide

## Overview

This guide explains how the frontend and backend are now connected with real-time data flow.

## Architecture

```
Frontend (React)
    ↓ HTTP/WebSocket
API Service (api.ts)
    ↓
Backend API (FastAPI)
    ↓
Frontend Connector
    ↓
Agent Services
    ↓
AI Agents
```

## Key Components

### 1. API Service (`frontend/src/services/api.ts`)
- Centralized API client using Axios
- WebSocket manager for real-time updates
- Automatic token management
- Error handling and retries

### 2. Frontend Connector (`src/certify_studio/frontend_connector.py`)
- WebSocket endpoint for real-time agent updates
- REST endpoints for dashboard data
- Agent state broadcasting
- Event hooks for system updates

### 3. Services

#### Agent Service (`frontend/src/services/agents.ts`)
- Fetches agent data from backend
- Subscribes to real-time updates
- Falls back to mock data in dev mode

#### Auth Service
- Handles login/logout
- Token persistence
- User session management

### 4. Hooks

#### `useDashboard.ts`
- Dashboard statistics
- Collaboration metrics
- Knowledge graph stats
- Auto-refresh capabilities

#### `useAgents.ts`
- Agent list and details
- Real-time status updates
- Performance metrics
- Collaboration events

## Real-Time Updates

### WebSocket Topics
- `agents` - Agent state changes
- `collaboration` - Agent collaboration events
- `generation_all` - Content generation progress
- `quality_all` - Quality check updates
- `knowledge_graph` - Knowledge graph changes

### Connection Flow
1. Frontend connects to WebSocket on load
2. Subscribes to relevant topics
3. Receives initial state
4. Gets real-time updates as they occur

## API Endpoints

### Dashboard
- `GET /api/v1/dashboard/stats` - Overall statistics
- `GET /api/v1/dashboard/agents` - Agent statuses
- `GET /api/v1/dashboard/collaboration` - Collaboration metrics
- `GET /api/v1/dashboard/knowledge-graph` - Knowledge graph stats

### Authentication
- `POST /api/v1/auth/register` - User registration
- `POST /api/v1/auth/login` - User login
- `GET /api/v1/auth/me` - Current user info

### Content Generation
- `POST /api/v1/generation/upload` - Upload files
- `POST /api/v1/generation/generate` - Start generation
- `GET /api/v1/generation/status/{job_id}` - Check progress

## Testing the Integration

### 1. Start the Backend
```bash
uv run uvicorn certify_studio.main:app --reload
```

### 2. Start the Frontend
```bash
cd frontend
npm run dev
```

### 3. Test Connectivity
```bash
# Run the connectivity test
uv run python tests/test_backend_connectivity.py
```

### 4. Run Full Test Suite
```bash
# Run comprehensive tests
.\run_comprehensive_tests.bat
```

## Common Issues & Solutions

### WebSocket Connection Failed
- Check if backend is running
- Verify CORS settings
- Check firewall/proxy settings

### Authentication Issues
- Clear browser localStorage
- Check token expiration
- Verify backend auth endpoints

### No Real-Time Updates
- Check WebSocket connection in browser console
- Verify topic subscriptions
- Check backend event broadcasting

## Development Tips

### Mock Data Fallback
The frontend automatically falls back to mock data when:
- Backend is unreachable
- API calls fail
- Running in development mode

### Debug Mode
Enable debug logging:
```javascript
// In browser console
localStorage.setItem('debug', 'certify:*')
```

### Network Tab
Monitor API calls and WebSocket messages in browser DevTools Network tab.

## Production Considerations

### Environment Variables
```bash
# Frontend (.env)
VITE_API_URL=https://api.certifystudio.com

# Backend (.env)
CORS_ORIGINS=["https://app.certifystudio.com"]
```

### Security
- Enable HTTPS for production
- Use secure WebSocket (wss://)
- Implement rate limiting
- Add request signing

### Performance
- Enable response caching
- Use CDN for static assets
- Implement connection pooling
- Add request debouncing

## Next Steps

1. **Add More Real-Time Features**
   - Live collaboration cursors
   - Push notifications
   - Activity feeds

2. **Enhance Error Handling**
   - Retry logic for failed requests
   - Offline mode support
   - Error boundary components

3. **Optimize Performance**
   - Implement virtual scrolling
   - Add request caching
   - Use React Query for data fetching

4. **Improve Testing**
   - Add E2E tests with Playwright
   - Mock WebSocket in tests
   - Add performance benchmarks
