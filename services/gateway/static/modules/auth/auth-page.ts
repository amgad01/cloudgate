import { Form } from '../../shared/components/form';
import { BasePage } from '../../shared/components/base-page';
import { executeAuthFlow } from '../../shared/utils/auth-flow';
import type { AuthFlowOptions } from '../../shared/utils/auth-flow';

import type { ApiResponse, AuthResponse, FormData, FormField } from '../../shared/types';

export interface AuthLayoutOptions {
    header: {
        title: string;
        subtitle?: string;
    };
    footer?: {
        yearElementId?: string;
    };
    messagesContainerId?: string;
}

export abstract class AuthPage extends BasePage {
    protected form: Form | null = null;

    public async init(): Promise<void> {
        this.initLayout(this.getLayoutOptions());
        this.afterLayout();
        this.setupForm();
    }

    protected abstract getLayoutOptions(): AuthLayoutOptions;

    protected abstract getFormFields(): FormField[];

    protected abstract createAction(data: FormData): Promise<ApiResponse<AuthResponse>>;

    protected abstract getSuccessMessage(): string;

    protected getDefaultErrorMessage(): string | undefined {
        return undefined;
    }

    protected getMessageDuration(): number {
        return 2000;
    }

    protected getRedirectDelay(): number {
        return 2000;
    }

    protected getFormId(): string {
        return 'auth-form';
    }

    protected getFormClassName(): string {
        return 'auth-form';
    }

    protected getFormContainerId(): string {
        return 'form-container';
    }

    protected decorateFields(fields: FormField[]): FormField[] {
        return fields.map((field) => ({ ...field }));
    }

    protected afterLayout(): void {
        // Override to perform work before the form renders
    }

    protected onAuthSuccess?(response: AuthResponse): Promise<void> | void;

    protected onRedirect?(): void;

    private setupForm(): void {
        const fields = this.decorateFields(this.getFormFields());

        this.form = new Form({
            id: this.getFormId(),
            className: this.getFormClassName(),
            fields,
            onSubmit: async (data: FormData) => {
                const defaultErrorMessage = this.getDefaultErrorMessage();
                const onSuccess = this.onAuthSuccess?.bind(this);
                const onRedirect = this.onRedirect?.bind(this);

                const flowOptions: AuthFlowOptions = {
                    form: this.form,
                    action: (formData: FormData) => this.createAction(formData),
                    successMessage: this.getSuccessMessage(),
                    messageDuration: this.getMessageDuration(),
                    redirectDelay: this.getRedirectDelay(),
                    showSuccess: (message, duration) =>
                        this.showSuccess(message, duration),
                    showError: (message) => this.showError(message),
                };

                if (defaultErrorMessage !== undefined) {
                    flowOptions.defaultErrorMessage = defaultErrorMessage;
                }

                if (onSuccess) {
                    flowOptions.onSuccess = onSuccess;
                }

                if (onRedirect) {
                    flowOptions.onRedirect = onRedirect;
                }

                await executeAuthFlow(flowOptions, data);
            },
        });

        const container = this.getElementById(this.getFormContainerId());
        if (container && this.form) {
            this.form.mount(container);
        }
    }
}
