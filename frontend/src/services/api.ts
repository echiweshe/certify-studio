// Frontend API Service - Real Backend Connection
import axios, { AxiosInstance, AxiosError } from 'axios';

// API configuration
const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';
const WS_BASE_URL = API_BASE_URL.replace(/^http/, 'ws');

// Create axios instance with default config
export const apiClient: AxiosInstance = axios.create({
  baseURL: `${API_BASE_URL}/api/v1`,
  headers: {
    'Content-Type': 'application/json',
  },
  timeout: 30000, // 30 seconds
});

// Add request interceptor to include auth token
apiClient.interceptors.request.use(
  (config) => {
    const token = localStorage.getItem('auth_token');
    if (token) {
      config.headers.Authorization = `Bearer ${token}`;
    }
    return config;
  },
  (error) => {
    return Promise.reject(error);
  }
);

// Add response interceptor for error handling
apiClient.interceptors.response.use(
  (response) => response,
  async (error: AxiosError) => {
    if (error.response?.status === 401) {
      // Token expired or invalid
      localStorage.removeItem('auth_token');
      window.location.href = '/login';
    }
    return Promise.reject(error);
  }
);

// WebSocket manager for real-time updates
export class WebSocketManager {
  private ws: WebSocket | null = null;
  private reconnectInterval: number = 5000;
  private reconnectAttempts: number = 0;
  private maxReconnectAttempts: number = 10;
  private subscribers: Map<string, Set<(data: any) => void>> = new Map();
  private clientId: string;
  private isConnecting: boolean = false;
  private connectionPromise: Promise<void> | null = null;

  constructor() {
    this.clientId = `frontend-${Math.random().toString(36).substr(2, 9)}`;
  }

  connect(): Promise<void> {
    if (this.ws?.readyState === WebSocket.OPEN) {
      return Promise.resolve();
    }

    if (this.isConnecting && this.connectionPromise) {
      return this.connectionPromise;
    }

    this.isConnecting = true;
    this.connectionPromise = new Promise((resolve, reject) => {
      const wsUrl = `${WS_BASE_URL}/ws/agents?client_id=${this.clientId}`;
      
      try {
        this.ws = new WebSocket(wsUrl);

        this.ws.onopen = () => {
          console.log('WebSocket connected');
          this.reconnectAttempts = 0;
          this.isConnecting = false;
          
          // Subscribe to default topics
          this.send({
            type: 'subscribe',
            topics: ['agents', 'collaboration', 'generation_all', 'quality_all']
          });
          
          resolve();
        };

        this.ws.onmessage = (event) => {
          try {
            const message = JSON.parse(event.data);
            this.handleMessage(message);
          } catch (error) {
            console.error('Failed to parse WebSocket message:', error);
          }
        };

        this.ws.onerror = (error) => {
          console.error('WebSocket error:', error);
          this.isConnecting = false;
          reject(error);
        };

        this.ws.onclose = () => {
          console.log('WebSocket disconnected');
          this.isConnecting = false;
          this.ws = null;
          
          // Attempt to reconnect
          if (this.reconnectAttempts < this.maxReconnectAttempts) {
            this.reconnectAttempts++;
            console.log(`Reconnecting in ${this.reconnectInterval}ms... (attempt ${this.reconnectAttempts})`);
            setTimeout(() => this.connect(), this.reconnectInterval);
          }
        };
      } catch (error) {
        this.isConnecting = false;
        reject(error);
      }
    });

    return this.connectionPromise;
  }

  disconnect() {
    if (this.ws) {
      this.ws.close();
      this.ws = null;
    }
    this.subscribers.clear();
  }

  subscribe(topic: string, callback: (data: any) => void) {
    if (!this.subscribers.has(topic)) {
      this.subscribers.set(topic, new Set());
    }
    this.subscribers.get(topic)!.add(callback);

    // Send subscription request to server
    if (this.ws?.readyState === WebSocket.OPEN) {
      this.send({
        type: 'subscribe',
        topics: [topic]
      });
    }
  }

  unsubscribe(topic: string, callback: (data: any) => void) {
    const callbacks = this.subscribers.get(topic);
    if (callbacks) {
      callbacks.delete(callback);
      if (callbacks.size === 0) {
        this.subscribers.delete(topic);
        
        // Send unsubscribe request to server
        if (this.ws?.readyState === WebSocket.OPEN) {
          this.send({
            type: 'unsubscribe',
            topics: [topic]
          });
        }
      }
    }
  }

  send(data: any) {
    if (this.ws?.readyState === WebSocket.OPEN) {
      this.ws.send(JSON.stringify(data));
    }
  }

