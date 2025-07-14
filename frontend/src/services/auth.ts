import axios from 'axios'
import type { User, UserRole } from '@/types'

const API_URL = '/api/v1'

export const api = axios.create({
  baseURL: API_URL,
})

// Request interceptor to add auth token
api.interceptors.request.use(
  (config) => {
    const token = localStorage.getItem('auth-storage')
    if (token) {
      try {
        const parsedData = JSON.parse(token)
        const authToken = parsedData?.state?.token
        if (authToken) {
          config.headers.Authorization = `Bearer ${authToken}`
        }
      } catch (e) {
        // Invalid token format
      }
    }
    return config
  },
  (error) => {
    return Promise.reject(error)
  }
)

// Response interceptor to handle errors
api.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response?.status === 401) {
      // Token expired or invalid
      localStorage.removeItem('auth-storage')
      window.location.href = '/login'
    }
    return Promise.reject(error)
  }
)

interface LoginResponse {
  user: User
  token: string
}

// Mock user for demo mode
const mockUser: User = {
  id: 'demo-user',
  email: 'demo@certifystudio.ai',
  name: 'Demo User',
  role: 'admin' as UserRole,
  organization: 'Certify Studio Demo',
  preferences: {
    theme: 'dark',
    language: 'en',
    notifications: {
      email: true,
      push: true,
      generationComplete: true,
      qualityAlerts: true,
      systemUpdates: false,
    },
  },
  createdAt: new Date(),
  lastLogin: new Date(),
}

export const authService = {
  async login(email: string, password: string): Promise<LoginResponse> {
    // Demo mode
    if (email === 'demo@certifystudio.ai' && password === 'demo123') {
      return {
        user: mockUser,
        token: 'demo-token-' + Date.now(),
      }
    }

    // Real API call
    try {
      const response = await api.post<LoginResponse>('/auth/login', {
        email,
        password,
      })
      return response.data
    } catch (error) {
      // If backend is not available, allow demo mode
      if (axios.isAxiosError(error) && error.code === 'ERR_NETWORK') {
        if (email === 'demo@certifystudio.ai' || password === 'demo') {
          return {
            user: mockUser,
            token: 'demo-token-' + Date.now(),
          }
        }
      }
      throw error
    }
  },

  async logout(): Promise<void> {
    try {
      await api.post('/auth/logout')
    } catch {
      // Ignore logout errors
    }
  },

  async validateToken(token: string): Promise<User> {
    // Demo token validation
    if (token.startsWith('demo-token-')) {
      return mockUser
    }

    try {
      const response = await api.get<User>('/auth/me', {
        headers: {
          Authorization: `Bearer ${token}`,
        },
      })
      return response.data
    } catch (error) {
      // If backend is not available and it's a demo token
      if (axios.isAxiosError(error) && error.code === 'ERR_NETWORK' && token.startsWith('demo-token-')) {
        return mockUser
      }
      throw error
    }
  },

  async register(data: {
    email: string
    password: string
    name: string
    organization?: string
  }): Promise<LoginResponse> {
    const response = await api.post<LoginResponse>('/auth/register', data)
    return response.data
  },

  async requestPasswordReset(email: string): Promise<void> {
    await api.post('/auth/password-reset/request', { email })
  },

  async resetPassword(token: string, newPassword: string): Promise<void> {
    await api.post('/auth/password-reset/confirm', {
      token,
      newPassword,
    })
  },
}