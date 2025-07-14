import { motion } from 'framer-motion'
import {
  Settings as SettingsIcon,
  User,
  Bell,
  Shield,
  Palette,
  Globe,
  Key,
  CreditCard,
  Users,
  Save,
} from 'lucide-react'
import * as Tabs from '@radix-ui/react-tabs'
import * as Switch from '@radix-ui/react-switch'
import * as Select from '@radix-ui/react-select'
import { useAuthStore } from '@/stores/authStore'
import { useTheme } from '@/components/ThemeProvider'
import { useState } from 'react'
import toast from 'react-hot-toast'

export default function Settings() {
  const { user, updateUser } = useAuthStore()
  const { theme, setTheme } = useTheme()
  const [isLoading, setIsLoading] = useState(false)

  const [preferences, setPreferences] = useState({
    emailNotifications: true,
    pushNotifications: false,
    generationComplete: true,
    qualityAlerts: true,
    systemUpdates: false,
    language: 'en',
  })

  const handleSave = async () => {
    setIsLoading(true)
    try {
      // Simulate API call
      await new Promise(resolve => setTimeout(resolve, 1000))
      toast.success('Settings saved successfully')
    } catch (error) {
      toast.error('Failed to save settings')
    } finally {
      setIsLoading(false)
    }
  }

  return (
    <div className="space-y-6 max-w-4xl">
      {/* Header */}
      <div>
        <h1 className="text-3xl font-bold">Settings</h1>
        <p className="text-muted-foreground mt-1">
          Manage your account and platform preferences
        </p>
      </div>

      <Tabs.Root defaultValue="profile" className="space-y-6">
        <Tabs.List className="flex items-center space-x-4 border-b border-border pb-2 overflow-x-auto">
          <Tabs.Trigger
            value="profile"
            className="flex items-center space-x-2 text-sm font-medium pb-2 border-b-2 border-transparent data-[state=active]:border-primary transition-colors whitespace-nowrap"
          >
            <User className="h-4 w-4" />
            <span>Profile</span>
          </Tabs.Trigger>
          <Tabs.Trigger
            value="notifications"
            className="flex items-center space-x-2 text-sm font-medium pb-2 border-b-2 border-transparent data-[state=active]:border-primary transition-colors whitespace-nowrap"
          >
            <Bell className="h-4 w-4" />
            <span>Notifications</span>
          </Tabs.Trigger>
          <Tabs.Trigger
            value="appearance"
            className="flex items-center space-x-2 text-sm font-medium pb-2 border-b-2 border-transparent data-[state=active]:border-primary transition-colors whitespace-nowrap"
          >
            <Palette className="h-4 w-4" />
            <span>Appearance</span>
          </Tabs.Trigger>
          <Tabs.Trigger
            value="security"
            className="flex items-center space-x-2 text-sm font-medium pb-2 border-b-2 border-transparent data-[state=active]:border-primary transition-colors whitespace-nowrap"
          >
            <Shield className="h-4 w-4" />
            <span>Security</span>
          </Tabs.Trigger>
          <Tabs.Trigger
            value="billing"
            className="flex items-center space-x-2 text-sm font-medium pb-2 border-b-2 border-transparent data-[state=active]:border-primary transition-colors whitespace-nowrap"
          >
            <CreditCard className="h-4 w-4" />
            <span>Billing</span>
          </Tabs.Trigger>
          <Tabs.Trigger
            value="team"
            className="flex items-center space-x-2 text-sm font-medium pb-2 border-b-2 border-transparent data-[state=active]:border-primary transition-colors whitespace-nowrap"
          >
            <Users className="h-4 w-4" />
            <span>Team</span>
          </Tabs.Trigger>
        </Tabs.List>

        {/* Profile Tab */}
        <Tabs.Content value="profile">
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            className="card-depth p-6 space-y-6"
          >
            <h2 className="text-lg font-semibold">Profile Information</h2>
            
            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
              <div>
                <label className="block text-sm font-medium mb-2">Full Name</label>
                <input
                  type="text"
                  defaultValue={user?.name}
                  className="w-full px-3 py-2 rounded-lg bg-card border border-input focus:outline-none focus:ring-2 focus:ring-primary"
                />
              </div>
              <div>
                <label className="block text-sm font-medium mb-2">Email</label>
                <input
                  type="email"
                  defaultValue={user?.email}
                  className="w-full px-3 py-2 rounded-lg bg-card border border-input focus:outline-none focus:ring-2 focus:ring-primary"
                />
              </div>
              <div>
                <label className="block text-sm font-medium mb-2">Organization</label>
                <input
                  type="text"
                  defaultValue={user?.organization}
                  className="w-full px-3 py-2 rounded-lg bg-card border border-input focus:outline-none focus:ring-2 focus:ring-primary"
                />
              </div>
              <div>
                <label className="block text-sm font-medium mb-2">Role</label>
                <input
                  type="text"
                  value={user?.role.replace('_', ' ')}
                  disabled
                  className="w-full px-3 py-2 rounded-lg bg-muted border border-input opacity-50 capitalize"
                />
              </div>
            </div>

            <div>
              <label className="block text-sm font-medium mb-2">Bio</label>
              <textarea
                rows={4}
                placeholder="Tell us about yourself..."
                className="w-full px-3 py-2 rounded-lg bg-card border border-input focus:outline-none focus:ring-2 focus:ring-primary resize-none"
              />
            </div>
          </motion.div>
        </Tabs.Content>

        {/* Notifications Tab */}
        <Tabs.Content value="notifications">
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            className="card-depth p-6 space-y-6"
          >
            <h2 className="text-lg font-semibold">Notification Preferences</h2>
            
            <div className="space-y-4">
              <div className="flex items-center justify-between">
                <div>
                  <p className="font-medium">Email Notifications</p>
                  <p className="text-sm text-muted-foreground">Receive updates via email</p>
                </div>
                <Switch.Root
                  checked={preferences.emailNotifications}
                  onCheckedChange={(checked) => 
                    setPreferences(prev => ({ ...prev, emailNotifications: checked }))
                  }
                  className="w-11 h-6 bg-muted rounded-full relative data-[state=checked]:bg-primary transition-colors"
                >
                  <Switch.Thumb className="block w-5 h-5 bg-white rounded-full transition-transform translate-x-0.5 will-change-transform data-[state=checked]:translate-x-[22px]" />
                </Switch.Root>
              </div>

              <div className="flex items-center justify-between">
                <div>
                  <p className="font-medium">Push Notifications</p>
                  <p className="text-sm text-muted-foreground">Receive browser notifications</p>
                </div>
                <Switch.Root
                  checked={preferences.pushNotifications}
                  onCheckedChange={(checked) => 
                    setPreferences(prev => ({ ...prev, pushNotifications: checked }))
                  }
                  className="w-11 h-6 bg-muted rounded-full relative data-[state=checked]:bg-primary transition-colors"
                >
                  <Switch.Thumb className="block w-5 h-5 bg-white rounded-full transition-transform translate-x-0.5 will-change-transform data-[state=checked]:translate-x-[22px]" />
                </Switch.Root>
              </div>

              <div className="flex items-center justify-between">
                <div>
                  <p className="font-medium">Generation Complete</p>
                  <p className="text-sm text-muted-foreground">Notify when content generation is done</p>
                </div>
                <Switch.Root
                  checked={preferences.generationComplete}
                  onCheckedChange={(checked) => 
                    setPreferences(prev => ({ ...prev, generationComplete: checked }))
                  }
                  className="w-11 h-6 bg-muted rounded-full relative data-[state=checked]:bg-primary transition-colors"
                >
                  <Switch.Thumb className="block w-5 h-5 bg-white rounded-full transition-transform translate-x-0.5 will-change-transform data-[state=checked]:translate-x-[22px]" />
                </Switch.Root>
              </div>

              <div className="flex items-center justify-between">
                <div>
                  <p className="font-medium">Quality Alerts</p>
                  <p className="text-sm text-muted-foreground">Alert on quality issues</p>
                </div>
                <Switch.Root
                  checked={preferences.qualityAlerts}
                  onCheckedChange={(checked) => 
                    setPreferences(prev => ({ ...prev, qualityAlerts: checked }))
                  }
                  className="w-11 h-6 bg-muted rounded-full relative data-[state=checked]:bg-primary transition-colors"
                >
                  <Switch.Thumb className="block w-5 h-5 bg-white rounded-full transition-transform translate-x-0.5 will-change-transform data-[state=checked]:translate-x-[22px]" />
                </Switch.Root>
              </div>
            </div>
          </motion.div>
        </Tabs.Content>

        {/* Appearance Tab */}
        <Tabs.Content value="appearance">
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            className="card-depth p-6 space-y-6"
          >
            <h2 className="text-lg font-semibold">Appearance Settings</h2>
            
            <div>
              <label className="block text-sm font-medium mb-3">Theme</label>
              <div className="grid grid-cols-3 gap-3">
                <button
                  onClick={() => setTheme('light')}
                  className={`p-4 rounded-lg border-2 transition-all ${
                    theme === 'light' ? 'border-primary bg-primary/10' : 'border-border'
                  }`}
                >
                  <div className="h-8 w-8 rounded bg-white border border-gray-300 mx-auto mb-2" />
                  <p className="text-sm">Light</p>
                </button>
                <button
                  onClick={() => setTheme('dark')}
                  className={`p-4 rounded-lg border-2 transition-all ${
                    theme === 'dark' ? 'border-primary bg-primary/10' : 'border-border'
                  }`}
                >
                  <div className="h-8 w-8 rounded bg-gray-900 border border-gray-700 mx-auto mb-2" />
                  <p className="text-sm">Dark</p>
                </button>
                <button
                  onClick={() => setTheme('system')}
                  className={`p-4 rounded-lg border-2 transition-all ${
                    theme === 'system' ? 'border-primary bg-primary/10' : 'border-border'
                  }`}
                >
                  <div className="h-8 w-8 rounded bg-gradient-to-br from-white to-gray-900 mx-auto mb-2" />
                  <p className="text-sm">System</p>
                </button>
              </div>
            </div>

            <div>
              <label className="block text-sm font-medium mb-2">Language</label>
              <Select.Root value={preferences.language} onValueChange={(value) => 
                setPreferences(prev => ({ ...prev, language: value }))
              }>
                <Select.Trigger className="w-full px-3 py-2 rounded-lg bg-card border border-input flex items-center justify-between">
                  <Select.Value />
                  <Select.Icon>
                    <Globe className="h-4 w-4" />
                  </Select.Icon>
                </Select.Trigger>
                <Select.Portal>
                  <Select.Content className="glass rounded-lg p-1">
                    <Select.Item value="en" className="px-3 py-2 rounded-md hover:bg-accent cursor-pointer">
                      <Select.ItemText>English</Select.ItemText>
                    </Select.Item>
                    <Select.Item value="es" className="px-3 py-2 rounded-md hover:bg-accent cursor-pointer">
                      <Select.ItemText>Español</Select.ItemText>
                    </Select.Item>
                    <Select.Item value="fr" className="px-3 py-2 rounded-md hover:bg-accent cursor-pointer">
                      <Select.ItemText>Français</Select.ItemText>
                    </Select.Item>
                  </Select.Content>
                </Select.Portal>
              </Select.Root>
            </div>
          </motion.div>
        </Tabs.Content>

        {/* Other tabs would follow similar patterns */}
        <Tabs.Content value="security">
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            className="card-depth p-6"
          >
            <h2 className="text-lg font-semibold mb-4">Security Settings</h2>
            <p className="text-muted-foreground">Security settings coming soon...</p>
          </motion.div>
        </Tabs.Content>

        <Tabs.Content value="billing">
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            className="card-depth p-6"
          >
            <h2 className="text-lg font-semibold mb-4">Billing & Subscription</h2>
            <p className="text-muted-foreground">Billing information coming soon...</p>
          </motion.div>
        </Tabs.Content>

        <Tabs.Content value="team">
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            className="card-depth p-6"
          >
            <h2 className="text-lg font-semibold mb-4">Team Management</h2>
            <p className="text-muted-foreground">Team management coming soon...</p>
          </motion.div>
        </Tabs.Content>
      </Tabs.Root>

      {/* Save button */}
      <div className="flex justify-end">
        <button
          onClick={handleSave}
          disabled={isLoading}
          className="flex items-center space-x-2 px-4 py-2 rounded-lg bg-primary text-primary-foreground hover:bg-primary/90 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
        >
          {isLoading ? (
            <div className="h-4 w-4 border-2 border-primary-foreground/30 border-t-primary-foreground rounded-full animate-spin" />
          ) : (
            <Save className="h-4 w-4" />
          )}
          <span>Save Changes</span>
        </button>
      </div>
    </div>
  )
}