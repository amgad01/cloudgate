import { API } from '../components/api';
import { handleApiResponse } from './api-error';

import type { Form } from '../components/form';
import type { ApiResponse, AuthResponse, FormData } from '../types';

export interface AuthFlowOptions {
    form: Form | null;
    action: (data: FormData) => Promise<ApiResponse<AuthResponse>>;
    successMessage: string;
    defaultErrorMessage?: string;
    messageDuration?: number;
    redirectDelay?: number;
    showError: (message: string) => void;
    showSuccess: (message: string, duration?: number) => void;
    onSuccess?: (response: AuthResponse) => Promise<void> | void;
    onRedirect?: () => void;
}

export async function executeAuthFlow(
    options: AuthFlowOptions,
    data: FormData
): Promise<void> {
    options.form?.setFormDisabled(true);

    try {
        const response = await options.action(data);
        const authData = await handleApiResponse(
            response,
            options.showError,
            options.defaultErrorMessage ?? options.successMessage
        );

        if (!authData) {
            return;
        }

        API.storeAuthData(authData);
        options.showSuccess(
            options.successMessage,
            options.messageDuration ?? 2000
        );

        if (options.onSuccess) {
            await options.onSuccess(authData);
        }

        const delay = options.redirectDelay ?? 2000;
        setTimeout(() => {
            if (options.onRedirect) {
                options.onRedirect();
            } else {
                API.redirectToHome();
            }
        }, delay);
    } catch (error) {
        const message =
            error instanceof Error ? error.message : 'An unexpected error occurred';
        options.showError(message);
    } finally {
        options.form?.setFormDisabled(false);
    }
}
