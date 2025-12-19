/**
 * CloudGate API Gateway - Shared Types
 * Centralized type definitions for the UI
 */

// API Response Types
export interface User {
  id: string;
  email: string;
  first_name: string;
  last_name: string;
}

export interface AuthResponse {
  access_token: string;
  refresh_token: string;
  user: User;
}

export interface ApiError {
  detail: string | string[];
  status: number;
}

export interface ApiResponse<T> {
  data?: T;
  error?: ApiError;
  success: boolean;
}

// Form Types
export type FormData = Record<string, string>;

// Message Types
export type MessageType = 'success' | 'error' | 'info' | 'warning';

export interface Message {
  type: MessageType;
  text: string;
  duration?: number;
}

// Component Types
export interface ComponentConfig {
  element?: HTMLElement;
  id?: string;
  className?: string;
}

export interface ButtonConfig extends ComponentConfig {
  text: string;
  onClick?: (event: MouseEvent) => void;
  disabled?: boolean;
  variant?: 'primary' | 'secondary' | 'danger';
}

export interface FormConfig extends ComponentConfig {
  onSubmit: (data: FormData) => Promise<void>;
  fields: FormField[];
}

export interface FormField {
  name: string;
  type: 'text' | 'email' | 'password' | 'number' | 'textarea';
  label: string;
  placeholder?: string;
  required?: boolean;
  validation?: (value: string) => boolean | string;
}

export interface MessageComponentConfig extends ComponentConfig {
  message: Message;
  onClose?: () => void;
}
