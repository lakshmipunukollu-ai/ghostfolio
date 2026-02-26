import { AiChatService } from '@ghostfolio/client/services/ai-chat.service';
import { TokenStorageService } from '@ghostfolio/client/services/token-storage.service';
import { GfEnvironment } from '@ghostfolio/ui/environment';
import { GF_ENVIRONMENT } from '@ghostfolio/ui/environment';

import { CommonModule } from '@angular/common';
import { HttpClient, HttpClientModule } from '@angular/common/http';
import {
  ChangeDetectionStrategy,
  ChangeDetectorRef,
  Component,
  ElementRef,
  Inject,
  OnDestroy,
  OnInit,
  ViewChild
} from '@angular/core';
import { FormsModule } from '@angular/forms';
import { Subscription } from 'rxjs';

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

const HISTORY_KEY = 'portfolioAssistantHistory';

@Component({
  changeDetection: ChangeDetectionStrategy.OnPush,
  imports: [CommonModule, FormsModule, HttpClientModule, AiMarkdownPipe],
  selector: 'gf-ai-chat',
  styleUrls: ['./ai-chat.component.scss'],
  templateUrl: './ai-chat.component.html'
})
export class GfAiChatComponent implements OnInit, OnDestroy {
  @ViewChild('messagesContainer') private messagesContainer: ElementRef;

  public isOpen = false;
  public isThinking = false;
  public inputValue = '';
  public messages: ChatMessage[] = [];
  public successBanner = '';
  public showSeedBanner = false;
  public isSeeding = false;
  public enableRealEstate: boolean;

  // Write confirmation state
  private pendingWrite: Record<string, unknown> | null = null;
  public awaitingConfirmation = false;

  private readonly AGENT_URL: string;
  private readonly FEEDBACK_URL: string;
  private readonly SEED_URL: string;
  private aiChatSubscription: Subscription;

  public constructor(
    private changeDetectorRef: ChangeDetectorRef,
    private http: HttpClient,
    private tokenStorageService: TokenStorageService,
    private aiChatService: AiChatService,
    @Inject(GF_ENVIRONMENT) environment: GfEnvironment
  ) {
    const base = (environment.agentUrl ?? '/agent').replace(/\/$/, '');
    this.AGENT_URL = `${base}/chat`;
    this.FEEDBACK_URL = `${base}/feedback`;
    this.SEED_URL = `${base}/seed`;
    this.enableRealEstate = environment.enableRealEstate ?? false;
  }

  public ngOnInit(): void {
    const saved = sessionStorage.getItem(HISTORY_KEY);
    if (saved) {
      try {
        this.messages = JSON.parse(saved);
      } catch {
        this.messages = [];
      }
    }

    // Listen for external open-with-query events (e.g. from Real Estate nav item)
    this.aiChatSubscription = this.aiChatService.openWithQuery.subscribe(
      (query) => {
        if (!this.isOpen) {
          this.openPanel();
        }
        // Small delay so the panel transition completes before firing the query
        setTimeout(() => {
          this.doSend(query);
          this.changeDetectorRef.markForCheck();
        }, 150);
      }
    );
  }

  public ngOnDestroy(): void {
    this.aiChatSubscription?.unsubscribe();
  }

  // ---------------------------------------------------------------------------
  // Welcome message (changes with real-estate flag)
  // ---------------------------------------------------------------------------

  public get welcomeMessage(): string {
    if (this.enableRealEstate) {
      return (
        "Hello! I'm your Portfolio Assistant, powered by Claude. " +
        'Ask me about your portfolio performance, transactions, or tax estimates — ' +
        'or explore housing markets and compare neighborhoods. ' +
        'Use the chips below to get started.'
      );
    }
    return (
      "Hello! I'm your Portfolio Assistant. " +
      'Ask me about your portfolio performance, transactions, tax estimates, ' +
      'or use commands like "buy 5 shares of AAPL" to record transactions.'
    );
  }

  // ---------------------------------------------------------------------------
  // History management
  // ---------------------------------------------------------------------------

  private saveHistory(): void {
    sessionStorage.setItem(HISTORY_KEY, JSON.stringify(this.messages));
  }

  public clearHistory(): void {
    this.messages = [{ role: 'assistant', content: this.welcomeMessage }];
    sessionStorage.removeItem(HISTORY_KEY);
    this.awaitingConfirmation = false;
    this.pendingWrite = null;
    this.successBanner = '';
    this.showSeedBanner = false;
    this.changeDetectorRef.markForCheck();
  }

  // ---------------------------------------------------------------------------
  // Suggestion chips
  // ---------------------------------------------------------------------------