  private handleMessage(message: any) {
    // Handle different message types
    switch (message.type) {
      case 'agent_state_update':
        this.notifySubscribers('agents', message.data);
        break;
      case 'collaboration_event':
        this.notifySubscribers('collaboration', message.data);
        break;
      case 'generation_progress':
        this.notifySubscribers(`generation_${message.data.job_id}`, message.data);
        this.notifySubscribers('generation_all', message.data);
        break;
      case 'quality_check_update':
        this.notifySubscribers(`qa_${message.data.content_id}`, message.data);
        this.notifySubscribers('quality_all', message.data);
        break;
      case 'initial_state':
        this.notifySubscribers('initial_state', message.data);
        break;
      default:
        console.log('Unhandled message type:', message.type);
    }
  }

  private notifySubscribers(topic: string, data: any) {
    const callbacks = this.subscribers.get(topic);
    if (callbacks) {
      callbacks.forEach(callback => {
        try {
          callback(data);
        } catch (error) {
          console.error('Error in subscriber callback:', error);
        }
      });
    }
  }
}

// Global WebSocket manager instance
export const wsManager = new WebSocketManager();

// API endpoints
export const api = {
  // Dashboard
  async getDashboardStats() {
    const response = await apiClient.get('/dashboard/stats');
    return response.data;
  },

  async getAgentStatuses() {
    const response = await apiClient.get('/dashboard/agents');
    return response.data;
  },

  async getCollaborationMetrics() {
    const response = await apiClient.get('/dashboard/collaboration');
    return response.data;
  },

  async getKnowledgeGraphStats() {
    const response = await apiClient.get('/dashboard/knowledge-graph');
    return response.data;
  },

  // Authentication
  async login(email: string, password: string) {
    const response = await apiClient.post('/auth/login', 
      new URLSearchParams({
        username: email,
        password: password,
      }),
      {
        headers: {
          'Content-Type': 'application/x-www-form-urlencoded',
        },
      }
    );
    
    if (response.data.access_token) {
      localStorage.setItem('auth_token', response.data.access_token);
    }
    
    return response.data;
  },

  async register(email: string, password: string, fullName: string) {
    const response = await apiClient.post('/auth/register', {
      email,
      password,
      full_name: fullName,
    });
    
    if (response.data.access_token) {
      localStorage.setItem('auth_token', response.data.access_token);
    }
    
    return response.data;
  },

  async logout() {
    localStorage.removeItem('auth_token');
    wsManager.disconnect();
  },

  async getCurrentUser() {
    const response = await apiClient.get('/auth/me');
    return response.data;
  },

  // Content Generation
  async uploadFile(file: File, onProgress?: (progress: number) => void) {
    const formData = new FormData();
    formData.append('file', file);

    const response = await apiClient.post('/generation/upload', formData, {
      headers: {
        'Content-Type': 'multipart/form-data',
      },
      onUploadProgress: (progressEvent) => {
        if (onProgress && progressEvent.total) {
          const progress = Math.round((progressEvent.loaded * 100) / progressEvent.total);
          onProgress(progress);
        }
      },
    });

    return response.data;
  },

  async extractDomains(fileIds: string[], config?: any) {
    const response = await apiClient.post('/domains/extract', {
      file_ids: fileIds,
      extraction_config: config || {
        extract_objectives: true,
        extract_domains: true,
        extract_prerequisites: true,
        extract_skills: true,
      },
    });

    return response.data;
  },

  async generateContent(request: any) {
    const response = await apiClient.post('/generation/generate', request);
    return response.data;
  },

  async getGenerationStatus(jobId: string) {
    const response = await apiClient.get(`/generation/status/${jobId}`);
    return response.data;
  },

  async getGenerationMetrics(contentId: string) {
    const response = await apiClient.get(`/generation/metrics/${contentId}`);
    return response.data;
  },

  // Quality Assurance
  async runQualityCheck(contentId: string, checks: string[]) {
    const response = await apiClient.post('/quality/check', {
      content_id: contentId,
      checks,
      strict_mode: true,
    });

    return response.data;
  },

  // Export
  async exportContent(contentId: string, format: string, config: any) {
    const response = await apiClient.post('/export/create', {
      content_id: contentId,
      format,
      [`${format}_config`]: config,
    });

    return response.data;
  },

  async downloadExport(downloadUrl: string) {
    const response = await apiClient.get(downloadUrl, {
      responseType: 'blob',
    });

    return response.data;
  },

  // Jobs
  async getJobStatus(jobId: string) {
    const response = await apiClient.get(`/jobs/${jobId}`);
    return response.data;
  },

  // System Info
  async getSystemInfo() {
    const response = await apiClient.get('/info');
    return response.data;
  },
};

export default api;
