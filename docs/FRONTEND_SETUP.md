# Frontend Development Guide

## 🎨 Modern Frontend for Certify Studio

### Quick Setup Commands

```bash
# 1. Create frontend directory
cd C:\ZBDuo_Share\Labs\src\BttlnsCldMCP\certify-studio
mkdir frontend
cd frontend

# 2. Initialize Vite + React + TypeScript
npm create vite@latest . -- --template react-ts

# 3. Install core dependencies
npm install

# 4. Install UI framework (choose one)
# Option A: Material-UI (recommended)
npm install @mui/material @emotion/react @emotion/styled @mui/icons-material

# Option B: Ant Design
npm install antd @ant-design/icons

# 5. Install essential packages
npm install axios react-query @tanstack/react-query
npm install react-router-dom
npm install react-hook-form zod @hookform/resolvers
npm install socket.io-client
npm install recharts
npm install date-fns
npm install react-dropzone

# 6. Install dev dependencies
npm install -D @types/react @types/node
npm install -D @typescript-eslint/eslint-plugin @typescript-eslint/parser
npm install -D prettier eslint-config-prettier
npm install -D @vitejs/plugin-react-swc
```

### Project Structure

```
frontend/
├── src/
│   ├── api/
│   │   ├── client.ts         # Axios configuration
│   │   ├── endpoints/        # API endpoint functions
│   │   └── types/           # Generated TypeScript types
│   ├── components/
│   │   ├── common/          # Shared components
│   │   ├── upload/          # File upload components
│   │   ├── generation/      # Content generation UI
│   │   ├── quality/         # QA components
│   │   └── export/          # Export components
│   ├── features/
│   │   ├── auth/           # Authentication
│   │   ├── dashboard/      # Main dashboard
│   │   ├── projects/       # Project management
│   │   └── settings/       # User settings
│   ├── hooks/              # Custom React hooks
│   ├── layouts/            # Page layouts
│   ├── pages/              # Route pages
│   ├── services/           # Business logic
│   ├── store/              # State management
│   ├── styles/             # Global styles
│   ├── types/              # TypeScript types
│   ├── utils/              # Utility functions
│   ├── App.tsx
│   └── main.tsx
├── public/
├── index.html
├── package.json
├── tsconfig.json
├── vite.config.ts
└── .env
```

### Environment Configuration

Create `.env` file:
```env
VITE_API_URL=http://localhost:8000
VITE_WS_URL=ws://localhost:8000
VITE_APP_NAME=Certify Studio
VITE_APP_VERSION=1.0.0
```

### Vite Configuration

```typescript
// vite.config.ts
import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react-swc'
import path from 'path'

export default defineConfig({
  plugins: [react()],
  resolve: {
    alias: {
      '@': path.resolve(__dirname, './src'),
    },
  },
  server: {
    port: 3000,
    proxy: {
      '/api': {
        target: 'http://localhost:8000',
        changeOrigin: true,
      },
      '/ws': {
        target: 'ws://localhost:8000',
        ws: true,
      },
    },
  },
})
```

### TypeScript Configuration

```json
// tsconfig.json
{
  "compilerOptions": {
    "target": "ES2020",
    "useDefineForClassFields": true,
    "lib": ["ES2020", "DOM", "DOM.Iterable"],
    "module": "ESNext",
    "skipLibCheck": true,
    "moduleResolution": "bundler",
    "allowImportingTsExtensions": true,
    "resolveJsonModule": true,
    "isolatedModules": true,
    "noEmit": true,
    "jsx": "react-jsx",
    "strict": true,
    "noUnusedLocals": true,
    "noUnusedParameters": true,
    "noFallthroughCasesInSwitch": true,
    "baseUrl": ".",
    "paths": {
      "@/*": ["src/*"]
    }
  },
  "include": ["src"],
  "references": [{ "path": "./tsconfig.node.json" }]
}
```

### API Client Setup

```typescript
// src/api/client.ts
import axios from 'axios';

const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';

export const apiClient = axios.create({
  baseURL: API_URL,
  headers: {
    'Content-Type': 'application/json',
  },
});

// Add auth interceptor
apiClient.interceptors.request.use((config) => {
  const token = localStorage.getItem('access_token');
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

// Add response interceptor for error handling
apiClient.interceptors.response.use(
  (response) => response,
  async (error) => {
    if (error.response?.status === 401) {
      // Handle token refresh
    }
    return Promise.reject(error);
  }
);
```

### Key Features to Implement

1. **Authentication Flow**
   - Login/Register forms
   - JWT token management
   - Protected routes
   - User profile

2. **Dashboard**
   - Overview cards
   - Recent projects
   - Quick actions
   - Statistics

3. **PDF Upload**
   - Drag-and-drop zone
   - Upload progress
   - File validation
   - Batch uploads

4. **Content Generation**
   - Configuration wizard
   - Real-time progress
   - Preview panel
   - Template selection

5. **Quality Assurance**
   - Review interface
   - Annotation tools
   - Feedback forms
   - Approval workflow

6. **Export Center**
   - Format selection
   - Configuration options
   - Download manager
   - Batch exports

### Run Development Server

```bash
# Start frontend dev server
npm run dev

# In another terminal, start backend
cd ..
uv run uvicorn certify_studio.main:app --reload

# Access frontend at http://localhost:3000
# Backend API at http://localhost:8000
```

### Build for Production

```bash
# Build optimized version
npm run build

# Preview production build
npm run preview

# Output will be in dist/ directory
```

### Next Steps

1. Generate TypeScript types from OpenAPI schema
2. Set up React Query for data fetching
3. Implement authentication flow
4. Create main layout with navigation
5. Build file upload component
6. Add real-time WebSocket connection
7. Implement each feature module
8. Add comprehensive testing

The backend is ready and waiting! Let's build an amazing frontend! 🚀
