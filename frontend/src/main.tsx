import React from 'react'
import ReactDOM from 'react-dom/client'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { createBrowserRouter, RouterProvider } from 'react-router-dom'
import { Toaster } from 'react-hot-toast'
import App from './App'
import Layout from '@/components/Layout'
import Dashboard from '@/pages/Dashboard'
import AgentOrchestrator from '@/pages/AgentOrchestrator'
import ContentGeneration from '@/pages/ContentGeneration'
import KnowledgeGraph from '@/pages/KnowledgeGraph'
import Analytics from '@/pages/Analytics'
import Settings from '@/pages/Settings'
import Login from '@/pages/Login'
import { ThemeProvider } from '@/components/ThemeProvider'
import './index.css'

const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      staleTime: 1000 * 60 * 5, // 5 minutes
      refetchOnWindowFocus: false,
    },
  },
})

// Create router with future flags enabled
const router = createBrowserRouter([
  {
    path: '/login',
    element: <Login />,
  },
  {
    path: '/',
    element: <App />,
    children: [
      {
        element: <Layout />,
        children: [
          {
            index: true,
            element: <Dashboard />,
          },
          {
            path: 'orchestrator',
            element: <AgentOrchestrator />,
          },
          {
            path: 'generation',
            element: <ContentGeneration />,
          },
          {
            path: 'knowledge',
            element: <KnowledgeGraph />,
          },
          {
            path: 'analytics',
            element: <Analytics />,
          },
          {
            path: 'settings',
            element: <Settings />,
          },
        ],
      },
    ],
  },
], {
  future: {
    v7_startTransition: true,
    v7_relativeSplatPath: true,
  },
})

ReactDOM.createRoot(document.getElementById('root')!).render(
  <React.StrictMode>
    <QueryClientProvider client={queryClient}>
      <ThemeProvider defaultTheme="dark" storageKey="certify-studio-theme">
        <RouterProvider router={router} />
        <Toaster
          position="bottom-right"
          toastOptions={{
            className: 'glass',
            duration: 4000,
            style: {
              background: 'rgba(0, 0, 0, 0.8)',
              color: '#fff',
              backdropFilter: 'blur(10px)',
            },
          }}
        />
      </ThemeProvider>
    </QueryClientProvider>
  </React.StrictMode>,
)
