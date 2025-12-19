/**
 * Login Page Module
 * Handles user authentication with form and API integration
 */

import { API } from '../../../shared/components/api';
import { loginFields } from '../../../shared/utils/form-fields';
import { copyToClipboard } from '../../../shared/utils';
import { AuthPage, AuthLayoutOptions } from '../auth-page';
import type { ApiResponse, AuthResponse, FormData, FormField } from '../../../shared/types';

class LoginPage extends AuthPage {
    protected getLayoutOptions(): AuthLayoutOptions {
        return {
            header: { title: 'CloudGate API Gateway', subtitle: 'User Login' },
            footer: { yearElementId: 'current-year' },
            messagesContainerId: 'messages-container',
        };
    }

    protected getFormFields(): FormField[] {
        return loginFields;
    }

    protected createAction(data: FormData): Promise<ApiResponse<AuthResponse>> {
        return API.login(data.email!, data.password!);
    }

    protected getSuccessMessage(): string {
        return 'Login successful! Redirecting...';
    }

    protected getDefaultErrorMessage(): string {
        return 'Login failed';
    }

    protected afterLayout(): void {
        this.checkIfAlreadyLoggedIn();
    }

    protected onAuthSuccess(response: AuthResponse): void {
        this.showTokenInfo(response.access_token);
    }

    private checkIfAlreadyLoggedIn(): void {
        if (API.isAuthenticated()) {
            const user = API.getStoredUser();
            if (user) {
                this.showInfo(`Already logged in as ${user.email}. Redirecting...`, 2000);
                setTimeout(() => {
                    API.redirectToHome();
                }, 2000);
            }
        }
    }

    private showTokenInfo(token: string): void {
        const tokenInfo = this.getElementById('token-info');
        const tokenValue = this.getElementById('token-value');
        const copyBtn = this.getElementById('copy-token');

        if (tokenInfo && tokenValue && copyBtn) {
            tokenValue.textContent = token;
            tokenInfo.style.display = 'block';

            copyBtn.addEventListener('click', async () => {
                const success = await copyToClipboard(token);
                if (success) {
                    this.showSuccess('Token copied to clipboard!', 2000);
                } else {
                    this.showError('Failed to copy token', 3000);
                }
            });
        }
    }
}

// Initialize when DOM is ready
document.addEventListener('DOMContentLoaded', async () => {
    const page = new LoginPage();
    await page.init();
});
