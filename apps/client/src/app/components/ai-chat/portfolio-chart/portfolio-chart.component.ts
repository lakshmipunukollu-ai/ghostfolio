import {
  AfterViewInit,
  Component,
  ElementRef,
  Input,
  OnChanges,
  OnDestroy,
  ViewChild
} from '@angular/core';
import {
  Chart,
  ArcElement,
  DoughnutController,
  Legend,
  Tooltip
} from 'chart.js';

Chart.register(ArcElement, DoughnutController, Legend, Tooltip);

export interface ChartData {
  type: 'allocation_pie';
  labels: string[];
  values: number[];
}

const PALETTE = [
  '#6366f1',
  '#10b981',
  '#f59e0b',
  '#3b82f6',
  '#ef4444',
  '#8b5cf6',
  '#06b6d4',
  '#84cc16',
  '#f97316',
  '#ec4899'
];

@Component({
  imports: [],
  selector: 'gf-portfolio-chart',
  styleUrls: ['./portfolio-chart.component.scss'],
  templateUrl: './portfolio-chart.component.html'
})
export class GfPortfolioChartComponent
  implements AfterViewInit, OnChanges, OnDestroy
{
  @Input() public chartData!: ChartData;
  @ViewChild('canvas') private canvasRef!: ElementRef<HTMLCanvasElement>;

  private chart: Chart | null = null;

  public ngAfterViewInit(): void {
    this.buildChart();
  }

  public ngOnChanges(): void {
    if (this.chart) {
      this.chart.destroy();
      this.chart = null;
    }
    if (this.canvasRef) {
      this.buildChart();
    }
  }

  public ngOnDestroy(): void {
    this.chart?.destroy();
  }

  private buildChart(): void {
    if (!this.canvasRef || !this.chartData) {
      return;
    }
    const ctx = this.canvasRef.nativeElement.getContext('2d');
    if (!ctx) {
      return;
    }

    const colors = this.chartData.labels.map(
      (_, i) => PALETTE[i % PALETTE.length]
    );

    this.chart = new Chart(ctx, {
      type: 'doughnut',
      data: {
        labels: this.chartData.labels,
        datasets: [
          {
            data: this.chartData.values,
            backgroundColor: colors,
            borderColor: 'transparent',
            hoverOffset: 6
          }
        ]
      },
      options: {
        responsive: false,
        cutout: '62%',
        plugins: {
          legend: {
            position: 'right',
            labels: {
              color: '#9ca3af',
              font: { size: 11 },
              boxWidth: 10,
              padding: 8,
              generateLabels: (chart) => {
                const data = chart.data;
                return (data.labels as string[]).map((label, i) => ({
                  text: `${label}  ${(data.datasets[0].data[i] as number).toFixed(1)}%`,
                  fillStyle: (data.datasets[0].backgroundColor as string[])[i],
                  hidden: false,
                  index: i
                }));
              }
            }
          },
          tooltip: {
            callbacks: {
              label: (ctx) =>
                ` ${ctx.label}: ${(ctx.raw as number).toFixed(1)}%`
            }
          }
        }
      }
    });
  }
}
