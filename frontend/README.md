# Certify Studio Frontend

The revolutionary frontend for the AI Agent Operating System that transforms educational content creation.

## 🚀 Features

- **Real-time Agent Orchestration Visualization**: Watch AI agents collaborate in real-time with 2D flow diagrams and 3D network visualizations
- **Intuitive Content Generation**: Drag-and-drop interface for uploading content and selecting output formats
- **Advanced Analytics Dashboard**: Deep insights into learning outcomes, agent performance, and system metrics
- **Knowledge Graph Explorer**: Interactive visualization of concept relationships and learning pathways
- **Responsive Design**: Fully responsive with dark/light theme support
- **Accessibility First**: WCAG compliant with full keyboard navigation and screen reader support

## 🛠️ Technology Stack

- **React 18** with TypeScript
- **Vite** for blazing fast development
- **Framer Motion** for smooth animations
- **React Flow** for node-based visualizations
- **Three.js** for 3D visualizations
- **Recharts** for data visualization
- **Tailwind CSS** for styling
- **Radix UI** for accessible components
- **React Query** for server state management
- **Zustand** for client state management

## 📦 Installation

1. Clone the repository
2. Navigate to the frontend directory:
   ```bash
   cd certify-studio/frontend
   ```

3. Install dependencies:
   ```bash
   npm install
   ```

4. Copy environment variables:
   ```bash
   cp .env.example .env
   ```

5. Start the development server:
   ```bash
   npm run dev
   ```

The frontend will be available at `http://localhost:3000`

## 🏗️ Project Structure

```
frontend/
├── src/
│   ├── components/      # Reusable components
│   ├── pages/          # Page components
│   ├── stores/         # Zustand stores
│   ├── services/       # API services
│   ├── hooks/          # Custom React hooks
│   ├── utils/          # Utility functions
│   └── types/          # TypeScript types
├── public/             # Static assets
└── index.html          # Entry HTML file
```

## 🎨 Key Components

### Agent Orchestrator
- Real-time visualization of agent collaboration
- 2D flow diagram and 3D network views
- Live message flow between agents
- Agent status monitoring

### Content Generation
- Multi-format output selection
- Real-time generation progress
- Cognitive load optimization settings
- Accessibility options

### Dashboard
- Platform metrics overview
- Active agent monitoring
- Recent generation tracking
- Performance analytics

### Knowledge Graph
- Interactive concept visualization
- Learning path exploration
- Relationship mapping
- Graph statistics

## 🔧 Development

### Available Scripts

- `npm run dev` - Start development server
- `npm run build` - Build for production
- `npm run preview` - Preview production build
- `npm run lint` - Run ESLint
- `npm run type-check` - Run TypeScript type checking

### Code Style

- TypeScript for type safety
- ESLint for code quality
- Prettier for code formatting
- Tailwind CSS for styling

## 🚀 Production Build

To create a production build:

```bash
npm run build
```

The build output will be in the `dist` directory.

## 🔗 Backend Integration

The frontend expects the backend API to be running on `http://localhost:8000`. Update the `.env` file to change the API URL if needed.

## 📱 Progressive Web App

The frontend is configured as a PWA with:
- Offline support
- App manifest
- Service worker
- Installation prompt

## 🎯 Future Enhancements

- [ ] Real-time collaboration features
- [ ] Advanced 3D visualizations
- [ ] Voice interface integration
- [ ] AR/VR preview capabilities
- [ ] Plugin system for custom components

## 📄 License

This project is part of the Certify Studio platform.