  public get showSuggestions(): boolean {
    return this.messages.length <= 1;
  }

  public clickChip(text: string): void {
    this.inputValue = text;
    this.sendMessage();
  }

  // ---------------------------------------------------------------------------
  // Panel open / close
  // ---------------------------------------------------------------------------

  private openPanel(): void {
    this.isOpen = true;
    if (this.messages.length === 0) {
      this.messages.push({ role: 'assistant', content: this.welcomeMessage });
    }
    this.changeDetectorRef.markForCheck();
    setTimeout(() => this.scrollToBottom(), 50);
  }

  public togglePanel(): void {
    this.isOpen = !this.isOpen;
    if (this.isOpen && this.messages.length === 0) {
      this.messages.push({ role: 'assistant', content: this.welcomeMessage });
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

  // ---------------------------------------------------------------------------
  // Messaging
  // ---------------------------------------------------------------------------

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
      bearer_token?: string;
    } = {
      query,
      history: this.messages
        .filter((m) => m.role === 'user')
        .map((m) => ({ role: 'user', content: m.content }))
    };

    if (this.pendingWrite) {
      body.pending_write = this.pendingWrite;
    }

    const userToken = this.tokenStorageService.getToken();
    if (userToken) {
      body.bearer_token = userToken;
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

        const emptyPortfolioHints = [
          '0 holdings',
          '0 positions',
          'no holdings',
          'no positions',
          'empty portfolio',
          'no transactions',
          '0.00 (0.0%)'
        ];
        const isEmptyPortfolio = emptyPortfolioHints.some((hint) =>
          data.response.toLowerCase().includes(hint)
        );
        if (isEmptyPortfolio && !this.showSeedBanner) {
          this.showSeedBanner = true;
        }

        if (isWriteSuccess) {
          this.successBanner = '✅ Transaction recorded successfully';
          setTimeout(() => {
            this.successBanner = '';
            this.changeDetectorRef.markForCheck();
          }, 4000);
        }

        this.isThinking = false;
        this.saveHistory();
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
        this.saveHistory();
        this.changeDetectorRef.markForCheck();
        this.scrollToBottom();
      }
    });
  }

  // ---------------------------------------------------------------------------
  // Seed portfolio
  // ---------------------------------------------------------------------------

  public seedPortfolio(): void {
    this.isSeeding = true;
    this.showSeedBanner = false;
    this.changeDetectorRef.markForCheck();

    const body: { bearer_token?: string } = {};
    const userToken = this.tokenStorageService.getToken();
    if (userToken) {
      body.bearer_token = userToken;
    }

    this.http
      .post<{ success: boolean; message: string }>(this.SEED_URL, body)
      .subscribe({
        next: (data) => {
          this.isSeeding = false;
          if (data.success) {
            this.messages.push({
              role: 'assistant',
              content: `🌱 **Demo portfolio loaded!** I've added 18 transactions across AAPL, MSFT, NVDA, GOOGL, AMZN, and VTI spanning 2021–2024. Try asking "how is my portfolio doing?" to see your analysis.`
            });
          } else {
            this.messages.push({
              role: 'assistant',
              content: '⚠️ Could not load demo data. Please try again.'
            });
          }
          this.saveHistory();
          this.changeDetectorRef.markForCheck();
          this.scrollToBottom();
        },
        error: () => {
          this.isSeeding = false;
          this.messages.push({
            role: 'assistant',
            content:
              '⚠️ Could not reach the seeding endpoint. Make sure the agent is running.'
          });
          this.saveHistory();
          this.changeDetectorRef.markForCheck();
        }
      });
  }

  // ---------------------------------------------------------------------------
  // Feedback
  // ---------------------------------------------------------------------------

  public giveFeedback(msgIndex: number, rating: 1 | -1): void {
    const msg = this.messages[msgIndex];
    if (!msg || msg.feedbackGiven !== null) {
      return;
    }
    msg.feedbackGiven = rating;

    const userQuery = msgIndex > 0 ? this.messages[msgIndex - 1].content : '';

    this.http
      .post(this.FEEDBACK_URL, {
        query: userQuery,
        response: msg.content,
        rating
      })
      .subscribe();

    this.changeDetectorRef.markForCheck();
  }

  // ---------------------------------------------------------------------------
  // Confidence helpers
  // ---------------------------------------------------------------------------

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

  // ---------------------------------------------------------------------------
  // Scroll
  // ---------------------------------------------------------------------------

  private scrollToBottom(): void {
    setTimeout(() => {
      if (this.messagesContainer?.nativeElement) {
        const el = this.messagesContainer.nativeElement;
        el.scrollTop = el.scrollHeight;
      }
    }, 30);
  }
}
