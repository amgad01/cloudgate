/**
 * Message Component
 * Reusable notification/alert component
 */

import type { Message, MessageComponentConfig } from '../types';

export class MessageComponent {
    private element: HTMLDivElement;
    private config: MessageComponentConfig;
    private closeTimer: number | null = null;

    constructor(config: MessageComponentConfig) {
        this.config = config;
        this.element = document.createElement('div');
        this.setup();
    }

    private setup(): void {
        const message = this.config.message;
        this.element.className = `message message--${message.type}`;

        if (this.config.id) {
            this.element.id = this.config.id;
        }

        if (this.config.className) {
            this.element.classList.add(this.config.className);
        }

        this.element.innerHTML = `
      <div class="message__content">
        <span class="message__icon">${this.getIcon(message.type)}</span>
        <span class="message__text">${message.text}</span>
        <button class="message__close" aria-label="Close message">&times;</button>
      </div>
    `;

        const closeButton = this.element.querySelector('.message__close');
        closeButton?.addEventListener('click', () => this.close());

        if (message.duration) {
            this.closeTimer = setTimeout(() => this.close(), message.duration);
        }
    }

    private getIcon(type: Message['type']): string {
        switch (type) {
            case 'success':
                return '✓';
            case 'error':
                return '✕';
            case 'warning':
                return '⚠';
            case 'info':
            default:
                return 'ℹ';
        }
    }

    public getElement(): HTMLDivElement {
        return this.element;
    }

    public close(): void {
        if (this.closeTimer) {
            clearTimeout(this.closeTimer);
        }

        this.element.classList.add('message--closing');
        setTimeout(() => {
            this.element.remove();
            if (this.config.onClose) {
                this.config.onClose();
            }
        }, 300);
    }

    public mount(parent: HTMLElement | string): void {
        const container =
            typeof parent === 'string' ? document.querySelector(parent) : parent;
        if (container) {
            container.appendChild(this.element);
        }
    }

    public static show(
        message: Message,
        container: HTMLElement | string = 'body'
    ): MessageComponent {
        const component = new MessageComponent({
            message,
            className: 'message--auto-position',
        });
        component.mount(container);
        return component;
    }

    public static success(text: string, duration: number = 3000): MessageComponent {
        return this.show({ type: 'success', text, duration });
    }

    public static error(text: string, duration: number = 5000): MessageComponent {
        return this.show({ type: 'error', text, duration });
    }

    public static warning(text: string, duration: number = 4000): MessageComponent {
        return this.show({ type: 'warning', text, duration });
    }

    public static info(text: string, duration: number = 3000): MessageComponent {
        return this.show({ type: 'info', text, duration });
    }
}
