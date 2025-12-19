import { PageLayout } from './page-layout';
import { MessageComponent } from './message';
import type { Message } from '../types';

export abstract class BasePage {
    protected layout: PageLayout | null = null;

    protected initLayout(opts: {
        header?: { title: string; subtitle?: string | undefined };
        footer?: { yearElementId?: string | undefined };
        messagesContainerId?: string | undefined;
    }): void {
        this.layout = new PageLayout(opts);
        this.layout.init();
    }

    protected getElementById<T extends HTMLElement = HTMLElement>(id: string): T | null {
        return document.getElementById(id) as T | null;
    }

    protected getElement<T extends HTMLElement = HTMLElement>(selector: string): T | null {
        return document.querySelector(selector) as T | null;
    }

    protected showElement(element: HTMLElement | null): void {
        if (element) {
            element.style.display = element.tagName === 'DIV' ? 'block' : '';
        }
    }

    protected hideElement(element: HTMLElement | null): void {
        if (element) {
            element.style.display = 'none';
        }
    }

    /**
     * Show a message using the messages container
     */
    protected showMessage(
        type: Message['type'],
        text: string,
        duration?: number
    ): void {
        const container = this.layout?.getMessagesContainer();
        if (container) {
            const message: Message = { type, text };
            if (duration !== undefined) {
                message.duration = duration;
            }
            MessageComponent.show(message, container);
        }
    }

    /**
     * Show success message
     */
    protected showSuccess(text: string, duration: number = 3000): void {
        this.showMessage('success', text, duration);
    }

    /**
     * Show error message
     */
    protected showError(text: string, duration: number = 5000): void {
        this.showMessage('error', text, duration);
    }

    /**
     * Show info message
     */
    protected showInfo(text: string, duration: number = 3000): void {
        this.showMessage('info', text, duration);
    }

    /**
     * Show warning message
     */
    protected showWarning(text: string, duration: number = 4000): void {
        this.showMessage('warning', text, duration);
    }
}
