import { create } from 'zustand'
import { persist } from 'zustand/middleware'
import type { User } from '@/types'
import api from '@/services/api'

interface AuthState {
  user: User | null
  token: string | null
  isAuthenticated: boolean
  isLoading: boolean
  login: (email: string, password: string) => Promise<void>
  logout: () => void
  checkAuth: () => Promise<void>
  updateUser: (user: Partial<User>) => void
}

export const useAuthStore = create<AuthState>()(
  persist(
    (set, get) => ({
      user: null,
      token: null,
      isAuthenticated: false,
      isLoading: false,

      login: async (email: string, password: string) => {
        set({ isLoading: true })
        try {
          const response = await api.login(email, password)
          
          // Get user details
          const userResponse = await api.getCurrentUser()
          
          set({
            user: {
              id: userResponse.id || '1',
              email: userResponse.email,
              name: userResponse.full_name || userResponse.email.split('@')[0],
              role: userResponse.role || 'user',
              avatar: userResponse.avatar || `https://ui-avatars.com/api/?name=${encodeURIComponent(userResponse.full_name || userResponse.email)}&background=6366f1&color=fff`,
            },
            token: response.access_token,
            isAuthenticated: true,
            isLoading: false,
          })
        } catch (error) {
          set({ isLoading: false })
          throw error
        }
      },

      logout: () => {
        api.logout()
        set({
          user: null,
          token: null,
          isAuthenticated: false,
        })
        window.location.href = '/login'
      },

      checkAuth: async () => {
        const token = localStorage.getItem('auth_token')
        if (!token) {
          set({ isAuthenticated: false })
          return
        }

        try {
          const user = await api.getCurrentUser()
          set({ 
            user: {
              id: user.id || '1',
              email: user.email,
              name: user.full_name || user.email.split('@')[0],
              role: user.role || 'user',
              avatar: user.avatar || `https://ui-avatars.com/api/?name=${encodeURIComponent(user.full_name || user.email)}&background=6366f1&color=fff`,
            },
            isAuthenticated: true,
            token 
          })
        } catch {
          // Token is invalid
          localStorage.removeItem('auth_token')
          set({ 
            isAuthenticated: false,
            user: null,
            token: null
          })
        }
      },

      updateUser: (updates: Partial<User>) => {
        const currentUser = get().user
        if (currentUser) {
          set({ user: { ...currentUser, ...updates } })
        }
      },
    }),
    {
      name: 'auth-storage',
      partialize: (state) => ({ 
        token: state.token,
        user: state.user,
        isAuthenticated: state.isAuthenticated 
      }),
      onRehydrateStorage: () => (state) => {
        // After rehydration, check if the stored auth is still valid
        if (state?.token && state?.isAuthenticated) {
          state.checkAuth()
        }
      },
    }
  )
)