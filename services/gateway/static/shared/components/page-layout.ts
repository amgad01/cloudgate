import { HeaderComponent } from './header';
import { FooterComponent } from './footer';

interface LayoutOptions {
    header?: { title: string; subtitle?: string | undefined };
    footer?: { yearElementId?: string | undefined };
    messagesContainerId?: string | undefined;
}

export class PageLayout {
    private readonly opts: LayoutOptions;
    constructor(opts: LayoutOptions) {
        this.opts = opts;
    }

    init(): void {
        this.mountHeader();
        this.mountFooter();
    }

    private mountHeader(): void {
        if (!this.opts.header) return;
        const container = document.querySelector('.container') as HTMLElement | null;
        new HeaderComponent(this.opts.header.title, this.opts.header.subtitle).mount(container);
    }

    private mountFooter(): void {
        const container = document;
        const yearElementId: string | undefined = this.opts.footer?.yearElementId;
        new FooterComponent({ yearElementId }).mount(container);
    }

    getMessagesContainer(): HTMLElement | null {
        if (!this.opts.messagesContainerId) return null;
        return document.getElementById(this.opts.messagesContainerId);
    }
}
