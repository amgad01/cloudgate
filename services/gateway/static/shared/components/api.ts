/**
 * API Component
 * Wrapper around API utilities for cleaner usage in components
 */

import { apiCall, getAuthToken, setAuthTokens } from '../utils';
import type { ApiResponse, AuthResponse, User } from '../types';

export class API {
    /**
     * Register a new user
     */
    static async register(email: string, password: string, firstName: string, lastName: string): Promise<ApiResponse<AuthResponse>> {
        return apiCall<AuthResponse>('/api/auth/register', {
            method: 'POST',
            body: JSON.stringify({
                email,
                password,
                first_name: firstName,
                last_name: lastName,
            }),
        });
    }

    /**
     * Login user
     */
    static async login(
        email: string,
        password: string
    ): Promise<ApiResponse<AuthResponse>> {
        return apiCall<AuthResponse>('/api/auth/login', {
            method: 'POST',
            body: JSON.stringify({
                email,
                password,
            }),
        });
    }

    /**
     * Get current user profile
     */
    static async getProfile(): Promise<ApiResponse<User>> {
        const token = getAuthToken();
        if (!token) {
            return {
                success: false,
                error: { detail: 'Not authenticated', status: 401 },
            };
        }

        return apiCall<User>('/api/auth/profile', {
            headers: {
                Authorization: `Bearer ${token}`,
            },
        });
    }

    /**
     * Refresh access token
     */
    static async refreshToken(
        refreshToken?: string
    ): Promise<ApiResponse<AuthResponse>> {
        const token = refreshToken || localStorage.getItem('refresh_token');

        if (!token) {
            return {
                success: false,
                error: { detail: 'No refresh token available', status: 401 },
            };
        }

        return apiCall<AuthResponse>('/api/auth/refresh', {
            method: 'POST',
            body: JSON.stringify({ refresh_token: token }),
        });
    }

    /**
     * Logout user
     */
    static async logout(): Promise<void> {
        localStorage.removeItem('access_token');
        localStorage.removeItem('refresh_token');
        localStorage.removeItem('user');
    }

    /**
     * Check if user is authenticated
     */
    static isAuthenticated(): boolean {
        return !!getAuthToken();
    }

    /**
     * Store auth tokens and user info
     */
    static storeAuthData(response: AuthResponse): void {
        setAuthTokens(response.access_token, response.refresh_token);
        localStorage.setItem('user', JSON.stringify(response.user));
    }

    /**
     * Get stored user info
     */
    static getStoredUser(): any {
        const user = localStorage.getItem('user');
        return user ? JSON.parse(user) : null;
    }

    /**
     * Redirect to login
     */
    static redirectToLogin(): void {
        window.location.href = '/modules/auth/login/';
    }

    /**
     * Redirect to home
     */
    static redirectToHome(): void {
        window.location.href = '/modules/home/';
    }
}
