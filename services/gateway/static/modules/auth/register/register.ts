/**
 * Register Page Module
 * Handles user registration with form validation and API integration
 */

import { API } from '../../../shared/components/api';
import { registerFields } from '../../../shared/utils/form-fields';
import { AuthPage, AuthLayoutOptions } from '../auth-page';
import type { ApiResponse, AuthResponse, FormData, FormField } from '../../../shared/types';

class RegisterPage extends AuthPage {
    protected getLayoutOptions(): AuthLayoutOptions {
        return {
            header: {
                title: 'CloudGate API Gateway',
                subtitle: 'User Registration',
            },
            footer: { yearElementId: 'current-year' },
            messagesContainerId: 'messages-container',
        };
    }

    protected getFormFields(): FormField[] {
        return registerFields;
    }

    protected decorateFields(fields: FormField[]): FormField[] {
        return fields.map((field) => {
            if (field.name === 'password_confirm') {
                return {
                    ...field,
                    validation: (value: string) => {
                        const password = this.form?.getFieldValue('password') || '';
                        if (value !== password) {
                            return 'Passwords do not match';
                        }
                        return true;
                    },
                };
            }

            return { ...field };
        });
    }

    protected createAction(data: FormData): Promise<ApiResponse<AuthResponse>> {
        return API.register(
            data.email!,
            data.password!,
            data.first_name!,
            data.last_name!
        );
    }

    protected getSuccessMessage(): string {
        return 'Registration successful! Redirecting...';
    }

    protected getDefaultErrorMessage(): string {
        return 'Registration failed';
    }
}

// Initialize when DOM is ready
document.addEventListener('DOMContentLoaded', async () => {
    const page = new RegisterPage();
    await page.init();
});
