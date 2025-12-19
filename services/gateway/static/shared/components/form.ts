/**
 * Form Component
 * Reusable form builder with built-in validation support
 */

import type { FormConfig, FormField, FormData } from '../types';
import { sanitizeFormData } from '../utils';

export class Form {
    private element: HTMLFormElement | null = null;
    private fields: Map<string, HTMLElement> = new Map();
    private config: FormConfig;

    constructor(config: FormConfig) {
        this.config = config;
        this.createElement();
    }

    private createElement(): void {
        this.element = document.createElement('form');
        this.element.id = this.config.id || '';
        this.element.className = this.config.className || '';
        this.element.noValidate = true; // Use custom validation

        // Create form fields
        this.config.fields.forEach((field) => {
            const fieldElement = this.createField(field);
            this.fields.set(field.name, fieldElement);
            this.element!.appendChild(fieldElement);
        });

        // Create submit button
        const submitButton = document.createElement('button');
        submitButton.type = 'submit';
        submitButton.className = 'btn btn-primary';
        submitButton.textContent = 'Submit';
        this.element.appendChild(submitButton);

        // Handle form submission
        this.element.addEventListener('submit', async (e) => {
            e.preventDefault();
            await this.handleSubmit();
        });
    }

    private createField(field: FormField): HTMLElement {
        const wrapper = document.createElement('div');
        wrapper.className = 'form-field';

        // Label
        const label = document.createElement('label');
        label.htmlFor = field.name;
        label.textContent = field.label;
        if (field.required) {
            const required = document.createElement('span');
            required.className = 'required';
            required.textContent = ' *';
            label.appendChild(required);
        }
        wrapper.appendChild(label);

        // Input or textarea
        let input: HTMLInputElement | HTMLTextAreaElement;
        if (field.type === 'textarea') {
            input = document.createElement('textarea');
            input.rows = 4;
        } else {
            input = document.createElement('input');
            input.type = field.type;
        }

        input.id = field.name;
        input.name = field.name;
        input.placeholder = field.placeholder || '';
        input.required = field.required || false;
        input.className = 'form-input';

        wrapper.appendChild(input);

        // Error message container
        const error = document.createElement('div');
        error.className = 'form-error';
        error.id = `${field.name}-error`;
        error.style.display = 'none';
        wrapper.appendChild(error);

        // Add blur validation
        if (field.validation) {
            input.addEventListener('blur', () => {
                this.validateField(field, input.value);
            });

            input.addEventListener('input', () => {
                // Clear error on input
                error.style.display = 'none';
            });
        }

        return wrapper;
    }

    private validateField(field: FormField, value: string): boolean {
        const error = this.element?.querySelector(`#${field.name}-error`) as HTMLElement;

        if (!error) return true;

        // Check required
        if (field.required && !value.trim()) {
            error.textContent = `${field.label} is required`;
            error.style.display = 'block';
            return false;
        }

        // Custom validation
        if (field.validation) {
            const result = field.validation(value);
            if (result !== true) {
                error.textContent = typeof result === 'string' ? result : 'Invalid value';
                error.style.display = 'block';
                return false;
            }
        }

        error.style.display = 'none';
        return true;
    }

    private async handleSubmit(): Promise<void> {
        if (!this.element) return;

        // Validate all fields
        let isValid = true;
        for (const field of this.config.fields) {
            const input = this.element.querySelector(`#${field.name}`) as HTMLInputElement;
            if (!input) continue;

            if (!this.validateField(field, input.value)) {
                isValid = false;
            }
        }

        if (!isValid) return;

        // Collect form data
        const formData = new FormData(this.element);
        const data: FormData = {};

        formData.forEach((value, key) => {
            data[key] = value.toString();
        });

        // Sanitize data to prevent XSS
        const sanitizedData = sanitizeFormData(data) as FormData;

        // Call submit handler with sanitized data
        if (this.config.onSubmit) {
            await this.config.onSubmit(sanitizedData);
        }
    }

    public mount(container: HTMLElement | string): void {
        const targetElement =
            typeof container === 'string'
                ? document.querySelector(container)
                : container;

        if (targetElement && this.element) {
            targetElement.appendChild(this.element);
        }
    }

    public getFieldValue(fieldName: string): string {
        const input = this.element?.querySelector(`#${fieldName}`) as HTMLInputElement;
        return input ? input.value : '';
    }

    public setFieldValue(fieldName: string, value: string): void {
        const input = this.element?.querySelector(`#${fieldName}`) as HTMLInputElement;
        if (input) {
            input.value = value;
        }
    }

    public reset(): void {
        this.element?.reset();

        // Clear all error messages
        this.element?.querySelectorAll('.form-error').forEach((error) => {
            (error as HTMLElement).style.display = 'none';
        });
    }

    public setFormDisabled(disabled: boolean): void {
        if (!this.element) return;

        const inputs = this.element.querySelectorAll('input, textarea, button');
        inputs.forEach((input) => {
            (input as HTMLInputElement | HTMLButtonElement).disabled = disabled;
        });
    }
}
