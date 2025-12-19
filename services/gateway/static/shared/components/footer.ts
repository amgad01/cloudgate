export class FooterComponent {
    private readonly yearElementId: string;

    constructor(options?: { yearElementId?: string | undefined }) {
        this.yearElementId = options?.yearElementId ?? 'current-year';
    }

    mount(container: HTMLElement | Document = document): void {
        const yearElement = (container as Document).getElementById
            ? (container as Document).getElementById(this.yearElementId)
            : (container as HTMLElement).querySelector(`#${this.yearElementId}`);

        if (yearElement) {
            yearElement.textContent = new Date().getFullYear().toString();
        }
    }
}
