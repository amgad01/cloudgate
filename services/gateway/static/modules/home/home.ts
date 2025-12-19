/**
 * Home Page Module
 * Main landing page with navigation and user info display
 */

import { API } from '../../shared/components/api';
import { BasePage } from '../../shared/components/base-page';

class HomePage extends BasePage {
    async init(): Promise<void> {
        this.initLayout({
            header: { title: 'CloudGate API Gateway', subtitle: 'Secure API Access & Management' },
            footer: { yearElementId: 'current-year' },
            messagesContainerId: 'messages-container',
        });
        this.setupNavigation();
        this.displayUserInfo();
    }

    private setupNavigation(): void {
        const logoutBtn = this.getElementById('logout-btn');
        if (logoutBtn) {
            logoutBtn.addEventListener('click', async () => {
                await this.handleLogout();
            });
        }

        const profileBtn = this.getElementById('profile-btn');
        if (profileBtn) {
            profileBtn.addEventListener('click', () => {
                this.handleProfileView();
            });
        }
    }

    private async displayUserInfo(): Promise<void> {
        const userInfo = this.getElementById('user-info');
        const authActions = this.getElementById('auth-actions');
        const userActions = this.getElementById('user-actions');
        const userMessage = this.getElementById('user-message');
        const logoutBtn = this.getElementById('logout-btn');

        if (!API.isAuthenticated()) {
            // Show login/register buttons
            if (authActions) authActions.style.display = 'flex';
            this.hideElement(userActions);
        } else {
            // Show user info and logout button
            this.hideElement(authActions);
            this.showElement(userActions);
            this.showElement(logoutBtn);

            const user = API.getStoredUser();
            if (user && userInfo) {
                userInfo.innerHTML = `
          <div class="user-profile">
            <span class="user-name">${user.first_name} ${user.last_name}</span>
            <span class="user-email">${user.email}</span>
          </div>
        `;
            }

            if (userMessage) {
                userMessage.textContent = `Welcome back, ${user?.first_name}!`;
            }

            // Try to fetch full profile
            await this.fetchUserProfile();
        }
    }

    private async fetchUserProfile(): Promise<void> {
        const response = await API.getProfile();

        if (!response.success) {
            console.warn('Failed to fetch profile:', response.error);

            // Token might be expired, try to refresh
            const refreshResponse = await API.refreshToken();
            if (refreshResponse.success && refreshResponse.data) {
                API.storeAuthData(refreshResponse.data);
                this.showSuccess('Token refreshed', 2000);
            } else {
                // Logout if refresh fails
                await this.handleLogout();
            }
        }
    }

    private async handleLogout(): Promise<void> {
        try {
            await API.logout();
            this.showSuccess('Logged out successfully!', 2000);

            // Reload page after logout
            setTimeout(() => {
                window.location.reload();
            }, 2000);
        } catch (error) {
            this.showError('Failed to logout', 3000);
        }
    }

    private handleProfileView(): void {
        const user = API.getStoredUser();
        if (user) {
            const profileInfo = `
        <strong>User Profile</strong><br>
        Name: ${user.first_name} ${user.last_name}<br>
        Email: ${user.email}<br>
        ID: ${user.id}
      `;

            this.showInfo(profileInfo, 5000);
        }
    }
}

// Initialize when DOM is ready
document.addEventListener('DOMContentLoaded', async () => {
    const page = new HomePage();
    await page.init();
});
