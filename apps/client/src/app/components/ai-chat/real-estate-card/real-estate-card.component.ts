import { CommonModule } from '@angular/common';
import { Component, Input } from '@angular/core';

export interface CityData {
  name: string;
  median_price: number;
  price_per_sqft: number;
  days_on_market: number;
  walk_score: number;
  yoy_change: number;
  inventory: string;
}

export interface ComparisonCard {
  city_a: CityData;
  city_b: CityData;
  winners: {
    median_price: string | null;
    price_per_sqft: string | null;
    days_on_market: string | null;
    walk_score: string | null;
  };
  verdict: string;
}

@Component({
  imports: [CommonModule],
  selector: 'gf-real-estate-card',
  styleUrls: ['./real-estate-card.component.scss'],
  templateUrl: './real-estate-card.component.html'
})
export class GfRealEstateCardComponent {
  @Input() public card!: ComparisonCard;

  public copyLabel = 'Copy';
  private copyTimer: ReturnType<typeof setTimeout> | null = null;

  public isWinner(
    cityName: string,
    metric: keyof ComparisonCard['winners']
  ): boolean {
    return this.card.winners[metric] === cityName;
  }

  public formatPrice(value: number): string {
    return `$${(value / 1000).toFixed(0)}k`;
  }

  public formatYoy(value: number): string {
    const sign = value >= 0 ? '+' : '';
    return `${sign}${value.toFixed(1)}%`;
  }

  public yoyClass(value: number): string {
    return value >= 0 ? 'positive' : 'negative';
  }

  public copyToClipboard(): void {
    const a = this.card.city_a;
    const b = this.card.city_b;
    const w = this.card.winners;

    const winLabel = (_metric: string, winner: string | null) =>
      winner ? `  ✓ ${winner.split(',')[0]} wins` : '';

    const text = [
      `${a.name} vs ${b.name} — Housing Comparison`,
      '─'.repeat(46),
      `Median Price:    ${this.formatPrice(a.median_price).padEnd(10)} vs  ${this.formatPrice(b.median_price)}${winLabel('median_price', w.median_price)}`,
      `Price/sqft:      $${String(a.price_per_sqft).padEnd(9)} vs  $${b.price_per_sqft}${winLabel('price_per_sqft', w.price_per_sqft)}`,
      `Days on Market:  ${String(a.days_on_market).padEnd(10)} vs  ${b.days_on_market}${winLabel('days_on_market', w.days_on_market)}`,
      `Walk Score:      ${String(a.walk_score).padEnd(10)} vs  ${b.walk_score}${winLabel('walk_score', w.walk_score)}`,
      `YoY Price:       ${this.formatYoy(a.yoy_change).padEnd(10)} vs  ${this.formatYoy(b.yoy_change)}`,
      '─'.repeat(46),
      `Verdict: ${this.card.verdict}`
    ].join('\n');

    navigator.clipboard.writeText(text).then(() => {
      this.copyLabel = 'Copied ✓';
      if (this.copyTimer !== null) {
        clearTimeout(this.copyTimer);
      }
      this.copyTimer = setTimeout(() => {
        this.copyLabel = 'Copy';
      }, 2000);
    });
  }
}
