import {
  ChangeDetectionStrategy,
  ChangeDetectorRef,
  Component,
  ElementRef,
  OnDestroy,
  ViewChild
} from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { HttpClient, HttpClientModule } from '@angular/common/http';

import { AiMarkdownPipe } from './ai-markdown.pipe';

interface ChatMessage {
  role: 'user' | 'assistant';
  content: string;
  toolsUsed?: string[];
  confidence?: number;
  latency?: number;
  feedbackGiven?: 1 | -1 | null;
  isWrite?: boolean;
}

interface AgentResponse {
  response: string;
  confidence_score: number;
  awaiting_confirmation: boolean;
  pending_write: Record<string, unknown> | null;
  tools_used: string[];
  latency_seconds: number;
}

@Component({
  changeDetection: ChangeDetectionStrategy.OnPush,
  imports: [CommonModule, FormsModule, HttpClientModule, AiMarkdownPipe],
  selector: 'gf-ai-chat',
  styleUrls: ['./ai-chat.component.scss'],
  templateUrl: './ai-chat.component.html'
})
export class GfAiChatComponent implements OnDestroy {
  @ViewChild('messagesContainer') private messagesContainer: ElementRef;

  public isOpen = false;
  public isThinking = false;
  public inputValue = '';
  public messages: ChatMessage[] = [];
  public successBanner = '';

  // Write confirmation state
  private pendingWrite: Record<string, unknown> | null = null;
  public awaitingConfirmation = false;

  private readonly AGENT_URL = '/agent/chat';
  private readonly FEEDBACK_URL = '/agent/feedback';

  public constructor(
    private changeDetectorRef: ChangeDetectorRef,
    private http: HttpClient
  ) {}

  public ngOnDestroy() {}

  public togglePanel(): void {
    this.isOpen = !this.isOpen;
    if (this.isOpen && this.messages.length === 0) {
      this.messages.push({
        role: 'assistant',
        content:
          'Hello! I\'m your Portfolio Assistant. Ask me about your portfolio performance, transactions, tax estimates, or use commands like "buy 5 shares of AAPL" to record transactions.'
      });
    }
    this.changeDetectorRef.markForCheck();
    if (this.isOpen) {
      setTimeout(() => this.scrollToBottom(), 50);
    }
  }

  public closePanel(): void {
    this.isOpen = false;
    this.changeDetectorRef.markForCheck();
  }

  public onKeydown(event: KeyboardEvent): void {
    if (event.key === 'Enter' && !event.shiftKey) {
      event.preventDefault();
      this.sendMessage();
    }
  }

  public sendMessage(): void {
    const query = this.inputValue.trim();
    if (!query || this.isThinking) {
      return;
    }
    this.inputValue = '';
    this.doSend(query);
  }

  public confirmWrite(): void {
    this.doSend('yes');
  }

  public cancelWrite(): void {
    this.doSend('no');
  }

  private doSend(query: string): void {
    this.messages.push({ role: 'user', content: query });
    this.isThinking = true;
    this.successBanner = '';
    this.changeDetectorRef.markForCheck();
    this.scrollToBottom();

    const body: {
      query: string;
      history: { role: string; content: string }[];
      pending_write?: Record<string, unknown>;
    } = {
      query,
      history: this.messages
        .filter((m) => m.role === 'user')
        .map((m) => ({ role: 'user', content: m.content }))
    };

    if (this.pendingWrite) {
      body.pending_write = this.pendingWrite;
    }

    this.http.post<AgentResponse>(this.AGENT_URL, body).subscribe({
      next: (data) => {
        const isWriteSuccess =
          data.tools_used.includes('write_transaction') &&
          data.response.includes('✅');

        const assistantMsg: ChatMessage = {
          role: 'assistant',
          content: data.response,
          toolsUsed: data.tools_used,
          confidence: data.confidence_score,
          latency: data.latency_seconds,
          feedbackGiven: null,
          isWrite: isWriteSuccess
        };

        this.messages.push(assistantMsg);
        this.awaitingConfirmation = data.awaiting_confirmation;
        this.pendingWrite = data.pending_write;

        if (isWriteSuccess) {
          this.successBanner = '✅ Transaction recorded successfully';
          setTimeout(() => {
            this.successBanner = '';
            this.changeDetectorRef.markForCheck();
          }, 4000);
        }

        this.isThinking = false;
        this.changeDetectorRef.markForCheck();
        this.scrollToBottom();
      },
      error: (err) => {
        this.messages.push({
          role: 'assistant',
          content: `⚠️ Connection error: ${err.message || 'Could not reach the AI agent'}. Make sure the agent is running on port 8000.`
        });
        this.isThinking = false;
        this.awaitingConfirmation = false;
        this.pendingWrite = null;
        this.changeDetectorRef.markForCheck();
        this.scrollToBottom();
      }
    });
  }

  public giveFeedback(
    msgIndex: number,
    rating: 1 | -1
  ): void {
    const msg = this.messages[msgIndex];
    if (!msg || msg.feedbackGiven !== null) {
      return;
    }
    msg.feedbackGiven = rating;

    const userQuery =
      msgIndex > 0 ? this.messages[msgIndex - 1].content : '';

    this.http
      .post(this.FEEDBACK_URL, {
        query: userQuery,
        response: msg.content,
        rating
      })
      .subscribe();

    this.changeDetectorRef.markForCheck();
  }

  public confidenceLabel(score: number): string {
    if (score >= 0.8) {
      return 'High';
    }
    if (score >= 0.6) {
      return 'Medium';
    }
    return 'Low';
  }

  public confidenceClass(score: number): string {
    if (score >= 0.8) {
      return 'confidence-high';
    }
    if (score >= 0.6) {
      return 'confidence-medium';
    }
    return 'confidence-low';
  }

  private scrollToBottom(): void {
    setTimeout(() => {
      if (this.messagesContainer?.nativeElement) {
        const el = this.messagesContainer.nativeElement;
        el.scrollTop = el.scrollHeight;
      }
    }, 30);
  }
}
