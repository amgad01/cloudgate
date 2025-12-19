export class HeaderComponent {
    private readonly title: string;
    private readonly subtitle: string | undefined;

    constructor(title: string, subtitle?: string | undefined) {
        this.title = title;
        this.subtitle = subtitle;
    }

    mount(container: HTMLElement | null): void {
        if (!container) return;
        const header = container.querySelector('.header');
        const titleEl = header?.querySelector('.header__title');
        const subtitleEl = header?.querySelector('.header__subtitle');

        if (titleEl) titleEl.textContent = this.title;
        if (subtitleEl && typeof this.subtitle === 'string') {
            subtitleEl.textContent = this.subtitle;
        }
    }
}
