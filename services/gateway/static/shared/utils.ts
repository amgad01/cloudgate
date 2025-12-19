/**
 * CloudGate API Gateway - Shared Utilities
 * Common functions used across the application
 */

import type { ApiResponse, FormData } from './types';

/**
 * Get API base URL
 * Priority order:
 * 1. Deployment-injected config from /api/config endpoint (set via FRONTEND_API_URL env var)
 * 2. Manual override via window.CLOUDGATE_API_URL
 * 3. Auto-detection from window.location.origin (production)
 * 4. Development fallback (localhost:8000)
 */
let API_BASE_URL: string | null = null;

async function fetchApiBaseUrl(): Promise<string> {
  // If already fetched, return cached value
  if (API_BASE_URL) {
    return API_BASE_URL;
  }

  try {
    // Try to fetch from deployment config endpoint
    const response = await fetch('/api/config');
    if (response.ok) {
      const config = await response.json() as { apiBaseUrl: string | null };
      if (config.apiBaseUrl) {
        API_BASE_URL = config.apiBaseUrl;
        return API_BASE_URL;
      }
    }
  } catch {
    // Endpoint might not exist or network error, continue to fallback
  }

  // Fallback to auto-detection
  return getApiBaseUrlFallback();
}

function getApiBaseUrlFallback(): string {
  // 1. Manual override via global variable
  if (typeof window !== 'undefined' && (window as any).CLOUDGATE_API_URL) {
    const url = (window as any).CLOUDGATE_API_URL as string;
    API_BASE_URL = url;
    return url;
  }

  // 2. Production: use current origin (works for same-domain deployments)
  if (typeof window !== 'undefined' && window.location.hostname !== 'localhost') {
    const url = window.location.origin;
    API_BASE_URL = url;
    return url;
  }

  // 3. Development fallback
  const url = 'http://localhost:8000';
  API_BASE_URL = url;
  return url;
}

/**
 * CSRF Token Management
 */

// CSRF token cache
let cachedCsrfToken: string | null = null;

/**
 * Get CSRF token from server (cached)
 */
export async function getCsrfToken(): Promise<string> {
  if (cachedCsrfToken) {
    return cachedCsrfToken;
  }

  try {
    // First try to get from meta tag if server provides it
    const metaTag = document.querySelector('meta[name="csrf-token"]');
    if (metaTag) {
      const token = metaTag.getAttribute('content');
      if (token) {
        cachedCsrfToken = token;
        return token;
      }
    }

    // Fallback: fetch from endpoint (if backend provides one)
    const baseUrl = await fetchApiBaseUrl();
    const response = await fetch(`${baseUrl}/api/csrf-token`, {
      method: 'GET',
      credentials: 'include', // Include cookies if using session-based CSRF
    });

    if (response.ok) {
      const data = await response.json() as { token: string };
      cachedCsrfToken = data.token;
      return data.token;
    }

    // If no CSRF endpoint, return empty string (backend may not require CSRF)
    return '';
  } catch {
    return '';
  }
}

/**
 * Clear cached CSRF token (call after logout)
 */
export function clearCsrfToken(): void {
  cachedCsrfToken = null;
}

/**
 * Fetch wrapper with error handling
 */
export async function apiCall<T>(
  endpoint: string,
  options: RequestInit = {}
): Promise<ApiResponse<T>> {
  try {
    const baseUrl = await fetchApiBaseUrl();
    const url = `${baseUrl}${endpoint}`;
    const headers: Record<string, string> = {
      'Content-Type': 'application/json',
      ...(options.headers as Record<string, string> || {}),
    };

    // Add CSRF token for state-changing requests (POST, PUT, DELETE, PATCH)
    const method = (options.method || 'GET').toUpperCase();
    if (['POST', 'PUT', 'DELETE', 'PATCH'].includes(method)) {
      const csrfToken = await getCsrfToken();
      if (csrfToken) {
        headers['X-CSRF-Token'] = csrfToken;
      }
    }

    const response = await fetch(url, {
      ...options,
      headers,
    });

    const data = await response.json();

    if (!response.ok) {
      return {
        success: false,
        error: {
          detail: data.detail || 'An error occurred',
          status: response.status,
        },
      };
    }

    return {
      success: true,
      data,
    };
  } catch (error) {
    return {
      success: false,
      error: {
        detail: error instanceof Error ? error.message : 'Network error',
        status: 0,
      },
    };
  }
}

