/**
 * Common Form Field Definitions
 * Centralize field configurations and validation patterns
 */

import type { FormField } from '../types';
import { validateEmail, validatePassword } from '../utils';

export const loginFields: FormField[] = [
    {
        name: 'email',
        type: 'email',
        label: 'Email Address',
        placeholder: 'Enter your email',
        required: true,
        validation: (value) => {
            if (!validateEmail(value)) {
                return 'Please enter a valid email address';
            }
            return true;
        },
    },
    {
        name: 'password',
        type: 'password',
        label: 'Password',
        placeholder: 'Enter your password',
        required: true,
        validation: (value) => {
            if (value.length < 1) {
                return 'Password is required';
            }
            return true;
        },
    },
];

export const registerFields: FormField[] = [
    {
        name: 'first_name',
        type: 'text',
        label: 'First Name',
        placeholder: 'Enter your first name',
        required: true,
        validation: (value) => {
            if (value.trim().length < 2) {
                return 'First name must be at least 2 characters';
            }
            return true;
        },
    },
    {
        name: 'last_name',
        type: 'text',
        label: 'Last Name',
        placeholder: 'Enter your last name',
        required: true,
        validation: (value) => {
            if (value.trim().length < 2) {
                return 'Last name must be at least 2 characters';
            }
            return true;
        },
    },
    {
        name: 'email',
        type: 'email',
        label: 'Email Address',
        placeholder: 'Enter your email',
        required: true,
        validation: (value) => {
            if (!validateEmail(value)) {
                return 'Please enter a valid email address';
            }
            return true;
        },
    },
    {
        name: 'password',
        type: 'password',
        label: 'Password',
        placeholder: 'Create a strong password',
        required: true,
        validation: (value) => {
            const validation = validatePassword(value);
            if (!validation.isValid) {
                const requirements = [];
                if (!validation.requirements.length) requirements.push('at least 8 characters');
                if (!validation.requirements.uppercase) requirements.push('one uppercase letter');
                if (!validation.requirements.lowercase) requirements.push('one lowercase letter');
                if (!validation.requirements.number) requirements.push('one number');
                if (!validation.requirements.special) requirements.push('one special character');
                return `Password must contain: ${requirements.join(', ')}`;
            }
            return true;
        },
    },
    {
        name: 'password_confirm',
        type: 'password',
        label: 'Confirm Password',
        placeholder: 'Re-enter your password',
        required: true,
        validation: (value) => {
            // This will be extended in the module to check against the password field
            if (!value) {
                return 'Please confirm your password';
            }
            return true;
        },
    },
];
