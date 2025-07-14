import { useState } from 'react'
import { Outlet, Link, useLocation, useNavigate } from 'react-router-dom'
import { motion, AnimatePresence } from 'framer-motion'
import {
  Brain,
  LayoutDashboard,
  Sparkles,
  GitBranch,
  BarChart3,
  Settings,
  LogOut,
  Menu,
  X,
  Moon,
  Sun,
  Bell,
  Search,
  ChevronDown,
} from 'lucide-react'
import { cn } from '@/utils'
import { useAuthStore } from '@/stores/authStore'
import { useTheme } from '@/components/ThemeProvider'
import * as DropdownMenu from '@radix-ui/react-dropdown-menu'
import * as Dialog from '@radix-ui/react-dialog'
import AgentStatusBar from '@/components/AgentStatusBar'

const navigation = [
  { name: 'Dashboard', href: '/', icon: LayoutDashboard },
  { name: 'Agent Orchestrator', href: '/orchestrator', icon: Brain },
  { name: 'Content Generation', href: '/generation', icon: Sparkles },
  { name: 'Knowledge Graph', href: '/knowledge', icon: GitBranch },
  { name: 'Analytics', href: '/analytics', icon: BarChart3 },
  { name: 'Settings', href: '/settings', icon: Settings },
]

export default function Layout() {
  const [sidebarOpen, setSidebarOpen] = useState(false)
  const [searchOpen, setSearchOpen] = useState(false)
  const location = useLocation()
  const navigate = useNavigate()
  const { user, logout } = useAuthStore()
  const { theme, setTheme } = useTheme()

  const handleLogout = () => {
    logout()
    navigate('/login')
  }

  const handleNavigation = (href: string) => {
    setSidebarOpen(false) // Close mobile sidebar
  }

  return (
    <div className="min-h-screen bg-background flex">
      {/* Mobile sidebar backdrop */}
      <AnimatePresence>
        {sidebarOpen && (
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            className="fixed inset-0 z-50 bg-black/50 lg:hidden"
            onClick={() => setSidebarOpen(false)}
          />
        )}
      </AnimatePresence>

      {/* Sidebar */}
      <aside
        className={cn(
          'fixed lg:fixed left-0 top-0 z-50 h-screen w-80',
          'bg-card border-r border-border',
          'transform transition-transform duration-300 ease-in-out lg:transform-none',
          sidebarOpen ? 'translate-x-0' : '-translate-x-full lg:translate-x-0'
        )}
      >
        <div className="flex h-full flex-col">
          {/* Logo */}
          <div className="flex h-16 items-center justify-between px-6 border-b border-border">
            <Link to="/" className="flex items-center space-x-3" onClick={() => handleNavigation('/')}>
              <div className="relative h-10 w-10">
                <div className="absolute inset-0 rounded-lg bg-gradient-to-br from-blue-500 to-purple-600 animate-pulse" />
                <div className="absolute inset-0 flex items-center justify-center">
                  <Brain className="h-6 w-6 text-white" />
                </div>
              </div>
              <div>
                <h1 className="text-lg font-bold gradient-text">Certify Studio</h1>
                <p className="text-xs text-muted-foreground">AI Agent OS</p>
              </div>
            </Link>
            <button
              onClick={() => setSidebarOpen(false)}
              className="lg:hidden p-2 hover:bg-accent rounded-lg"
            >
              <X className="h-5 w-5" />
            </button>
          </div>

          {/* Navigation */}
          <nav className="flex-1 space-y-1 px-3 py-4 overflow-y-auto">
            {navigation.map((item) => {
              const isActive = location.pathname === item.href
              return (
                <Link
                  key={item.name}
                  to={item.href}
                  onClick={() => handleNavigation(item.href)}
                  className={cn(
                    'flex items-center space-x-3 rounded-lg px-3 py-2.5',
                    'transition-all duration-200',
                    isActive
                      ? 'bg-primary text-primary-foreground shadow-lg'
                      : 'hover:bg-accent text-muted-foreground hover:text-foreground'
                  )}
                >
                  <item.icon className="h-5 w-5 flex-shrink-0" />
                  <span className="font-medium">{item.name}</span>
                </Link>
              )
            })}
          </nav>

          {/* Agent Status Bar */}
          <div className="border-t border-border px-3 py-4">
            <AgentStatusBar />
          </div>

          {/* User section */}
          <div className="border-t border-border p-4">
            <DropdownMenu.Root>
              <DropdownMenu.Trigger asChild>
                <button className="flex w-full items-center space-x-3 rounded-lg p-3 hover:bg-accent transition-colors">
                  <div className="h-10 w-10 rounded-full bg-gradient-to-br from-blue-500 to-purple-600 flex-shrink-0" />
                  <div className="flex-1 text-left min-w-0">
                    <p className="text-sm font-medium truncate">{user?.name || 'Demo User'}</p>
                    <p className="text-xs text-muted-foreground truncate">{user?.email || 'demo@certifystudio.ai'}</p>
                  </div>
                  <ChevronDown className="h-4 w-4 text-muted-foreground flex-shrink-0" />
                </button>
              </DropdownMenu.Trigger>
              <DropdownMenu.Portal>
                <DropdownMenu.Content
                  className="w-56 rounded-lg bg-card border border-border shadow-lg p-2"
                  sideOffset={5}
                >
                  <DropdownMenu.Item
                    className="flex items-center space-x-2 rounded-md px-3 py-2 hover:bg-accent cursor-pointer outline-none"
                    onClick={handleLogout}
                  >
                    <LogOut className="h-4 w-4" />
                    <span>Logout</span>
                  </DropdownMenu.Item>
                </DropdownMenu.Content>
              </DropdownMenu.Portal>
            </DropdownMenu.Root>
          </div>
        </div>
      </aside>

      {/* Main content area */}
      <div className="flex-1 lg:ml-80 flex flex-col min-h-screen">
        {/* Top bar */}
        <header className="sticky top-0 z-40 h-16 flex items-center justify-between border-b border-border bg-background px-4 sm:px-6">
          <div className="flex items-center space-x-4">
            <button
              onClick={() => setSidebarOpen(true)}
              className="lg:hidden p-2 hover:bg-accent rounded-lg"
            >
              <Menu className="h-5 w-5" />
            </button>
            
            {/* Search */}
            <button
              onClick={() => setSearchOpen(true)}
              className="flex items-center space-x-2 rounded-lg bg-accent px-3 py-2 text-sm hover:bg-accent/80 transition-colors"
            >
              <Search className="h-4 w-4" />
              <span className="hidden sm:inline">Search</span>
              <kbd className="hidden sm:inline-flex h-5 select-none items-center gap-1 rounded border bg-muted px-1.5 font-mono text-[10px] font-medium">
                <span className="text-xs">⌘</span>K
              </kbd>
            </button>
          </div>

          <div className="flex items-center space-x-4">
            {/* Notifications */}
            <button className="relative p-2 hover:bg-accent rounded-lg">
              <Bell className="h-5 w-5" />
              <span className="absolute top-1 right-1 h-2 w-2 rounded-full bg-red-500" />
            </button>

            {/* Theme toggle */}
            <button
              onClick={() => setTheme(theme === 'dark' ? 'light' : 'dark')}
              className="p-2 hover:bg-accent rounded-lg"
            >
              {theme === 'dark' ? (
                <Sun className="h-5 w-5" />
              ) : (
                <Moon className="h-5 w-5" />
              )}
            </button>
          </div>
        </header>

        {/* Page content */}
        <main className="flex-1 overflow-y-auto">
          <div className="p-4 sm:p-6 lg:p-8">
            <AnimatePresence mode="wait">
              <motion.div
                key={location.pathname}
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                exit={{ opacity: 0, y: -20 }}
                transition={{ duration: 0.2 }}
              >
                <Outlet />
              </motion.div>
            </AnimatePresence>
          </div>
        </main>
      </div>

      {/* Search modal */}
      <Dialog.Root open={searchOpen} onOpenChange={setSearchOpen}>
        <Dialog.Portal>
          <Dialog.Overlay className="fixed inset-0 z-50 bg-black/50 animate-in fade-in-0" />
          <Dialog.Content className="fixed left-[50%] top-[50%] z-50 w-full max-w-2xl translate-x-[-50%] translate-y-[-50%] rounded-lg bg-card border border-border shadow-lg p-6 animate-in fade-in-0 zoom-in-95">
            <div className="flex items-center space-x-2 mb-4">
              <Search className="h-5 w-5 text-muted-foreground" />
              <input
                type="text"
                placeholder="Search agents, content, or commands..."
                className="flex-1 bg-transparent outline-none text-lg placeholder:text-muted-foreground"
                autoFocus
              />
            </div>
            <div className="space-y-2">
              <p className="text-sm text-muted-foreground">Recent searches</p>
              {/* Search results would go here */}
            </div>
          </Dialog.Content>
        </Dialog.Portal>
      </Dialog.Root>
    </div>
  )
}