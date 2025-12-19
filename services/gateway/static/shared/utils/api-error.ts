/**
 * API Error Handling Utilities
 * Centralized error message extraction and handling
 */

import type { ApiResponse } from '../types';

/**
 * Extract user-friendly error message from API response
 */
export function getErrorMessage(
    response: ApiResponse<unknown>,
    defaultMessage: string = 'Operation failed'
): string {
    if (!response.error) return defaultMessage;

    const { detail } = response.error;

    if (typeof detail === 'string') {
        return detail;
    }

    if (Array.isArray(detail)) {
        return detail.join(', ');
    }

    return defaultMessage;
}

/**
 * Handle API response with error display
 */
export async function handleApiResponse<T>(
    response: ApiResponse<T>,
    onError?: (message: string) => void,
    defaultErrorMessage: string = 'Operation failed'
): Promise<T | null> {
    if (!response.success || !response.data) {
        const errorMsg = getErrorMessage(response, defaultErrorMessage);
        if (onError) {
            onError(errorMsg);
        }
        return null;
    }

    return response.data;
}
