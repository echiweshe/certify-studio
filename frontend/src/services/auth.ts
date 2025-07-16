// Re-export the api client from the main api service
export { apiClient as api } from './api';

// Authentication utilities
export function isAuthenticated(): boolean {
  return !!localStorage.getItem('auth_token');
}

export function getAuthToken(): string | null {
  return localStorage.getItem('auth_token');
}

export function clearAuth(): void {
  localStorage.removeItem('auth_token');
  window.location.href = '/login';
}