/**
 * Get auth token from localStorage
 */
export function getAuthToken(): string | null {
  return localStorage.getItem('access_token');
}

/**
 * Set auth tokens in localStorage
 */
export function setAuthTokens(accessToken: string, refreshToken: string): void {
  localStorage.setItem('access_token', accessToken);
  localStorage.setItem('refresh_token', refreshToken);
}

/**
 * Clear auth tokens from localStorage
 */
export function clearAuthTokens(): void {
  localStorage.removeItem('access_token');
  localStorage.removeItem('refresh_token');
}

/**
 * Get form data from form element
 */
export function getFormData(form: HTMLFormElement): FormData {
  const formData = new FormData(form);
  const data: FormData = {};

  formData.forEach((value, key) => {
    data[key] = value.toString();
  });

  return data;
}

/**
 * Copy text to clipboard
 */
export async function copyToClipboard(text: string): Promise<boolean> {
  try {
    await navigator.clipboard.writeText(text);
    return true;
  } catch (error) {
    // Fallback for older browsers
    const textarea = document.createElement('textarea');
    textarea.value = text;
    document.body.appendChild(textarea);
    textarea.select();
    const success = document.execCommand('copy');
    document.body.removeChild(textarea);
    return success;
  }
}

/**
 * Debounce function
 */
export function debounce<T extends (...args: unknown[]) => unknown>(
  func: T,
  wait: number
): (...args: Parameters<T>) => void {
  let timeout: number;

  return function executedFunction(...args: Parameters<T>) {
    const later = () => {
      clearTimeout(timeout);
      func(...args);
    };

    clearTimeout(timeout);
    timeout = setTimeout(later, wait);
  };
}

/**
 * Validate email
 */
export function validateEmail(email: string): boolean {
  const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
  return emailRegex.test(email);
}

/**
 * Validate password strength
 */
export function validatePassword(password: string): {
  isValid: boolean;
  requirements: {
    length: boolean;
    uppercase: boolean;
    lowercase: boolean;
    number: boolean;
    special: boolean;
  };
} {
  return {
    isValid:
      password.length >= 8 &&
      /[A-Z]/.test(password) &&
      /[a-z]/.test(password) &&
      /\d/.test(password) &&
      /[!@#$%^&*(),.?":{}|<>]/.test(password),
    requirements: {
      length: password.length >= 8,
      uppercase: /[A-Z]/.test(password),
      lowercase: /[a-z]/.test(password),
      number: /\d/.test(password),
      special: /[!@#$%^&*(),.?":{}|<>]/.test(password),
    },
  };
}

/**
 * Sanitize HTML input to prevent XSS
 */
export function sanitizeHtml(input: string): string {
  const div = document.createElement('div');
  div.textContent = input;
  return div.innerHTML;
}

/**
 * Sanitize form data to prevent XSS
 */
export function sanitizeFormData(data: Record<string, unknown>): Record<string, unknown> {
  const sanitized: Record<string, unknown> = {};

  for (const [key, value] of Object.entries(data)) {
    if (typeof value === 'string') {
      sanitized[key] = sanitizeHtml(value);
    } else {
      sanitized[key] = value;
    }
  }

  return sanitized;
}

/**
 * Format date
 */
export function formatDate(date: Date): string {
  return new Intl.DateTimeFormat('en-US', {
    year: 'numeric',
    month: 'short',
    day: 'numeric',
  }).format(date);
}

/**
 * Load template HTML
 */
export async function loadTemplate(path: string): Promise<string> {
  const response = await fetch(path);
  if (!response.ok) {
    throw new Error(`Failed to load template: ${path}`);
  }
  return response.text();
}
