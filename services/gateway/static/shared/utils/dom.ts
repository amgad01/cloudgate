export function setText(el: HTMLElement | null, text: string): void {
    if (el) el.textContent = text;
}

export function on(el: HTMLElement | null, event: string, handler: (e: Event) => void): void {
    if (el) el.addEventListener(event, handler);
}

export function qs<T extends Element = Element>(selector: string, root: Document | HTMLElement = document): T | null {
    return root.querySelector(selector) as T | null;
}
