import { Injectable } from '@angular/core';
import { Observable, Subject } from 'rxjs';

/**
 * Broadcast service that lets any component open the AI chat panel
 * with an optional pre-filled query that auto-submits immediately.
 * Used by the Real Estate header nav item (and any future trigger points).
 */
@Injectable({ providedIn: 'root' })
export class AiChatService {
  private openWithQuery$ = new Subject<string>();

  public get openWithQuery(): Observable<string> {
    return this.openWithQuery$.asObservable();
  }

  public openChat(query: string): void {
    this.openWithQuery$.next(query);
  }
}
