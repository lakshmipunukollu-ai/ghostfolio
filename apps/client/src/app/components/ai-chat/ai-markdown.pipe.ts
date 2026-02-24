import { Pipe, PipeTransform } from '@angular/core';
import { DomSanitizer, SafeHtml } from '@angular/platform-browser';

/**
 * Minimal Markdown-to-HTML pipe for chat messages.
 * Handles: bold, inline code, bullet lists, line breaks, horizontal rules.
 * Does NOT use an external library to keep the bundle lean.
 */
@Pipe({
  name: 'aiMarkdown',
  standalone: true
})
export class AiMarkdownPipe implements PipeTransform {
  public constructor(private sanitizer: DomSanitizer) {}

  public transform(value: string): SafeHtml {
    if (!value) {
      return '';
    }

    let html = value
      // Escape HTML entities
      .replace(/&/g, '&amp;')
      .replace(/</g, '&lt;')
      .replace(/>/g, '&gt;')
      // Bold **text** or __text__
      .replace(/\*\*(.+?)\*\*/g, '<strong>$1</strong>')
      .replace(/__(.+?)__/g, '<strong>$1</strong>')
      // Inline code `code`
      .replace(/`([^`]+)`/g, '<code>$1</code>')
      // Horizontal rule ---
      .replace(/^---+$/gm, '<hr>')
      // Bullet lines starting with "- " or "* "
      .replace(/^[*\-] (.+)$/gm, '<li>$1</li>')
      // Wrap consecutive <li> in <ul>
      .replace(/(<li>.*<\/li>(\n|$))+/g, (block) => `<ul>${block}</ul>`)
      // Newlines → <br> (except inside <ul>)
      .replace(/\n/g, '<br>');

    // Cleanup: remove <br> immediately before/after block elements
    html = html
      .replace(/<br>\s*(<\/?(?:ul|li|hr))/g, '$1')
      .replace(/(<\/(?:ul|li)>)\s*<br>/g, '$1');

    return this.sanitizer.bypassSecurityTrustHtml(html);
  }
}
