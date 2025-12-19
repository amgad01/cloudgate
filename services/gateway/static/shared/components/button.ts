/**
 * Button Component
 * Reusable button with multiple variants and states
 */

import type { ButtonConfig } from '../types';

export class Button {
  private element: HTMLButtonElement;
  private config: ButtonConfig;

  constructor(config: ButtonConfig) {
    this.config = config;
    this.element = document.createElement('button');
    this.setup();
  }

  private setup(): void {
    this.element.textContent = this.config.text;
    this.element.className = `btn btn--${this.config.variant || 'primary'}`;

    if (this.config.id) {
      this.element.id = this.config.id;
    }

    if (this.config.className) {
      this.element.classList.add(this.config.className);
    }

    if (this.config.disabled) {
      this.element.disabled = true;
    }

    if (this.config.onClick) {
      this.element.addEventListener('click', this.config.onClick);
    }
  }

  public getElement(): HTMLButtonElement {
    return this.element;
  }

  public setText(text: string): void {
    this.element.textContent = text;
  }

  public setDisabled(disabled: boolean): void {
    this.element.disabled = disabled;
  }

  public setLoading(loading: boolean): void {
    if (loading) {
      this.element.disabled = true;
      this.element.innerHTML = '<span class="spinner"></span> Loading...';
      this.element.classList.add('btn--loading');
    } else {
      this.element.disabled = this.config.disabled || false;
      this.element.textContent = this.config.text;
      this.element.classList.remove('btn--loading');
    }
  }

  public onClick(callback: (event: MouseEvent) => void): void {
    this.element.addEventListener('click', callback);
  }

  public mount(parent: HTMLElement | string): void {
    const container =
      typeof parent === 'string' ? document.querySelector(parent) : parent;
    if (container) {
      container.appendChild(this.element);
    }
  }
}
